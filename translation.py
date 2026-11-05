"""Traduction des seuls contenus publics, avec cache persistant."""
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

CHUNK = 1200  # caractères maximum envoyés par requête

def initialize(c):
    c.execute('CREATE TABLE IF NOT EXISTS translations (id TEXT PRIMARY KEY, original TEXT NOT NULL, french TEXT NOT NULL)')

def identity(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def cached(c, text):
    if not text or not text.strip(): return text
    row = c.execute('SELECT french FROM translations WHERE id=?', (identity(text),)).fetchone()
    return row['french'] if row else None

def chunks(text, size=CHUNK):
    """Découpe aux fins de phrases pour ne jamais dépasser la taille acceptée."""
    parts, current = [], ''
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        while len(sentence) > size:
            if current: parts.append(current); current = ''
            parts.append(sentence[:size]); sentence = sentence[size:]
        if current and len(current) + len(sentence) + 1 > size:
            parts.append(current); current = sentence
        else:
            current = (current + ' ' + sentence).strip()
    if current: parts.append(current)
    return parts

class RateLimited(Exception):
    """Tous les points d'accès refusent temporairement (HTTP 429)."""

# Points d'accès sans clé, sans garantie de disponibilité ; le second sert de secours.
ENDPOINTS = [
    ('https://translate.googleapis.com/translate_a/single?' + urllib.parse.urlencode({'client': 'gtx', 'sl': 'auto', 'tl': 'fr', 'dt': 't'}),
     lambda result: ''.join(part[0] for part in result[0] if part and part[0])),
    ('https://clients5.google.com/translate_a/t?' + urllib.parse.urlencode({'client': 'dict-chrome-ex', 'sl': 'auto', 'tl': 'fr'}),
     lambda result: ''.join((item[0] if isinstance(item, list) else item) for item in result)),
]
COOLDOWN = 1800  # pause d'un point d'accès après un refus « trop de requêtes »
BLOCKED_UNTIL = {}

def translate_chunk(text):
    data = urllib.parse.urlencode({'q': text}).encode('utf-8')
    last = None
    for url, parse in ENDPOINTS:
        if BLOCKED_UNTIL.get(url, 0) > time.time(): continue
        for attempt in range(2):
            try:
                request = urllib.request.Request(url, data=data, headers={'User-Agent': 'Signal/1.0'})
                with urllib.request.urlopen(request, timeout=25) as response:
                    translated = parse(json.load(response))
                if not translated.strip(): raise ValueError('Traduction vide')
                return translated
            except urllib.error.HTTPError as error:
                last = error
                if error.code == 429:
                    BLOCKED_UNTIL[url] = time.time() + COOLDOWN  # ne pas insister : passer au secours
                    break
                time.sleep(1.5)
            except Exception as error:
                last = error
                time.sleep(1.5)
    if all(BLOCKED_UNTIL.get(url, 0) > time.time() for url, _ in ENDPOINTS): raise RateLimited()
    raise last or RuntimeError('Traduction indisponible')

def translate_public(text):
    return ' '.join(translate_chunk(part) for part in chunks(text))

def populate(connect, texts):
    texts = list(dict.fromkeys(t for t in texts if t and t.strip()))
    # Une seule lecture des identifiants déjà traduits (au lieu d'une requête par texte).
    with connect() as c:
        known = {row['id'] for row in c.execute('SELECT id FROM translations')}
    pending = [t for t in texts if identity(t) not in known]
    errors = {}
    def worker(text):
        try: return text, translate_public(text)
        except Exception as error:
            reason = type(error).__name__ + ' ' + str(getattr(error, 'code', '') or '')
            errors[reason] = errors.get(reason, 0) + 1
            return text, None
    saved = 0
    def save(batch):
        # Écritures regroupées dans une seule connexion : pas de verrou concurrent sur la base.
        nonlocal saved
        try:
            with connect() as c:
                for text, french in batch:
                    c.execute('INSERT INTO translations VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET original=excluded.original, french=excluded.french',(identity(text),text,french))
            saved += len(batch)
        except Exception:
            pass
    # Enregistrement par lots de 30 : les traductions apparaissent au fil de l'eau.
    for start in range(0, len(pending), 30):
        with ThreadPoolExecutor(max_workers=3) as pool:
            save([(text, french) for text, french in pool.map(worker,pending[start:start+30]) if french])
        if errors.get('RateLimited ', 0):
            print('Traduction en pause 30 min : service saturé (%d/%d enregistrées)' % (saved, len(pending)), flush=True)
            break
        print('Traduction : %d/%d enregistrées, échecs %s' % (saved, len(pending), errors or 'aucun'), flush=True)
    return {'translated':saved,'pending':len(pending)-saved}
