import tempfile, pathlib, unittest, json, uuid
from unittest.mock import patch
import server

class Tests(unittest.TestCase):
    def setUp(self):
        self.environment=patch.dict(server.os.environ,{'DATABASE_URL':'','APP_ENV':'test','RENDER':''})
        self.environment.start()
        self.previous=server.DB
        server.DB=server.ROOT/('test-'+uuid.uuid4().hex+'.sqlite3'); server.init()
    def tearDown(self):
        server.DB.unlink(); server.DB=self.previous; self.environment.stop()
    def test_dedup_and_persistence(self):
        record=[('Copilot maintenance','https://example.com/article','2026-09-24T10:00:00+00:00','Maintenance Copilot')]
        with patch.object(server,'fetch_feed',return_value=record),patch.dict(server.os.environ,{'OPENAI_API_KEY':''}),patch.object(server.translation,'translate_public',side_effect=lambda t:'Français : '+t):
            server.sync(); server.sync()
        with server.conn() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM articles').fetchone()[0],1)
            c.execute('UPDATE articles SET favorite=1,read=1')
        s=server.state(); self.assertEqual(s['articles'][0]['favorite'],1); self.assertEqual(s['articles'][0]['read'],1)
    def test_free_daily_ideas_persist_and_rotate(self):
        import ideas
        from datetime import datetime, timedelta, timezone
        seen=set()
        with patch.object(server,'ai',side_effect=AssertionError('Aucun appel payant')):
            for day in range(20):
                with patch.object(ideas,'datetime') as clock:
                    clock.now.return_value=datetime(2026,9,25,tzinfo=timezone.utc)+timedelta(days=day)
                    self.assertEqual(ideas.generate_daily()['count'],3)
                    current=ideas.read_daily()
                    ids={i['id'] for i in current['ideas']}
                    self.assertEqual(len(ids),3)
                    self.assertFalse(ids & seen)
                    seen.update(ids)
                    self.assertEqual(ideas.generate_daily()['status'],'already_generated')
                    self.assertEqual(ideas.read_daily(),current)
        self.assertEqual(len(seen),60)

    def test_free_mode_blocks_paid_calls_even_with_key(self):
        with patch.dict(server.os.environ,{'OPENAI_API_KEY':'not-a-real-key','ALLOW_PAID_AI':''}),patch('urllib.request.urlopen') as network:
            with self.assertRaises(server.AIUnavailable): server.ai('Bonjour')
            status,payload=server.perform_action('/api/ask',{'question':'Bonjour'})
            self.assertEqual(status,503)
            self.assertIn('sans frais',payload['error'])
            network.assert_not_called()

    def test_score_is_explained_and_bounded(self):
        a=server.classify('Copilot Power BI production maintenance qualité automatisation','')
        self.assertLessEqual(a['score'],100); self.assertGreaterEqual(a['score'],0); self.assertEqual(a['mode'],'Mots-clés'); self.assertIn('Correspondances',a['reason'])
    def test_source_fallback_is_visible_and_persistent(self):
        name='OpenAI'; config=server.news_sources.BY_NAME[name]
        record=[('An official announcement','https://news.google.com/rss/articles/example','2026-09-25T00:00:00+00:00','Original excerpt')]
        def fetch(url):
            if url==config['feed']: raise OSError('Temporary failure')
            self.assertEqual(url,config['fallback']); return record
        with patch.object(server,'SOURCES',[(name,config['feed'])]),patch.object(server,'fetch_feed',side_effect=fetch),patch.object(server.translation,'translate_public',side_effect=lambda t:t):
            server.sync()
        state=server.state()
        self.assertEqual(state['articles'][0]['collection_mode'],'Relais Google Actualités')
        self.assertIn('relais Google',next(s['status'] for s in state['sources'] if s['name']==name))
        self.assertEqual(len(state['sources']),26)
        server.init()
        self.assertEqual(len(server.state()['sources']),26)
    def test_feed_parsing(self):
        from io import BytesIO
        xml=b'<rss><channel><item><title>Official update</title><link>https://example.com/a?utm_source=rss</link><pubDate>Thu, 24 Sep 2026 10:00:00 GMT</pubDate><description>&lt;p&gt;Real excerpt&lt;/p&gt;</description></item><item><title>Bad link</title><link>javascript:alert(1)</link></item></channel></rss>'
        with patch('urllib.request.urlopen',return_value=BytesIO(xml)): rows=server.fetch_feed('https://example.com/feed')
        self.assertEqual(len(rows),1); self.assertEqual(rows[0][1],'https://example.com/a'); self.assertIn('2026-09-24',rows[0][2]); self.assertEqual(rows[0][3],'Real excerpt')
    def test_failed_source_does_not_invent_articles(self):
        with patch.object(server,'fetch_feed',side_effect=OSError('offline')): server.sync()
        self.assertEqual(server.state()['articles'],[]); self.assertTrue(all('Échec' in s['status'] for s in server.state()['sources']))

    def test_translation_persisted_without_replacing_original(self):
        record=[('Official update','https://example.com/news',None,'New features')]
        translations={'Official update':'Annonce officielle','New features':'Nouvelles fonctionnalités'}
        with patch.object(server,'fetch_feed',return_value=record),patch.dict(server.os.environ,{'OPENAI_API_KEY':''}),patch.object(server.translation,'translate_public',side_effect=translations.__getitem__) as translate:
            server.sync(); server.sync()
            self.assertEqual(translate.call_count,2)
        article=server.state()['articles'][0]
        self.assertEqual(article['title'],'Annonce officielle')
        self.assertEqual(article['summary'],'Nouvelles fonctionnalités')
        self.assertEqual(article['original_title'],'Official update')
        self.assertFalse(article['translation_pending'])
        with server.conn() as c:
            self.assertEqual(c.execute('SELECT title FROM articles').fetchone()['title'],'Official update')

    def test_unavailable_translation_retries_and_keeps_french_interface(self):
        record=[('Official update','https://example.com/news',None,'New features')]
        with patch.object(server,'fetch_feed',return_value=record),patch.dict(server.os.environ,{'OPENAI_API_KEY':''}),patch.object(server.translation,'translate_public',side_effect=OSError('offline')):
            server.sync()
        a=server.state()['articles'][0]
        self.assertTrue(a['translation_pending'])
        self.assertIn('en attente',a['title'])
        self.assertNotIn('New features',a['summary'])
        with patch.object(server.translation,'translate_public',return_value='Texte français'):
            server.translate_articles()
        self.assertFalse(server.state()['articles'][0]['translation_pending'])

if __name__=='__main__': unittest.main()
