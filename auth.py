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

# ---- Comptes supplémentaires (inscription libre, fermable par l'administrateur) ----
# Le compte « access » est celui de l'administrateur (le premier créé). Les autres sont
# rangés un par un sous la clé « account:<identifiant en minuscules> » : l'unicité est
# garantie par la clé primaire, sans créer de nouvelle table.
PREFIX='account:'
SIGNUP_KEY='signup'

def _member_key(username): return PREFIX+username.strip().lower()

def find(conn,username):
    """Compte correspondant à l'identifiant (administrateur ou membre), sinon None."""
    username=(username or '').strip()
    if not username: return None
    owner=load(conn)
    if owner and owner['username'].lower()==username.lower(): return dict(owner,role='admin')
    with conn() as c:
        row=c.execute('SELECT value FROM settings WHERE key=?',(_member_key(username),)).fetchone()
    return dict(json.loads(row['value']),role='member') if row else None

def register(conn,username,password):
    """Créer un compte membre. Retourne None si l'identifiant est déjà pris."""
    owner=load(conn)
    if not owner or owner['username'].lower()==username.strip().lower(): return None
    record=dict(_record(username.strip(),password),created=time.time())
    with conn() as c:
        cursor=c.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT DO NOTHING',(_member_key(username),json.dumps(record)))
        if cursor.rowcount!=1: return None
    return dict(record,role='member')

def members(conn):
    with conn() as c:
        rows=c.execute('SELECT value FROM settings WHERE key LIKE ?',(PREFIX+'%',)).fetchall()
    accounts=[json.loads(r['value']) for r in rows]
    return sorted(({'username':a['username'],'created':a.get('created') or a.get('updated')} for a in accounts),key=lambda a:a['created'] or 0)

def delete_member(conn,username):
    with conn() as c:
        deleted=c.execute('DELETE FROM settings WHERE key=?',(_member_key(username),)).rowcount==1
        c.execute('DELETE FROM settings WHERE key=?',('space:'+username.strip().lower(),))  # espace personnel du compte
        return deleted

def change_member(conn,old_username,username,password):
    """Changer l'identifiant et/ou le mot de passe d'un membre. None si le nouvel identifiant est pris."""
    owner=load(conn)
    if owner and owner['username'].lower()==username.strip().lower(): return None
    record=dict(_record(username.strip(),password),created=(find(conn,old_username) or {}).get('created'))
    with conn() as c:
        if _member_key(old_username)!=_member_key(username):
            if c.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT DO NOTHING',(_member_key(username),json.dumps(record))).rowcount!=1: return None
            c.execute('DELETE FROM settings WHERE key=?',(_member_key(old_username),))
            c.execute('UPDATE settings SET key=? WHERE key=?',('space:'+username.strip().lower(),'space:'+old_username.strip().lower()))  # l'espace suit le compte
        else:
            c.execute('UPDATE settings SET value=? WHERE key=?',(json.dumps(record),_member_key(username)))
    return dict(record,role='member')

def signup_open(conn):
    with conn() as c:
        row=c.execute('SELECT value FROM settings WHERE key=?',(SIGNUP_KEY,)).fetchone()
    return not row or row['value']!='closed'

def set_signup(conn,is_open):
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(SIGNUP_KEY,'open' if is_open else 'closed'))

def verify(record,username,password):
    if not record: return False
    expected=bytes.fromhex(record['hash'])
    actual=bytes.fromhex(_hash(password or '',record['salt'],int(record.get('iterations',ITERATIONS))))
    same_user=hmac.compare_digest((username or '').strip().lower().encode(),record['username'].lower().encode())
    return hmac.compare_digest(actual,expected) and same_user
