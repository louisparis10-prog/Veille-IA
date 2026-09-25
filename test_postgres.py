"""Tests d'intégration sur le PostgreSQL éphémère de GitHub Actions."""
import json
import os
import unittest
import uuid
from urllib.parse import urlsplit
from unittest.mock import patch
import server
import manage

@unittest.skipUnless(os.environ.get('TEST_POSTGRES_URL'),'PostgreSQL de test non configuré')
class PostgresTests(unittest.TestCase):
    def setUp(self):
        import psycopg
        self.url=os.environ['TEST_POSTGRES_URL']
        if urlsplit(self.url).hostname not in ('localhost','127.0.0.1'):
            self.skipTest('Les tests utilisent uniquement un PostgreSQL local jetable.')
        self.schema='test_'+uuid.uuid4().hex
        self.real_connect=psycopg.connect
        with self.real_connect(self.url,sslmode='disable',autocommit=True) as c:
            c.execute('CREATE SCHEMA '+self.schema)
        def test_connect(url,**kwargs):
            kwargs['sslmode']='disable'
            kwargs['options']='-c search_path='+self.schema
            return self.real_connect(url,**kwargs)
        self.connector=patch('psycopg.connect',side_effect=test_connect); self.connector.start()
        self.environment=patch.dict(os.environ,{'DATABASE_URL':self.url,'OPENAI_API_KEY':''}); self.environment.start()
        server.init()
    def tearDown(self):
        self.environment.stop(); self.connector.stop()
        with self.real_connect(self.url,sslmode='disable',autocommit=True) as c:
            c.execute('DROP SCHEMA '+self.schema+' CASCADE')
    def test_collect_deduplicate_translate_and_modify(self):
        record=[('Factory update','https://example.com/update',None,'New robot')]
        with patch.object(server,'fetch_feed',return_value=record),patch.object(server.translation,'translate_public',return_value='Actualité traduite'):
            server.sync(); server.sync()
        state=server.state()
        self.assertEqual(len(state['articles']),1)
        self.assertEqual(state['articles'][0]['title'],'Actualité traduite')
        server.perform_action('/api/item',{'title':'Premier projet','stage':'Idée'})
        item=server.state()['items'][0]
        self.assertGreater(item['id'],0)
        server.perform_action('/api/item',{**item,'stage':'Projet'})
        self.assertEqual(server.state()['items'][0]['stage'],'Projet')
    def test_sqlite_import_and_sequence(self):
        old_path=server.DB
        source=server.ROOT/('test-'+uuid.uuid4().hex+'.sqlite3')
        try:
            with patch.dict(os.environ,{'DATABASE_URL':''}):
                server.DB=source; server.init()
                with server.conn() as c:
                    c.execute('INSERT INTO items(id,title,stage) VALUES(?,?,?)',(42,'Idée conservée','Test'))
                    c.execute("UPDATE settings SET value='maintenance' WHERE key='interests'")
            server.DB=old_path
            manage.migrate(source); manage.migrate(source)
            self.assertEqual(len(server.state()['items']),1)
            self.assertEqual(server.get_setting('interests'),'maintenance')
            server.perform_action('/api/item',{'title':'Nouvelle idée'})
            self.assertGreater(server.state()['items'][0]['id'],42)
        finally:
            server.DB=old_path
            if source.exists(): source.unlink()

if __name__=='__main__': unittest.main()
