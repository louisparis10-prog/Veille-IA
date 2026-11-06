"""Limitation des tentatives, partagée entre tous les processus via la base.

Le compteur en mémoire ne fonctionnait pas en ligne : Render lance plusieurs
processus web, chacun avec sa propre mémoire, donc aucun n'atteignait le seuil.

On enregistre donc chaque tentative comme une ligne distincte de la table settings
(aucune table à créer : le rôle Neon de l'application n'a pas le droit de créer des
objets). Clé : « rl:<catégorie>:<identifiant>:<horodatage> ». Chaque tentative est
une insertion indépendante : pas de lecture-modification-réécriture, donc aucune
écriture concurrente n'en écrase une autre (le défaut de la version précédente).

L'horodatage est en nanosecondes, sur 20 chiffres : l'ordre alphabétique des clés
suit l'ordre du temps, ce qui permet de compter et de purger par simple comparaison.
"""
import time

def _prefix(category, identifier):
    return 'rl:' + category + ':' + (identifier or '?').lower()[:60] + ':'

def _cutoff(prefix, window):
    return prefix + format(time.time_ns() - int(window * 1e9), '020d')

def blocked(conn, category, identifier, limit, window):
    """Vrai si le nombre de tentatives récentes atteint déjà la limite."""
    prefix = _prefix(category, identifier)
    with conn() as c:
        row = c.execute("SELECT COUNT(*) AS n FROM settings WHERE key LIKE ? AND key >= ?",
                        (prefix + '%', _cutoff(prefix, window))).fetchone()
    return (row['n'] if row else 0) >= limit

def record(conn, category, identifier, window):
    """Enregistre une tentative (insertion atomique) et purge les plus anciennes."""
    prefix = _prefix(category, identifier)
    key = prefix + format(time.time_ns(), '020d')
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO NOTHING", (key, ''))
        c.execute("DELETE FROM settings WHERE key LIKE ? AND key < ?", (prefix + '%', _cutoff(prefix, window)))

def clear(conn, category, identifier):
    """Efface les tentatives (après une connexion réussie)."""
    with conn() as c:
        c.execute("DELETE FROM settings WHERE key LIKE ?", (_prefix(category, identifier) + '%',))
