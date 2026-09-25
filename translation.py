"""Traduction des seuls contenus publics, avec cache SQLite persistant."""
import hashlib
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

def initialize(c):
    c.execute('CREATE TABLE IF NOT EXISTS translations (id TEXT PRIMARY KEY, original TEXT NOT NULL, french TEXT NOT NULL)')

def identity(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def cached(c, text):
    if not text or not text.strip(): return text
    row = c.execute('SELECT french FROM translations WHERE id=?', (identity(text),)).fetchone()
    return row['french'] if row else None

def translate_public(text):
    # Ce point d’accès sans clé n’a pas de garantie de disponibilité.
    query = urllib.parse.urlencode({'client':'gtx','sl':'auto','tl':'fr','dt':'t','q':text})
    request = urllib.request.Request('https://translate.googleapis.com/translate_a/single?' + query,
                                     headers={'User-Agent':'Signal/1.0'})
    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.load(response)
    translated = ''.join(part[0] for part in result[0] if part and part[0])
    if not translated.strip(): raise ValueError('Traduction vide')
    return translated

def populate(connect, texts):
    texts = list(dict.fromkeys(t for t in texts if t and t.strip()))
    with connect() as c:
        pending = [t for t in texts if cached(c,t) is None]
    def worker(text):
        try:
            french = translate_public(text)
            with connect() as c:
                c.execute('INSERT INTO translations VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET original=excluded.original, french=excluded.french',(identity(text),text,french))
            return True
        except Exception:
            return False
    with ThreadPoolExecutor(max_workers=3) as pool:
        outcomes = list(pool.map(worker,pending))
    return {'translated':sum(outcomes),'pending':len(outcomes)-sum(outcomes)}
