import unittest, uuid
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
        record=[('Copilot maintenance','https://example.com/article','2026-09-24T10:00:00+00:00','Maintenance Copilot avec une description officielle suffisamment complète pour expliquer concrètement la nouvelle fonction et son usage.')]
        with patch.object(server,'fetch_feed',return_value=record),patch.object(server,'enrich_record',side_effect=lambda r,c,v:r),patch.dict(server.os.environ,{'OPENAI_API_KEY':''}),patch.object(server.translation,'translate_public',side_effect=lambda t:'Français : '+t):
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
            self.assertEqual(status,404)
            self.assertEqual(payload['error'],'Introuvable')
            network.assert_not_called()

    def test_state_exposes_no_local_ai_configuration(self):
        state=server.state()
        self.assertNotIn('ai_local',state)
        self.assertNotIn('ai_model',state)
        self.assertNotIn('ai_status',state)
        self.assertNotIn('chat_history',state)

    def test_score_is_explained_and_bounded(self):
        a=server.classify('Copilot Power BI production maintenance qualité automatisation','')
        self.assertLessEqual(a['score'],100); self.assertGreaterEqual(a['score'],0); self.assertEqual(a['mode'],'Mots-clés'); self.assertIn('Correspondances',a['reason'])
    def test_article_guide_is_explicit_when_only_title_is_available(self):
        guide=server.article_guide('New model','Titre repéré sur le domaine officiel via Google Actualités. Consultez la publication originale pour son contenu complet.','Éditeur','IA et innovation')
        self.assertFalse(guide['details_available'])
        self.assertEqual(guide['key_points'],[])
        self.assertEqual(len(guide['checks']),3)

    def test_article_guide_extracts_three_factual_points(self):
        details='Première information suffisamment détaillée pour être retenue. Deuxième information suffisamment détaillée pour être retenue. Troisième information suffisamment détaillée pour être retenue. Quatrième information qui ne doit pas être ajoutée.'
        guide=server.article_guide('Titre',details,'Éditeur','Automatisation')
        self.assertTrue(guide['details_available'])
        self.assertEqual(len(guide['key_points']),3)
        self.assertIn('validation humaine',guide['checks'][2])
    def test_source_fallback_is_visible_and_persistent(self):
        name='OpenAI'; config=server.news_sources.BY_NAME[name]
        record=[('An official announcement','https://news.google.com/rss/articles/example','2026-09-25T00:00:00+00:00','Original excerpt')]
        def fetch(url):
            if url==config['feed']: raise OSError('Temporary failure')
            self.assertEqual(url,config['fallback']); return record
        with patch.object(server,'SOURCES',[(name,config['feed'])]),patch.object(server,'fetch_feed',side_effect=fetch),patch.object(server,'enrich_record',side_effect=lambda r,c,v:r),patch.object(server.translation,'translate_public',side_effect=lambda t:t):
            server.sync()
        state=server.state()
        self.assertEqual(state['articles'][0]['collection_mode'],'Publication officielle retrouvée via Google Actualités')
        self.assertIn('Google Actualités',next(s['status'] for s in state['sources'] if s['name']==name))
        self.assertEqual(len(state['sources']),len(server.news_sources.CATALOG))
        server.init()
        self.assertEqual(len(server.state()['sources']),len(server.news_sources.CATALOG))
    def test_paper_and_tool_news_rank_above_generic_news(self):
        import relevance
        paper=relevance.assess('Valmet launches AI assistant for paper machine operators','The new feature predicts web breaks on the paper machine and helps the pulp mill reduce downtime.','maintenance, qualité')
        copilot=relevance.assess('Introducing new Copilot features in Excel and Outlook','Microsoft 365 Copilot can now summarize meetings in Teams.','Copilot')
        generic=relevance.assess('A research residency for scientists','We are hiring researchers for a summer program.','maintenance')
        self.assertEqual(paper['category'],'Papeterie et process')
        self.assertIn('machine à papier',paper['opportunity'])
        self.assertTrue(copilot['new_feature'])
        self.assertIn('Microsoft 365 Copilot',copilot['tools'])
        self.assertNotIn('Copilot',[t for t in copilot['tools'] if t!='Microsoft 365 Copilot'])
        self.assertGreater(paper['score'],generic['score']+30)
        self.assertGreater(copilot['score'],generic['score']+30)
        data_center=relevance.assess('Old paper mill becomes a data center','The paper mill site will host a data center.','')
        self.assertLess(data_center['score'],paper['score']-30)
    def test_noise_pages_and_title_suffixes(self):
        import relevance
        self.assertTrue(relevance.is_noise('Ishmehar Chawla, Author - Salesforce'))
        self.assertTrue(relevance.is_noise('Start your career at Valmet - Valmet'))
        self.assertTrue(relevance.is_noise('Consultant in Agentic AI (f/m/d) - Siemens'))
        self.assertTrue(relevance.is_noise('Anything','https://www.salesforce.com/blog/author/someone/'))
        self.assertFalse(relevance.is_noise('Valmet to acquire MES business from Tieto','https://www.valmet.com/media/news/a'))
        self.assertEqual(relevance.clean_title('Mistral Large 4 est en poids ouvert - mistral.ai','Mistral AI'),'Mistral Large 4 est en poids ouvert')
        self.assertEqual(relevance.clean_title('Double rappel : la mémoire Agentforce - Salesforce','Salesforce IA'),'Double rappel : la mémoire Agentforce')
        self.assertEqual(relevance.clean_title('Avant - après : un cas concret','OpenAI'),'Avant - après : un cas concret')
    def test_noise_and_removed_sources_are_hidden_from_state(self):
        import json
        with server.conn() as c:
            for ident,title,url,source in [('a','Real Copilot news','https://example.com/a','OpenAI'),('b','Jane Doe, Author - Salesforce','https://example.com/b','Salesforce IA'),('c','Voices news','https://example.com/c','Ancienne source retirée')]:
                c.execute('INSERT INTO articles(id,title,url,source,excerpt,analysis) VALUES(?,?,?,?,?,?)',(ident,title,url,source,'Excerpt text',json.dumps(server.classify(title,'Excerpt text'))))
        self.assertEqual([a['id'] for a in server.state()['articles']],['a'])
        self.assertNotIn('excerpt',server.state()['articles'][0])
    def test_major_launches_are_must_read(self):
        import relevance
        self.assertTrue(relevance.must_read('OpenAI introduces a new ChatGPT agent for shopping','',''))
        self.assertTrue(relevance.must_read('Anthropic launches Claude Opus 5 model','','Anthropic / Claude'))
        self.assertFalse(relevance.must_read('Why the history of chatbots matters','',''))
        self.assertFalse(relevance.must_read('ElevenLabs Renews Security Certifications, Adds FedRAMP','','ElevenLabs'))
        launch=relevance.assess('OpenAI introduces a new ChatGPT agent for shopping','ChatGPT can now buy for you.','')
        self.assertTrue(launch['must_read'])
        self.assertGreater(launch['score'],relevance.assess('Why the history of chatbots matters','A long essay.','')['score']+25)
    def test_creative_tools_are_detected(self):
        import relevance
        video=relevance.assess('Runway releases a new video generation model','Generate cinematic video clips from text prompts.','')
        self.assertEqual(video['category'],'Création (vidéo, image, audio)')
        self.assertTrue(video['creative'])
        self.assertIn('Runway',video['tools'])
    def test_observatory_tracks_assistants_and_models(self):
        import observatory
        from datetime import datetime, timezone
        self.assertIn('claude',observatory.mentions('Anthropic launches Claude Opus 5'))
        self.assertIn('chatgpt',observatory.mentions('New ChatGPT agent'))
        self.assertEqual(observatory.mentions('Valmet paper machine'),[])
        now=datetime(2026,11,1,tzinfo=timezone.utc)
        articles=[dict(id=str(i),title='t',url='https://x/'+str(i),published='2026-10-2'+str(i)+'T10:00:00+00:00',source='Anthropic / Claude',
                       original_title='Anthropic launches Claude Opus 5',assistants=['claude'],must_read=i==0) for i in range(3)]
        board={o['id']:o for o in observatory.build(articles,now)}
        self.assertEqual(board['claude']['count30'],3)
        self.assertEqual(board['claude']['status'],'Actif')
        self.assertEqual(board['claude']['must_read'],1)
        self.assertEqual(board['claude']['models'][0]['name'],'Claude Opus 5')
        self.assertEqual(board['gemini']['count30'],0)
        self.assertEqual(observatory.build(articles,now)[0]['id'],'claude')
    def test_google_news_resolution_rejects_an_unofficial_domain(self):
        html='<div data-n-a-id="abc" data-n-a-ts="123" data-n-a-sg="sig"></div>'
        response=")]}'\n[[\"wrb.fr\",\"Fbv4je\",\"[\\\"garturlres\\\",\\\"https://evil.example/article\\\",1]\",null]]"
        from io import BytesIO
        from email.message import Message
        def page(content,content_type):
            stream=BytesIO(content.encode()); headers=Message(); headers['Content-Type']=content_type; stream.headers=headers; return stream
        with patch('urllib.request.urlopen',side_effect=[page(html,'text/html'),page(response,'application/json')]):
            self.assertIsNone(server.resolve_google_news_url('https://news.google.com/rss/articles/abc','anthropic.com'))

    def test_extracts_a_real_excerpt_from_the_official_page(self):
        html='''<html><head><meta property="og:description" content="A detailed official description explaining the product announcement and what has changed for customers today."></head><body><article><p>The release introduces a concrete capability for teams working with industrial information and documented workflows.</p><p>Customers can test the feature before enabling it more broadly in their organisation.</p></article></body></html>'''
        from io import BytesIO
        from email.message import Message
        page=BytesIO(html.encode()); headers=Message(); headers['Content-Type']='text/html; charset=utf-8'; page.headers=headers
        with patch('urllib.request.urlopen',return_value=page):
            excerpt=server.extract_public_excerpt('https://news.example.com/article','example.com')
        self.assertIn('detailed official description',excerpt)
        self.assertIn('concrete capability',excerpt)
        self.assertLessEqual(len(excerpt),1400)
    def test_rejects_a_generic_site_description(self):
        html='<html><head><meta property="og:description" content="Qwen offers comprehensive chatbot, image generation, document processing, search integration and tool utilization for everyone."></head></html>'
        from io import BytesIO
        from email.message import Message
        page=BytesIO(html.encode()); headers=Message(); headers['Content-Type']='text/html; charset=utf-8'; page.headers=headers
        with patch('urllib.request.urlopen',return_value=page):
            excerpt=server.extract_public_excerpt('https://qwen.example/blog?id=live','example',title='LiveTranslate identifies speakers and preserves meaning')
        self.assertEqual(excerpt,'')
    def test_feed_parsing(self):
        from io import BytesIO
        xml=b'<rss><channel><item><title>Official update</title><link>https://example.com/a?utm_source=rss</link><pubDate>Thu, 24 Sep 2026 10:00:00 GMT</pubDate><description>&lt;p&gt;Real excerpt&lt;/p&gt;</description></item><item><title>Bad link</title><link>javascript:alert(1)</link></item></channel></rss>'
        with patch('urllib.request.urlopen',return_value=BytesIO(xml)): rows=server.fetch_feed('https://example.com/feed')
        self.assertEqual(len(rows),1); self.assertEqual(rows[0][1],'https://example.com/a'); self.assertIn('2026-09-24',rows[0][2]); self.assertEqual(rows[0][3],'Real excerpt')
    def test_failed_source_does_not_invent_articles(self):
        with patch.object(server,'fetch_feed',side_effect=OSError('offline')): server.sync()
        self.assertEqual(server.state()['articles'],[]); self.assertTrue(all('Échec' in s['status'] for s in server.state()['sources']))

    def test_translation_persisted_without_replacing_original(self):
        details='New features are presented in this official excerpt with enough information to explain their purpose and expected use by customers.'
        record=[('Official update','https://example.com/news',None,details)]
        translations={'Official update':'Annonce officielle',details:'Nouvelles fonctionnalités avec des informations détaillées.'}
        with patch.object(server,'fetch_feed',return_value=record),patch.object(server,'enrich_record',side_effect=lambda r,c,v:r),patch.dict(server.os.environ,{'OPENAI_API_KEY':''}),patch.object(server.translation,'translate_public',side_effect=translations.__getitem__) as translate:
            server.sync(); server.sync()
            self.assertEqual(translate.call_count,2)
        article=server.state()['articles'][0]
        self.assertEqual(article['title'],'Annonce officielle')
        self.assertEqual(article['summary'],'Nouvelles fonctionnalités avec des informations détaillées.')
        self.assertEqual(article['original_title'],'Official update')
        self.assertFalse(article['translation_pending'])
        with server.conn() as c:
            self.assertEqual(c.execute('SELECT title FROM articles').fetchone()['title'],'Official update')

    def test_unavailable_translation_shows_original_text_and_retries(self):
        details='New features are presented in this official excerpt with enough information to explain their purpose and expected use by customers.'
        record=[('Official update','https://example.com/news',None,details)]
        official=[('OpenAI',server.news_sources.BY_NAME['OpenAI']['feed'])]
        with patch.object(server,'SOURCES',official),patch.object(server,'fetch_feed',return_value=record),patch.object(server,'enrich_record',side_effect=lambda r,c,v:r),patch.dict(server.os.environ,{'OPENAI_API_KEY':''}),patch.object(server.translation,'translate_public',side_effect=OSError('offline')):
            server.sync()
        a=server.state()['articles'][0]
        self.assertTrue(a['translation_pending'])
        self.assertEqual(a['title'],'Official update')
        self.assertIn('New features',a['summary'])
        self.assertIn('New features',a['details'])
        self.assertEqual(a['excerpt_label'],'Extrait original de la publication officielle')
        french='Texte français suffisamment détaillé pour expliquer les nouvelles fonctions, leur objectif et leur utilisation attendue par les clients.'
        with patch.object(server.translation,'translate_public',return_value=french):
            server.translate_articles()
        translated=server.state()['articles'][0]
        self.assertFalse(translated['translation_pending'])
        self.assertEqual(translated['excerpt_label'],'Extrait traduit de la publication officielle')

if __name__=='__main__': unittest.main()
