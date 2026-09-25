"""Stockage PostgreSQL en ligne ; SQLite conservé pour l'utilisation locale."""
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager

class PostgresConnection:
    def __init__(self, connection): self.connection=connection
    def execute(self, query, parameters=()):
        return self.connection.execute(query.replace('?', '%s'), parameters)
    def executescript(self, script):
        for statement in script.split(';'):
            if statement.strip():
                self.execute(statement.replace('id INTEGER PRIMARY KEY,title TEXT,stage TEXT',
                    'id BIGSERIAL PRIMARY KEY,title TEXT,stage TEXT'))

@contextmanager
def connect(sqlite_path):
    url=os.environ.get('DATABASE_URL')
    if url:
        import psycopg
        from psycopg.rows import dict_row
        # Neon exige TLS ; ne jamais journaliser la chaîne de connexion.
        with psycopg.connect(url, sslmode='require', connect_timeout=15, row_factory=dict_row) as connection:
            yield PostgresConnection(connection)
    else:
        if os.environ.get('RENDER') or os.environ.get('APP_ENV')=='production':
            raise RuntimeError('DATABASE_URL est obligatoire en production.')
        connection=sqlite3.connect(sqlite_path,timeout=30)
        connection.row_factory=sqlite3.Row
        try:
            with connection: yield connection
        finally: connection.close()

@contextmanager
def collection_lock(sqlite_path):
    if not os.environ.get('DATABASE_URL'):
        yield True
        return
    # Une connexion gardée pendant tous les téléchargements peut être fermée par
    # le pooler Neon. Une courte transaction réserve donc un bail, puis libère la
    # connexion pendant le travail réseau.
    token=uuid.uuid4().hex
    now=time.time()
    acquired=False
    with connect(sqlite_path) as c:
        mutex=c.execute('SELECT pg_try_advisory_xact_lock(782361940) AS acquired').fetchone()['acquired']
        if mutex:
            row=c.execute("SELECT value FROM settings WHERE key='collection_lease'").fetchone()
            try: lease=json.loads(row['value']) if row else {}
            except Exception: lease={}
            if now-float(lease.get('started',0))>3600:
                c.execute("INSERT INTO settings(key,value) VALUES('collection_lease',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(json.dumps({'token':token,'started':now}),))
                acquired=True
    try:
        yield acquired
    finally:
        if acquired:
            with connect(sqlite_path) as c:
                mutex=c.execute('SELECT pg_try_advisory_xact_lock(782361940) AS acquired').fetchone()['acquired']
                if mutex:
                    row=c.execute("SELECT value FROM settings WHERE key='collection_lease'").fetchone()
                    try: lease=json.loads(row['value']) if row else {}
                    except Exception: lease={}
                    if lease.get('token')==token:
                        c.execute("DELETE FROM settings WHERE key='collection_lease'")
