"""Stockage PostgreSQL en ligne ; SQLite conservé pour l'utilisation locale."""
import os
import sqlite3
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
    # Verrou transactionnel compatible avec la connexion mutualisée Neon.
    # Il empêche une collecte Render et une collecte planifiée de se chevaucher.
    with connect(sqlite_path) as c:
        acquired=c.execute('SELECT pg_try_advisory_xact_lock(782361940) AS acquired').fetchone()['acquired']
        yield acquired
