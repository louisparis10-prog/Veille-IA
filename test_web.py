import base64
import os
import unittest
import uuid
from unittest.mock import patch
import server
from app import create_app

class WebTests(unittest.TestCase):
    def setUp(self):
        self.environment=patch.dict(os.environ,{'DATABASE_URL':'','RENDER':'','APP_ENV':'test','APP_PASSWORD':'test-password-123456','APP_USERNAME':'louis'})
        self.environment.start()
        self.previous=server.DB
        server.DB=server.ROOT/('test-'+uuid.uuid4().hex+'.sqlite3')
        server.init()
        self.client=create_app().test_client()
        token=base64.b64encode(b'louis:test-password-123456').decode()
        self.headers={'Authorization':'Basic '+token,'Origin':'http://localhost'}
    def tearDown(self):
        server.DB.unlink(); server.DB=self.previous; self.environment.stop()
    def test_private_pages_and_public_health(self):
        self.assertEqual(self.client.get('/').status_code,401)
        self.assertEqual(self.client.get('/api/state').status_code,401)
        self.assertEqual(self.client.get('/healthz').status_code,200)
        with self.client.get('/',headers=self.headers) as response:
            self.assertEqual(response.status_code,200)
    def test_cross_origin_post_is_blocked(self):
        response=self.client.post('/api/item',json={'title':'Action'},headers={**self.headers,'Origin':'https://other.example'})
        self.assertEqual(response.status_code,403)
        self.assertEqual(server.state()['items'],[])
    def test_create_and_advance_action(self):
        response=self.client.post('/api/item',json={'title':'Réduire les saisies','stage':'Idée','notes':'Mesurer le temps gagné'},headers=self.headers)
        self.assertEqual(response.status_code,200)
        item=self.client.get('/api/state',headers=self.headers).json['items'][0]
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
    def test_production_rejects_missing_database_or_password(self):
        with patch.dict(os.environ,{'APP_ENV':'production','DATABASE_URL':''}):
            with self.assertRaises(RuntimeError): create_app()
        with patch.dict(os.environ,{'APP_ENV':'production','DATABASE_URL':'postgresql://unused','APP_PASSWORD':''}):
            with self.assertRaises(RuntimeError): create_app()
    def test_invalid_stage_and_payload(self):
        self.assertEqual(self.client.post('/api/item',json={'title':'A','stage':'invalid'},headers=self.headers).status_code,400)
        self.assertEqual(self.client.post('/api/item',json=[],headers=self.headers).status_code,400)
    def test_internal_error_does_not_disclose_credentials(self):
        with patch.object(server,'state',side_effect=RuntimeError('postgresql://private-password')):
            response=self.client.get('/api/state',headers=self.headers)
        self.assertEqual(response.status_code,503)
        self.assertNotIn('private-password',response.get_data(as_text=True))

if __name__=='__main__': unittest.main()
