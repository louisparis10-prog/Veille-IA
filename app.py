"""Point d'entrée WSGI Render, protégé par une page de connexion et une session signée."""
import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict
from datetime import timedelta

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from werkzeug.middleware.proxy_fix import ProxyFix
import server

PUBLIC_PATHS = {'/healthz', '/login'}

def _digest(value):
    return hashlib.sha256((value or '').encode('utf-8')).digest()

def create_app():
    server.AUTO_TRANSLATE=not os.environ.get('DISABLE_AUTO_TRANSLATE')
    app=Flask(__name__,static_folder=None)
    app.config['MAX_CONTENT_LENGTH']=30000
    production=os.environ.get('APP_ENV')=='production' or bool(os.environ.get('RENDER'))
    password=os.environ.get('APP_PASSWORD','')
    username=os.environ.get('APP_USERNAME','louis')
    if production and not os.environ.get('DATABASE_URL'):
        raise RuntimeError('Configurer DATABASE_URL avant le démarrage.')
    if production and 0<len(password)<12:
        raise RuntimeError('APP_PASSWORD doit contenir au moins 12 caractères.')
    # En production, l'absence de mot de passe verrouille l'application ; en local elle reste ouverte.
    locked=production and not password
    auth_required=bool(password) or locked
    # Clé de session : SECRET_KEY si fournie, sinon dérivée de secrets déjà présents sur le serveur.
    secret=os.environ.get('SECRET_KEY') or hashlib.sha256(('signal-session|'+password+'|'+os.environ.get('DATABASE_URL','')+'|'+username).encode()).hexdigest()
    app.config.update(SECRET_KEY=secret,SESSION_COOKIE_NAME='signal_session',SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=production,
                      PERMANENT_SESSION_LIFETIME=timedelta(days=30))
    # Toute modification de l'identifiant ou du mot de passe invalide les sessions existantes.
    fingerprint=hmac.new(secret.encode(),('v1|'+username+'|'+password).encode(),hashlib.sha256).hexdigest()[:32]
    if os.environ.get('RENDER'):
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
    failures=defaultdict(list)
    failure_lock=threading.Lock()

    def credentials_match(user,secret_value):
        return bool(password) and hmac.compare_digest(_digest(user),_digest(username)) & hmac.compare_digest(_digest(secret_value),_digest(password))

    def blocked(ip):
        now=time.monotonic()
        with failure_lock:
            failures[ip]=[t for t in failures[ip] if now-t<60]
            return len(failures[ip])>=8

    def record_failure(ip):
        with failure_lock: failures[ip].append(time.monotonic())

    def authenticated():
        if not auth_required: return True
        if session.get('auth')==fingerprint: return True
        # Accès programmatique (scripts, tests) : en-tête Basic accepté, sans fenêtre du navigateur.
        auth=request.authorization
        if auth and auth.type=='basic' and not blocked(request.remote_addr):
            if credentials_match(auth.username,auth.password): return True
            record_failure(request.remote_addr)
        return False

    def same_origin():
        return request.headers.get('Origin') in (None,request.host_url.rstrip('/'))

    @app.before_request
    def protect():
        if request.path in PUBLIC_PATHS: return None
        if not authenticated():
            if request.path.startswith('/api/'):
                return jsonify(error='Session expirée. Reconnectez-vous.',login=True),401
            return redirect('/login?m=expire' if session.get('was_logged_in') else '/login')
        if request.method=='POST':
            if request.path=='/logout':
                if not same_origin(): return jsonify(error='Origine de la requête non autorisée.'),403
                return None
            if request.headers.get('Origin')!=request.host_url.rstrip('/'):
                return jsonify(error='Origine de la requête non autorisée.'),403
            if not request.is_json:
                return jsonify(error='Une requête JSON est requise.'),415

    @app.after_request
    def response_headers(response):
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='same-origin'
        if production: response.headers['Strict-Transport-Security']='max-age=31536000'
        return response

    @app.get('/login')
    def login_page():
        if auth_required and not locked and session.get('auth')==fingerprint: return redirect('/')
        if not auth_required: return redirect('/')
        if locked and not request.args.get('m'): return redirect('/login?m=config')
        return send_from_directory(server.ROOT/'public','login.html')

    @app.post('/login')
    def login():
        ip=request.remote_addr
        if locked: return redirect('/login?m=config',303)
        if not same_origin(): return redirect('/login?m=origine',303)
        if blocked(ip): return redirect('/login?m=bloque',303)
        if not credentials_match(request.form.get('username','').strip(),request.form.get('password','')):
            record_failure(ip)
            time.sleep(0.4)  # ralentit les essais automatisés
            return redirect('/login?m=identifiants',303)
        with failure_lock: failures.pop(ip,None)
        session.clear()
        session.permanent=request.form.get('remember')=='1'
        session['auth']=fingerprint; session['user']=username; session['was_logged_in']=True
        return redirect('/',303)

    @app.post('/logout')
    def logout():
        session.clear()
        if request.is_json: return jsonify(ok=True,redirect='/login?m=deconnecte')
        return redirect('/login?m=deconnecte',303)

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
        payload['user']=session.get('user') or (username if auth_required else '')
        payload['auth']=auth_required
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
