"""Point d'entrée WSGI Render : page de connexion et compte gérés par l'application."""
import hashlib
import hmac
import os
import threading
import time
from datetime import timedelta

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from werkzeug.middleware.proxy_fix import ProxyFix
import auth
import ratelimit
import server

# Seuils de limitation, partagés entre tous les processus via la base (voir ratelimit.py).
LOGIN_LIMIT, LOGIN_WINDOW = 8, 60       # 8 échecs de connexion par minute et par adresse IP
SIGNUP_LIMIT, SIGNUP_WINDOW = 8, 3600   # 8 tentatives d'inscription par heure et par adresse IP

PUBLIC_PATHS = {'/healthz', '/login', '/setup', '/signup'}

def create_app():
    server.AUTO_TRANSLATE=not os.environ.get('DISABLE_AUTO_TRANSLATE')
    app=Flask(__name__,static_folder=None)
    app.config['MAX_CONTENT_LENGTH']=30000
    production=os.environ.get('APP_ENV')=='production' or bool(os.environ.get('RENDER'))
    if production and not os.environ.get('DATABASE_URL'):
        raise RuntimeError('Configurer DATABASE_URL avant le démarrage.')
    # Clé de signature des sessions, dans l'ordre de préférence :
    # 1. SECRET_KEY si fournie (contrôlée par l'exploitant) ;
    # 2. sinon une clé aléatoire persistée en base, indépendante de DATABASE_URL ;
    # 3. en dernier recours (base indisponible au démarrage), dérivée de DATABASE_URL.
    secret=os.environ.get('SECRET_KEY')
    if not secret:
        try: secret=auth.session_secret(server.conn)
        except Exception: secret=None
    if not secret:
        secret=hashlib.sha256(('signal-session|'+os.environ.get('DATABASE_URL','')+'|'+str(server.DB)).encode()).hexdigest()
    app.config.update(SECRET_KEY=secret,SESSION_COOKIE_NAME='signal_session',SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=production,
                      PERMANENT_SESSION_LIFETIME=timedelta(days=30))
    # Nettoyage unique des comptes de test créés pendant l'audit de sécurité (à retirer ensuite).
    try: auth.purge_test_accounts(server.conn,('sonde','audit-securite','test-'))
    except Exception: pass
    if os.environ.get('RENDER'):
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
        # Préchauffe le cache de pertinence au réveil du service pour que le premier affichage soit rapide.
        def warm():
            try: server.state()
            except Exception: pass
        threading.Thread(target=warm,daemon=True).start()
    cache={'record':None,'loaded':None}
    cache_lock=threading.Lock()

    def account(force=False):
        """Compte stocké en base, relu au plus toutes les 30 secondes."""
        with cache_lock:
            if force or cache['loaded'] is None or time.monotonic()-cache['loaded']>30:
                cache['record']=auth.load(server.conn); cache['loaded']=time.monotonic()
            return cache['record']

    users={}  # identifiant en minuscules -> (compte, date de lecture)

    def current(force=False):
        """Compte de la session en cours (administrateur ou membre), relu au plus toutes les 30 secondes."""
        name=session.get('user')
        if not name: return None
        with cache_lock:
            hit=users.get(name.lower())
            if not force and hit and time.monotonic()-hit[1]<30: return hit[0]
        record=auth.find(server.conn,name)
        with cache_lock: users[name.lower()]=(record,time.monotonic())
        return record

    def is_admin(record): return bool(record) and record.get('role','admin')!='member'

    def remember(record):
        with cache_lock:
            if is_admin(record): cache['record']=record; cache['loaded']=time.monotonic()
            users[record['username'].lower()]=(record,time.monotonic())

    def forget(username):
        with cache_lock: users.pop(username.lower(),None)

    def too_many_signups(ip):
        return ratelimit.blocked(server.conn,'signup',ip,SIGNUP_LIMIT,SIGNUP_WINDOW)

    def fingerprint(record):
        # Changer le mot de passe change l'empreinte et invalide les autres sessions.
        return hmac.new(secret.encode(),(record['username']+'|'+record['hash']).encode(),hashlib.sha256).hexdigest()[:32]

    def open_session(record,persistent):
        session.clear()
        session.permanent=persistent
        session['auth']=fingerprint(record); session['user']=record['username']; session['was_logged_in']=True

    def blocked(ip):
        return ratelimit.blocked(server.conn,'login',ip,LOGIN_LIMIT,LOGIN_WINDOW)

    def record_failure(ip):
        ratelimit.record(server.conn,'login',ip,LOGIN_WINDOW)
        time.sleep(0.4)  # ralentit les essais automatisés

    def logged_in(record):
        return bool(record) and hmac.compare_digest(str(session.get('auth','')),fingerprint(record))

    def same_origin():
        return request.headers.get('Origin') in (None,request.host_url.rstrip('/'))

    @app.before_request
    def protect():
        if request.path in PUBLIC_PATHS: return None
        if not account():
            if request.path.startswith('/api/'): return jsonify(error='Créez votre accès pour commencer.',setup=True),401
            return redirect('/setup')
        if not logged_in(current()):
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
        if account(force=True): return redirect('/' if logged_in(current()) else '/login')
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
        if not account(force=True): return redirect('/setup')
        if logged_in(current()): return redirect('/')
        return login_html()

    @app.post('/login')
    def login():
        ip=request.remote_addr
        if not same_origin(): return redirect('/login?m=origine',303)
        owner=account(force=True)
        if not owner: return redirect('/setup',303)
        if blocked(ip): return redirect('/login?m=bloque',303)
        username=request.form.get('username','')
        record=auth.find(server.conn,username)
        if not record: auth.verify(owner,'',request.form.get('password',''))  # même durée qu'un vrai essai
        if not record or not auth.verify(record,username,request.form.get('password','')):
            record_failure(ip)
            return redirect('/login?m=identifiants',303)
        remember(record)
        ratelimit.clear(server.conn,'login',ip)
        open_session(record,request.form.get('remember')=='1')
        return redirect('/',303)

    @app.get('/signup')
    def signup_page():
        if not account(force=True): return redirect('/setup')
        if logged_in(current()): return redirect('/')
        if not auth.signup_open(server.conn): return redirect('/login?m=ferme')
        return login_html()

    @app.post('/signup')
    def signup():
        ip=request.remote_addr
        if not same_origin(): return redirect('/signup?m=origine',303)
        if not account(force=True): return redirect('/setup',303)
        if not auth.signup_open(server.conn): return redirect('/login?m=ferme',303)
        if too_many_signups(ip): return redirect('/signup?m=bloque',303)
        # Chaque tentative compte (pas seulement les réussites) : empêche de sonder en masse
        # quels identifiants existent déjà.
        ratelimit.record(server.conn,'signup',ip,SIGNUP_WINDOW)
        username=request.form.get('username','').strip()
        password=request.form.get('password','')
        problem=auth.validate(username,password,request.form.get('confirm',''))
        if problem: return redirect('/signup?m='+problem,303)
        record=auth.register(server.conn,username,password)
        if not record: return redirect('/signup?m=pris',303)
        remember(record); open_session(record,True)
        return redirect('/',303)

    @app.get('/api/accounts')
    def accounts():
        if not is_admin(current()): return jsonify(error='Réservé à l’administrateur.'),403
        return jsonify(members=auth.members(server.conn),signup_open=auth.signup_open(server.conn))

    @app.post('/api/accounts')
    def manage_accounts():
        if not is_admin(current(force=True)): return jsonify(error='Réservé à l’administrateur.'),403
        body=request.get_json()
        if not isinstance(body,dict): return jsonify(error='Données invalides.'),400
        if body.get('action')=='signup':
            auth.set_signup(server.conn,bool(body.get('open')))
        elif body.get('action')=='delete':
            username=str(body.get('username',''))
            if not auth.delete_member(server.conn,username): return jsonify(error='Compte introuvable.'),404
            forget(username)
        else: return jsonify(error='Action inconnue.'),400
        return jsonify(members=auth.members(server.conn),signup_open=auth.signup_open(server.conn))

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
        record=current(force=True)
        if not auth.verify(record,record['username'],str(body.get('current',''))):
            record_failure(ip)
            return jsonify(error='Mot de passe actuel incorrect.'),403
        username=str(body.get('username') or record['username']).strip()
        problem=auth.validate(username,str(body.get('new','')),str(body.get('confirm','')))
        if problem:
            messages={'identifiant':'Identifiant invalide : 1 à 60 caractères, sans espace.','faible':'Le nouveau mot de passe doit contenir au moins '+str(auth.MIN_LENGTH)+' caractères.','evident':'Mot de passe trop simple ou trop courant. Évitez les suites et les répétitions.','different':'La confirmation ne correspond pas au nouveau mot de passe.'}
            return jsonify(error=messages[problem]),400
        taken=jsonify(error='Cet identifiant est déjà utilisé par un autre compte.'),409
        if is_admin(record):
            other=auth.find(server.conn,username)
            if other and not is_admin(other): return taken
            updated=auth.change(server.conn,username,str(body['new']))
        else:
            updated=auth.change_member(server.conn,record['username'],username,str(body['new']))
            if not updated: return taken
        forget(record['username']); remember(updated); open_session(updated,session.permanent)
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
        record=current()
        payload=server.state(None if is_admin(record) else record['username'])
        if server.sync_if_stale(payload.get('last_sync')): payload['syncing']=True
        payload['user']=session.get('user','')
        payload['auth']=True
        payload['admin']=is_admin(record)
        return jsonify(payload)

    @app.post('/api/<action>')
    def action(action):
        body=request.get_json()
        if not isinstance(body,dict): return jsonify(error='Données invalides.'),400
        record=current()
        status,payload=server.perform_action('/api/'+action,body,None if is_admin(record) else record['username'])
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
        import traceback
        frame=traceback.extract_tb(error.__traceback__)[-1] if error.__traceback__ else None
        where='%s:%s %s'%(os.path.basename(frame.filename),frame.lineno,frame.name) if frame else '?'
        message=str(error)[:160] if isinstance(error,(AttributeError,NameError,IndexError)) else ''
        app.logger.error('Requête interrompue : %s à %s %s',type(error).__name__,where,message)
        return jsonify(error='Service momentanément indisponible. Réessayez dans un instant.'),503
    return app

app=create_app()
