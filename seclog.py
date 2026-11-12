"""Journal de sécurité : détection silencieuse des outils d'IA et d'automatisation.

On repère les visiteurs connectés dont la signature technique (User-Agent) correspond à
un outil d'IA ou à un navigateur automatisé qui s'annonce (Claude, ChatGPT, Perplexity,
navigateurs « sans affichage », scripts…). La visite est journalisée pour l'administrateur,
sans jamais rien bloquer ni rien montrer à la personne.

Limites assumées : ne détecte que les outils qui s'identifient. Une signature maquillée,
ou une simple capture d'écran depuis un navigateur ordinaire, reste indétectable.

Rangé dans la table settings (clés « seclog:<horodatage> »), aucune table à créer.
"""
import json
import time

# (libellé affiché, fragment recherché dans le User-Agent en minuscules)
MARKERS = [
    ('Claude', 'claude'),
    ('ChatGPT', 'chatgpt'),
    ('GPTBot (OpenAI)', 'gptbot'),
    ('OpenAI', 'openai'),
    ('Perplexity', 'perplexity'),
    ('Anthropic', 'anthropic'),
    ('Google (entraînement IA)', 'google-extended'),
    ('CCBot (entraînement IA)', 'ccbot'),
    ('Bytespider', 'bytespider'),
    ('Diffbot', 'diffbot'),
    ('Navigateur automatisé', 'headlesschrome'),
    ('Puppeteer', 'puppeteer'),
    ('Playwright', 'playwright'),
    ('Selenium', 'selenium'),
    ('Scrapy', 'scrapy'),
    ('Script python-requests', 'python-requests'),
    ('curl', 'curl'),
    ('wget', 'wget'),
]

PREFIX = 'seclog:'
MAX_KEEP = 200

def detect(user_agent):
    """Renvoie le libellé de l'outil détecté, ou None."""
    ua = (user_agent or '').lower()
    for label, needle in MARKERS:
        if needle in ua:
            return label
    return None

def _all(conn):
    with conn() as c:
        return [(r['key'], r['value'])
                for r in c.execute("SELECT key,value FROM settings WHERE key LIKE ?", (PREFIX + '%',)).fetchall()]

def record(conn, event):
    """Journalise un évènement {t, user, tool, ip, ua, path} et garde les plus récents."""
    key = PREFIX + format(time.time_ns(), '020d')
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO NOTHING",
                  (key, json.dumps(event, ensure_ascii=False)))
    rows = _all(conn)
    if len(rows) > MAX_KEEP:
        def moment(value):
            try: return json.loads(value).get('t', 0)
            except Exception: return 0
        for k, _ in sorted(rows, key=lambda kv: moment(kv[1]))[:len(rows) - MAX_KEEP]:
            with conn() as c:
                c.execute("DELETE FROM settings WHERE key=?", (k,))

def recent(conn, limit=100):
    events = []
    for _, value in _all(conn):
        try: events.append(json.loads(value))
        except Exception: pass
    events.sort(key=lambda e: e.get('t', 0), reverse=True)
    return events[:limit]
