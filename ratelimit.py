"""Limitation des tentatives, partagée entre tous les processus via la base.

Le compteur en mémoire ne fonctionnait pas en ligne : Render lance plusieurs
processus web, chacun avec sa propre mémoire, donc aucun n'atteignait le seuil.
On range donc les horodatages d'échec dans la table settings (aucune table à
créer : le rôle Neon de l'application n'a pas le droit de créer des objets).

Clé : « rl:<catégorie>:<identifiant> » (identifiant = adresse IP ou nom de compte).
Valeur : liste JSON d'instants (epoch). Chaque catégorie/identifiant a sa propre
clé, ce qui évite toute contention entre adresses différentes.
"""
import json
import time

MAX_KEEP = 50  # on ne conserve jamais plus d'horodatages que nécessaire

def _key(category, identifier):
    return 'rl:' + category + ':' + (identifier or '?').lower()[:80]

def _recent(conn, key, window):
    now = time.time()
    with conn() as c:
        row = c.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    try:
        times = json.loads(row['value']) if row else []
    except Exception:
        times = []
    return [t for t in times if now - t < window][-MAX_KEEP:]

def blocked(conn, category, identifier, limit, window):
    """Vrai si le seuil est déjà atteint, sans rien enregistrer."""
    return len(_recent(conn, _key(category, identifier), window)) >= limit

def record(conn, category, identifier, window):
    """Enregistre un échec et renvoie le nombre d'échecs récents."""
    key = _key(category, identifier)
    times = _recent(conn, key, window)
    times.append(time.time())
    times = times[-MAX_KEEP:]
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                  (key, json.dumps(times)))
    return len(times)

def clear(conn, category, identifier):
    """Efface le compteur (après une connexion réussie)."""
    with conn() as c:
        c.execute('DELETE FROM settings WHERE key=?', (_key(category, identifier),))
