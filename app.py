"""Point d'entrée WSGI Render : page de connexion et compte gérés par l'application."""
import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict
from datetime import timedelta

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from werkzeug.middleware.proxy_fix import ProxyFix
import auth
import server

PUBLIC_PATHS = {'/healthz', '/login', '/setup'}

def create_app():
    server.AUTO_TRANSLATE=not os.environ.get('DISABLE_AUTO_TRANSLATE')
    app=Flask(__name__,static_folder=None)
    app.config['MAX_CONTENT_LENGTH']=30000
    production=os.environ.get('APP_ENV')=='production' or bool(os.environ.get('RENDER'))
    if production and not os.environ.get('DATABASE_URL'):
        raise RuntimeError('Configurer DATABASE_URL avant le démarrage.')
    # Clé de signature des sessions : SECRET_KEY si fournie, sinon dérivée de la chaîne de base de données,
    # secrète et présente uniquement sur le serveur.
    secret=os.environ.get('SECRET_KEY') or hashlib.sha256(('signal-session|'+os.environ.get('DATABASE_URL','')+'|'+str(server.DB)).encode()).hexdigest()
    app.config.update(SECRET_KEY=secret,SESSION_COOKIE_NAME='signal_session',SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=production,
                      PERMANENT_SESSION_LIFETIME=timedelta(days=30))
    if os.environ.get('RENDER'):
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
    failures=defaultdict(list)
    failure_lock=threading.Lock()
    cache={'record':None,'loaded':None}
    cache_lock=threading.Lock()

    def account(force=False):
        """Compte stocké en base, relu au plus toutes les 30 secondes."""
        with cache_lock:
            if force or cache['loaded'] is None or time.monotonic()-cache['loaded']>30:
                cache['record']=auth.load(server.conn); cache['loaded']=time.monotonic()
            return cache['record']

    def remember(record):
        with cache_lock: cache['record']=record; cache['loaded']=time.monotonic()

    def fingerprint(record):
        # Changer le mot de passe change l'empreinte et invalide les autres sessions.
        return hmac.new(secret.encode(),(record['username']+'|'+record['hash']).encode(),hashlib.sha256).hexdigest()[:32]

    def open_session(record,persistent):
        session.clear()
        session.permanent=persistent
        session['auth']=fingerprint(record); session['user']=record['username']; session['was_logged_in']=True

    def blocked(ip):
        now=time.monotonic()
        with failure_lock:
            failures[ip]=[t for t in failures[ip] if now-t<60]
            return len(failures[ip])>=8

    def record_failure(ip):
        with failure_lock: failures[ip].append(time.monotonic())
        time.sleep(0.4)  # ralentit les essais automatisés

    def logged_in(record):
        return bool(record) and hmac.compare_digest(str(session.get('auth','')),fingerprint(record))

    def same_origin():
        return request.headers.get('Origin') in (None,request.host_url.rstrip('/'))

    @app.before_request
    def protect():
        if request.path in PUBLIC_PATHS: return None
        record=account()
        if not record:
            if request.path.startswith('/api/'): return jsonify(error='Créez votre accès pour commencer.',setup=True),401
            return redirect('/setup')
        if not logged_in(record):
            if request.path.startswith('/api/'): return jsonify(error='Session expirée. Reconnectez-vous.',login=True),401
            return redirect('/login?m=expire' if session.get('was_logged_in') else '/login')
        if request.method=='POST':
            if request.headers.get('Origin')!=request.host_url.rstrip('/'):
                return jsonify(error='Origine de la requête non autorisée.'),403
            if request.path!='/logout' and not request.is_json:
                return jsonify(error='Une requête JSON est requise.'),415

    @app.after_request
    def response_headers(response):
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='same-origin'
        if production: response.headers['Strict-Transport-Security']='max-age=31536000'
        return response

    def login_html(): return send_from_directory(server.ROOT/'public','login.html')

    @app.get('/setup')
    def setup_page():
        record=account(force=True)
        if record: return redirect('/' if logged_in(record) else '/login')
        return login_html()

    @app.post('/setup')
    def setup():
        if not same_origin(): return redirect('/setup?m=origine',303)
        if account(force=True): return redirect('/login?m=existe',303)
        username=request.form.get('username','').strip()
        password=request.form.get('password','')
        problem=auth.validate(username,password,request.form.get('confirm',''))
        if problem: return redirect('/setup?m='+problem,303)
        record=auth.create(server.conn,username,password)
        if not record: return redirect('/login?m=existe',303)
        remember(record); open_session(record,True)
        return redirect('/',303)

    @app.get('/login')
    def login_page():
        record=account(force=True)
        if not record: return redirect('/setup')
        if logged_in(record): return redirect('/')
        return login_html()

    @app.post('/login')
    def login():
        ip=request.remote_addr
        if not same_origin(): return redirect('/login?m=origine',303)
        record=account(force=True)
        if not record: return redirect('/setup',303)
        if blocked(ip): return redirect('/login?m=bloque',303)
        if not auth.verify(record,request.form.get('username',''),request.form.get('password','')):
            record_failure(ip)
            return redirect('/login?m=identifiants',303)
        with failure_lock: failures.pop(ip,None)
        open_session(record,request.form.get('remember')=='1')
        return redirect('/',303)

    @app.post('/logout')
    def logout():
        session.clear()
        if request.is_json: return jsonify(ok=True,redirect='/login?m=deconnecte')
        return redirect('/login?m=deconnecte',303)

    @app.post('/api/password')
    def change_password():
        body=request.get_json()
        if not isinstance(body,dict): return jsonify(error='Données invalides.'),400
        ip=request.remote_addr
        if blocked(ip): return jsonify(error='Trop de tentatives. Réessayez dans une minute.'),429
        record=account(force=True)
        if not auth.verify(record,record['username'],str(body.get('current',''))):
            record_failure(ip)
            return jsonify(error='Mot de passe actuel incorrect.'),403
        username=str(body.get('username') or record['username']).strip()
        problem=auth.validate(username,str(body.get('new','')),str(body.get('confirm','')))
        if problem:
            messages={'identifiant':'Identifiant invalide : 1 à 60 caractères, sans espace.','faible':'Le nouveau mot de passe doit contenir au moins '+str(auth.MIN_LENGTH)+' caractères.','different':'La confirmation ne correspond pas au nouveau mot de passe.'}
            return jsonify(error=messages[problem]),400
        updated=auth.change(server.conn,username,str(body['new']))
        remember(updated); open_session(updated,session.permanent)
        return jsonify(ok=True,user=username)

    @app.get('/healthz')
    def health():
        try:
            with server.conn() as c: c.execute('SELECT 1').fetchone()
            return jsonify(status='ok')
        except Exception:
            return jsonify(status='unavailable'),503

    @app.get('/')
    def home(): return send_from_directory(server.ROOT/'public','index.html')

    @app.get('/<name>')
    def asset(name):
        if name not in ('app.js','style.css'): return jsonify(error='Page introuvable.'),404
        return send_from_directory(server.ROOT/'public',name)

    @app.get('/api/state')
    def state():
        payload=server.state()
        if server.sync_if_stale(payload.get('last_sync')): payload['syncing']=True
        payload['user']=session.get('user','')
        payload['auth']=True
        return jsonify(payload)

    @app.post('/api/<action>')
    def action(action):
        body=request.get_json()
        if not isinstance(body,dict): return jsonify(error='Données invalides.'),400
        status,payload=server.perform_action('/api/'+action,body)
        return jsonify(payload),status

    @app.errorhandler(400)
    def invalid_json(error): return jsonify(error='Données JSON invalides.'),400

    @app.errorhandler(413)
    def too_large(error): return jsonify(error='Contenu trop volumineux.'),413

    @app.errorhandler(Exception)
    def error(error):
        from werkzeug.exceptions import HTTPException
        if isinstance(error,HTTPException): return jsonify(error='Requête non autorisée ou page introuvable.'),error.code
        if isinstance(error,(ValueError,KeyError,TypeError)):
            return jsonify(error='Vérifiez les champs de votre demande.'),400
        # Ne pas exposer de mot de passe, de chaîne Neon ou de détails SQL.
        app.logger.error('Requête interrompue : %s',type(error).__name__)
        return jsonify(error='Service momentanément indisponible. Réessayez dans un instant.'),503
    return app

app=create_app()
