"""Compte d'accès géré par l'application.

Le mot de passe n'est jamais stocké : seule une empreinte PBKDF2-SHA256 salée est
enregistrée dans la table settings (clé « access »), dans la base de l'application.
"""
import hashlib
import hmac
import json
import secrets
import time

KEY='access'
ITERATIONS=310_000
MIN_LENGTH=10

def _hash(password,salt,iterations):
    return hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),bytes.fromhex(salt),iterations).hex()

def _record(username,password):
    salt=secrets.token_hex(16)
    return {'username':username,'salt':salt,'iterations':ITERATIONS,'hash':_hash(password,salt,ITERATIONS),'updated':time.time()}

def validate(username,password,confirm):
    """Retourne un code d'erreur, ou None si les valeurs sont acceptables."""
    if not username or len(username)>60 or any(ch.isspace() for ch in username): return 'identifiant'
    if len(password)<MIN_LENGTH or len(password)>256: return 'faible'
    if password!=confirm: return 'different'
    return None

def load(conn):
    with conn() as c:
        row=c.execute('SELECT value FROM settings WHERE key=?',(KEY,)).fetchone()
    return json.loads(row['value']) if row else None

def create(conn,username,password):
    """Créer le compte unique. Retourne None si un compte existe déjà."""
    record=_record(username,password)
    with conn() as c:
        cursor=c.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT DO NOTHING',(KEY,json.dumps(record)))
        if cursor.rowcount!=1: return None
    return record

def change(conn,username,password):
    record=_record(username,password)
    with conn() as c:
        c.execute('UPDATE settings SET value=? WHERE key=?',(json.dumps(record),KEY))
    return record

def reset(conn):
    with conn() as c: c.execute('DELETE FROM settings WHERE key=?',(KEY,))

def verify(record,username,password):
    if not record: return False
    expected=bytes.fromhex(record['hash'])
    actual=bytes.fromhex(_hash(password or '',record['salt'],int(record.get('iterations',ITERATIONS))))
    same_user=hmac.compare_digest((username or '').strip().lower().encode(),record['username'].lower().encode())
    return hmac.compare_digest(actual,expected) and same_user
