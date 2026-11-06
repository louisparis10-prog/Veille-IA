"""Limitation des tentatives, partagée entre tous les processus via la base.

Le compteur en mémoire ne fonctionnait pas en ligne : Render lance plusieurs
processus web, chacun avec sa propre mémoire. On enregistre donc chaque tentative
comme une ligne distincte de la table settings (aucune table à créer : le rôle Neon
de l'application n'a pas le droit de créer des objets).

Clé : « rl:<catégorie>:<identifiant>:<horodatage ns> » — unique, donc chaque tentative
est une insertion indépendante : aucune écriture concurrente n'en écrase une autre.
Valeur : l'instant (epoch, en secondes). Le comptage et la purge se font en Python
sur ces valeurs numériques, sans dépendre du classement du texte par la base
(différent entre SQLite et PostgreSQL selon la locale).
"""
import time

def _prefix(category, identifier):
    return 'rl:' + category + ':' + (identifier or '?').lower()[:60] + ':'

def _seconds(value):
    try: return float(value)
    except (TypeError, ValueError): return 0.0

def _rows(conn, prefix):
    with conn() as c:
        return [(r['key'], _seconds(r['value']))
                for r in c.execute("SELECT key,value FROM settings WHERE key LIKE ?", (prefix + '%',)).fetchall()]

def blocked(conn, category, identifier, limit, window):
    """Vrai si le nombre de tentatives dans la fenêtre atteint déjà la limite."""
    cutoff = time.time() - window
    recent = sum(1 for _, t in _rows(conn, _prefix(category, identifier)) if t >= cutoff)
    return recent >= limit

def record(conn, category, identifier, window):
    """Enregistre une tentative (insertion atomique) et purge les plus anciennes."""
    prefix = _prefix(category, identifier)
    now = time.time()
    key = prefix + format(time.time_ns(), '020d')
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO NOTHING", (key, repr(now)))
    old = [k for k, t in _rows(conn, prefix) if t < now - window]
    if old:
        with conn() as c:
            for k in old:
                c.execute("DELETE FROM settings WHERE key=?", (k,))

def clear(conn, category, identifier):
    """Efface les tentatives (après une connexion réussie)."""
    with conn() as c:
        c.execute("DELETE FROM settings WHERE key LIKE ?", (_prefix(category, identifier) + '%',))
