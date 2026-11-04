import os
import unittest
import uuid
from unittest.mock import patch
import auth
import server
from app import create_app

PASSWORD='mot-de-passe-de-test'

class WebTests(unittest.TestCase):
    def setUp(self):
        self.environment=patch.dict(os.environ,{'DATABASE_URL':'','RENDER':'','APP_ENV':'test'})
        self.environment.start()
        self.iterations=patch.object(auth,'ITERATIONS',1000); self.iterations.start()
        self.sleep=patch('app.time.sleep'); self.sleep.start()
        self.previous=server.DB
        server.DB=server.ROOT/('test-'+uuid.uuid4().hex+'.sqlite3')
        server.init()
        self.app=create_app(); server.AUTO_TRANSLATE=False
        self.client=self.app.test_client()
        self.assertEqual(self.client.post('/setup',data={'username':'louis','password':PASSWORD,'confirm':PASSWORD}).status_code,303)
        self.headers={'Origin':'http://localhost'}
    def tearDown(self):
        self.sleep.stop(); self.iterations.stop()
        server.DB.unlink(); server.DB=self.previous; self.environment.stop()
    def visitor(self): return self.app.test_client()

    def test_first_launch_asks_to_create_access(self):
        auth.reset(server.conn)
        app=create_app(); server.AUTO_TRANSLATE=False
        client=app.test_client()
        self.assertTrue(client.get('/').headers['Location'].endswith('/setup'))
        self.assertTrue(client.get('/login').headers['Location'].endswith('/setup'))
        self.assertTrue(client.get('/api/state').json['setup'])
        with client.get('/setup') as page: self.assertEqual(page.status_code,200)
        self.assertIn('m=faible',client.post('/setup',data={'username':'louis','password':'court','confirm':'court'}).headers['Location'])
        self.assertIn('m=different',client.post('/setup',data={'username':'louis','password':PASSWORD,'confirm':PASSWORD+'x'}).headers['Location'])
        self.assertIn('m=identifiant',client.post('/setup',data={'username':'avec espace','password':PASSWORD,'confirm':PASSWORD}).headers['Location'])
        self.assertIsNone(auth.load(server.conn))
        created=client.post('/setup',data={'username':'Louis','password':PASSWORD,'confirm':PASSWORD})
        self.assertTrue(created.headers['Location'].endswith('/'))
        self.assertEqual(client.get('/api/state').json['user'],'Louis')
        record=auth.load(server.conn)
        self.assertNotIn(PASSWORD,str(record))
        # Une fois l'accès créé, personne ne peut le remplacer par la page de création.
        other=app.test_client()
        self.assertIn('m=existe',other.post('/setup',data={'username':'pirate','password':'autre-mot-de-passe','confirm':'autre-mot-de-passe'}).headers['Location'])
        self.assertEqual(auth.load(server.conn)['username'],'Louis')
        self.assertTrue(other.get('/setup').headers['Location'].endswith('/login'))

    def test_private_pages_and_public_health(self):
        visitor=self.visitor()
        self.assertTrue(visitor.get('/').headers['Location'].endswith('/login'))
        self.assertEqual(visitor.get('/api/state').status_code,401)
        self.assertNotIn('WWW-Authenticate',visitor.get('/api/state').headers)
        self.assertEqual(visitor.get('/healthz').status_code,200)
        with visitor.get('/login') as page:
            self.assertEqual(page.status_code,200)
            self.assertIn('Connexion',page.get_data(as_text=True))
        with self.client.get('/') as page: self.assertEqual(page.status_code,200)

    def test_login_session_and_logout(self):
        visitor=self.visitor()
        self.assertIn('m=identifiants',visitor.post('/login',data={'username':'louis','password':'mauvais'}).headers['Location'])
        self.assertEqual(visitor.get('/api/state').status_code,401)
        right=visitor.post('/login',data={'username':'LOUIS','password':PASSWORD,'remember':'1'})
        self.assertTrue(right.headers['Location'].endswith('/'))
        self.assertIn('HttpOnly',right.headers['Set-Cookie'])
        self.assertEqual(visitor.get('/api/state').json['user'],'louis')
        self.assertTrue(visitor.get('/login').headers['Location'].endswith('/'))
        self.assertEqual(visitor.post('/logout',json={},headers={'Origin':'https://other.example'}).status_code,403)
        self.assertEqual(visitor.post('/logout',json={},headers=self.headers).status_code,200)
        self.assertEqual(visitor.get('/api/state').status_code,401)

    def test_login_from_another_site_is_refused(self):
        visitor=self.visitor()
        response=visitor.post('/login',data={'username':'louis','password':PASSWORD},headers={'Origin':'https://other.example'})
        self.assertIn('m=origine',response.headers['Location'])
        self.assertEqual(visitor.get('/api/state').status_code,401)

    def test_repeated_failures_are_blocked(self):
        visitor=self.visitor()
        for _ in range(8): visitor.post('/login',data={'username':'louis','password':'faux'})
        self.assertIn('m=bloque',visitor.post('/login',data={'username':'louis','password':PASSWORD}).headers['Location'])

    def test_change_password_invalidates_other_sessions(self):
        other=self.visitor(); other.post('/login',data={'username':'louis','password':PASSWORD})
        self.assertEqual(other.get('/api/state').status_code,200)
        wrong=self.client.post('/api/password',json={'current':'faux','new':'nouveau-secret-123','confirm':'nouveau-secret-123'},headers=self.headers)
        self.assertEqual(wrong.status_code,403)
        mismatch=self.client.post('/api/password',json={'current':PASSWORD,'new':'nouveau-secret-123','confirm':'autre'},headers=self.headers)
        self.assertEqual(mismatch.status_code,400)
        done=self.client.post('/api/password',json={'current':PASSWORD,'new':'nouveau-secret-123','confirm':'nouveau-secret-123'},headers=self.headers)
        self.assertEqual(done.status_code,200)
        self.assertEqual(self.client.get('/api/state').status_code,200)
        self.assertEqual(other.get('/api/state').status_code,401)
        visitor=self.visitor()
        self.assertIn('m=identifiants',visitor.post('/login',data={'username':'louis','password':PASSWORD}).headers['Location'])
        self.assertTrue(visitor.post('/login',data={'username':'louis','password':'nouveau-secret-123'}).headers['Location'].endswith('/'))

    def test_cross_origin_post_is_blocked(self):
        response=self.client.post('/api/item',json={'title':'Action'},headers={'Origin':'https://other.example'})
        self.assertEqual(response.status_code,403)
        self.assertEqual(server.state()['items'],[])
    def test_create_and_advance_action(self):
        response=self.client.post('/api/item',json={'title':'Réduire les saisies','stage':'Idée','notes':'Mesurer le temps gagné'},headers=self.headers)
        self.assertEqual(response.status_code,200)
        item=self.client.get('/api/state').json['items'][0]
        response=self.client.post('/api/item',json={**item,'stage':'Test'},headers=self.headers)
        self.assertEqual(response.status_code,200)
        self.assertEqual(server.state()['items'][0]['stage'],'Test')
    def test_profile_uses_new_interests_immediately(self):
        with server.conn() as c:
            import json
            c.execute('INSERT INTO articles(id,title,excerpt,analysis) VALUES(?,?,?,?)',('test','Robotics news','Robot factory',json.dumps(server.classify('Robotics news','Robot factory'))))
        response=self.client.post('/api/settings',json={'interests':'robot'},headers=self.headers)
        self.assertEqual(response.status_code,200)
        self.assertIn('robot',server.state()['articles'][0]['reason'])
    def test_production_requires_database(self):
        with patch.dict(os.environ,{'APP_ENV':'production','DATABASE_URL':''}):
            with self.assertRaises(RuntimeError): create_app()
        server.AUTO_TRANSLATE=False
    def test_invalid_stage_and_payload(self):
        self.assertEqual(self.client.post('/api/item',json={'title':'A','stage':'invalid'},headers=self.headers).status_code,400)
        self.assertEqual(self.client.post('/api/item',json=[],headers=self.headers).status_code,400)
    def test_internal_error_does_not_disclose_credentials(self):
        with patch.object(server,'state',side_effect=RuntimeError('postgresql://private-password')):
            response=self.client.get('/api/state')
        self.assertEqual(response.status_code,503)
        self.assertNotIn('private-password',response.get_data(as_text=True))

if __name__=='__main__': unittest.main()
