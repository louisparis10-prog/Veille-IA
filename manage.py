"""Commandes d'administration, indépendantes du serveur web."""
import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
import server

TABLES=('settings','sources','articles','items','activity','translations')

def migrate(source):
    if not os.environ.get('DATABASE_URL'): raise ValueError('DATABASE_URL est obligatoire pour importer vers Neon.')
    source=Path(source).resolve()
    if not source.is_file(): raise ValueError('Base SQLite source introuvable.')
    old=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
    old.row_factory=sqlite3.Row
    try:
        with server.conn() as target:
            counts={}
            for table in TABLES:
                rows=old.execute('SELECT * FROM '+table).fetchall()
                counts[table]=len(rows)
                for row in rows:
                    columns=list(row.keys())
                    placeholders=','.join('?' for _ in columns)
                    # Import idempotent. Conserver les modifications déjà faites en ligne.
                    query='INSERT INTO '+table+' ('+','.join(columns)+') VALUES ('+placeholders+') ON CONFLICT DO NOTHING'
                    if table=='settings':
                        query=query.replace('ON CONFLICT DO NOTHING','ON CONFLICT(key) DO UPDATE SET value=excluded.value')
                    target.execute(query,tuple(row))
            target.execute("SELECT setval(pg_get_serial_sequence('items','id'), GREATEST(COALESCE((SELECT MAX(id) FROM items),0),1), EXISTS(SELECT 1 FROM items))")
        return counts
    finally: old.close()

def main():
    parser=argparse.ArgumentParser(description='Administration de Signal')
    parser.add_argument('command',choices=['init','sync','migrate','check'])
    parser.add_argument('--source',default=str(server.DB))
    args=parser.parse_args()
    try:
        server.init()
        if args.command=='sync':
            result=server.sync()
            with server.conn() as c:
                statuses=[r['status'] for r in c.execute('SELECT status FROM sources')]
            print(json.dumps(result,ensure_ascii=False))
            if all(s.startswith('Échec') for s in statuses) or result.get('pending',0): return 1
        elif args.command=='migrate': print(json.dumps(migrate(args.source),ensure_ascii=False))
        elif args.command=='check':
            with server.conn() as c:
                print(json.dumps({table:c.execute('SELECT COUNT(*) AS n FROM '+table).fetchone()['n'] for table in TABLES}))
        else: print('Base de données initialisée.')
        return 0
    except Exception as error:
        print('Opération interrompue ('+type(error).__name__+'). Vérifiez la configuration et la connexion à la base.',file=sys.stderr)
        return 1

if __name__=='__main__': raise SystemExit(main())
