"""Point d'entrée WSGI Render, protégé par authentification HTTP."""
import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
import server

def create_app():
    app=Flask(__name__,static_folder=None)
    app.config['MAX_CONTENT_LENGTH']=30000
    production=os.environ.get('APP_ENV')=='production' or bool(os.environ.get('RENDER'))
    password=os.environ.get('APP_PASSWORD','')
    username=os.environ.get('APP_USERNAME','louis')
    if production and (not os.environ.get('DATABASE_URL') or len(password)<16):
        raise RuntimeError('Configurer DATABASE_URL et APP_PASSWORD (16 caractères minimum) avant le démarrage.')
    if os.environ.get('RENDER'):
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
    failures=defaultdict(list)
    failure_lock=threading.Lock()

    def unauthorized():
        return 'Connexion requise pour accéder à votre veille.',401,{'WWW-Authenticate':'Basic realm="Signal", charset="UTF-8"'}

    @app.before_request
    def protect():
        if request.path=='/healthz': return None
        if password:
            now=time.monotonic(); ip=request.remote_addr
            with failure_lock:
                failures[ip]=[t for t in failures[ip] if now-t<60]
                if len(failures[ip])>=10:
                    return jsonify(error='Trop de tentatives. Réessayez dans une minute.'),429
            auth=request.authorization
            matches=auth and auth.type=='basic' and hmac.compare_digest(
                hashlib.sha256((auth.username or '').encode()).digest(),hashlib.sha256(username.encode()).digest()) and hmac.compare_digest(
                hashlib.sha256((auth.password or '').encode()).digest(),hashlib.sha256(password.encode()).digest())
            if not matches:
                with failure_lock: failures[ip].append(now)
                return unauthorized()
            with failure_lock: failures.pop(ip,None)
        if request.method=='POST':
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
    def state(): return jsonify(server.state())

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
