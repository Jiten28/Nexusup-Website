import json
from unittest.mock import patch
from datetime import timedelta
from django.test import TestCase,Client,override_settings
from django.core.management import call_command
from django.core.cache import cache
from django.utils import timezone
from .models import Article,NewsSource,Category,Tag,FetchRun,ContactMessage,Comment
from .ingestion import ingest,NewsAPIAdapter
from .tests_enhancements import RSS

@override_settings(DEBUG=True)
class RESTTests(TestCase):
    @classmethod
    def setUpTestData(cls):call_command('seed_demo',verbosity=0)
    def setUp(self):cache.clear()
    def test_published_only_and_detail_privacy(self):
        post=Article.objects.first();post.status='draft';post.save()
        self.assertEqual(self.client.get(f'/api/articles/{post.slug}/').status_code,404)
        ids=[x['id'] for x in self.client.get('/api/articles/').json()['results']]
        self.assertNotIn(post.pk,ids)
        post.status='published';post.published_at=timezone.now()+timedelta(days=1);post.save()
        self.assertEqual(self.client.get(f'/api/articles/{post.slug}/').status_code,404)
    def test_pagination_search_category_and_tags(self):
        first=Article.objects.first();tag=Tag.objects.create(name='Test topic',slug='test-topic');first.tags.add(tag)
        payload=self.client.get('/api/articles/',{'page_size':3}).json()
        self.assertEqual(len(payload['results']),3);self.assertTrue(payload['next'])
        second=self.client.get(payload['next']).json()
        self.assertFalse(set(x['id'] for x in payload['results'])&set(x['id'] for x in second['results']))
        for params in [{'q':first.title},{'tag':'test-topic'},{'category':first.category.slug}]:
            data=self.client.get('/api/articles/',params).json()['results'];self.assertTrue(data);self.assertIn(first.pk,[x['id'] for x in data])
        self.assertEqual(self.client.get('/api/articles/',{'page':9999}).status_code,404)
        self.assertEqual(self.client.get('/api/articles/',{'q':'DOES_NOT_EXIST'}).json()['count'],0)
    def test_home_disjoint_and_exclude(self):
        data=self.client.get('/api/home/').json()
        a={x['id'] for x in data['carousel']};b={x['id'] for x in data['featured']}
        self.assertFalse(a&b);self.assertLessEqual(len(data['carousel']),4);self.assertLessEqual(len(data['featured']),5)
        latest=self.client.get('/api/articles/',{'exclude':','.join(map(str,data['excluded']))}).json()
        self.assertFalse(set(data['excluded'])&set(x['id'] for x in latest['results']))
        self.assertEqual(len(data['excluded']),len(a|b))
    def test_empty_home(self):
        Article.objects.update(status='draft');d=self.client.get('/api/home/').json()
        self.assertEqual(d,{'carousel':[],'featured':[],'excluded':[]})
    def test_readonly_and_no_private_fields(self):
        data=self.client.get('/api/articles/').json()['results'][0]
        for field in ['author','source_guid','source_url_hash','normalized_title_hash','rights_confirmed','last_error']:
            self.assertNotIn(field,data)
        for path in ['/api/articles/','/api/categories/','/api/tags/']:
            self.assertEqual(self.client.post(path,{}).status_code,405)
    def test_related_and_only_approved_comments(self):
        post=Article.objects.first();Comment.objects.create(article=post,name='Private',body='Pending')
        Comment.objects.create(article=post,name='Public',body='Approved',approved=True)
        data=self.client.get(f'/api/articles/{post.slug}/').json()
        self.assertEqual([c['body'] for c in data['comments']],['Approved'])
        related=self.client.get(f'/api/articles/{post.slug}/related/').json()['results']
        self.assertNotIn(post.pk,[x['id'] for x in related])
    def test_media_and_category_endpoints(self):
        self.assertTrue(self.client.get('/api/categories/').json())
        data=self.client.get('/api/articles/').json()['results']
        for a in data:
            if a['image']:self.assertTrue(a['image'].startswith('http://testserver/media/'))
    def test_form_csrf_validation_and_moderation(self):
        strict=Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post('/api/contact/',data='{}',content_type='application/json').status_code,403)
        token=strict.get('/api/csrf/').json()['csrfToken']
        response=strict.post('/api/contact/',data=json.dumps({'name':'Test','email':'test@example.com','message':'A test message'}),content_type='application/json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,201);self.assertEqual(ContactMessage.objects.count(),1)
        self.assertEqual(strict.post('/api/contact/',data='{}',content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,429)
        cache.clear();post=Article.objects.first()
        self.assertEqual(strict.post(f'/api/articles/{post.slug}/comments/',data=json.dumps({'name':'Test','body':'A comment'}),content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,201)
        self.assertFalse(Comment.objects.get().approved)
    def test_invalid_forms(self):
        self.assertEqual(self.client.post('/api/contact/',data='{',content_type='application/json').status_code,400)
        cache.clear();self.assertEqual(self.client.post('/api/contact/',data='{}',content_type='application/json').status_code,400)
    @override_settings(CORS_ALLOWED_ORIGINS=['https://frontend.example'],CORS_ALLOW_CREDENTIALS=True,CSRF_TRUSTED_ORIGINS=['https://frontend.example'])
    def test_separate_origin_cors_and_csrf(self):
        response=self.client.get('/api/articles/',HTTP_ORIGIN='https://frontend.example')
        self.assertEqual(response['Access-Control-Allow-Origin'],'https://frontend.example')
        denied=self.client.get('/api/articles/',HTTP_ORIGIN='https://untrusted.example')
        self.assertNotIn('Access-Control-Allow-Origin',denied)
        strict=Client(enforce_csrf_checks=True);token=strict.get('/api/csrf/').json()['csrfToken']
        data=json.dumps({'name':'Test','email':'test@example.com','message':'Cross-origin test'})
        self.assertEqual(strict.post('/api/contact/',data=data,content_type='application/json',HTTP_ORIGIN='https://untrusted.example',HTTP_X_CSRFTOKEN=token).status_code,403)
        self.assertEqual(strict.post('/api/contact/',data=data,content_type='application/json',HTTP_ORIGIN='https://frontend.example',HTTP_X_CSRFTOKEN=token).status_code,201)
    def test_health(self):
        self.assertEqual(self.client.get('/health/live/').status_code,200)
        self.assertEqual(self.client.get('/health/ready/').status_code,200)
    @patch('apps.news.rest.connection.cursor',side_effect=Exception('private-password'))
    def test_health_sanitized_failure(self,cursor):
        response=self.client.get('/health/ready/');self.assertEqual(response.status_code,503);self.assertNotIn('private-password',response.content.decode())

@override_settings(DEBUG=True, NEWS_FETCH_ENABLED=True)
class TrustTests(TestCase):
    @classmethod
    def setUpTestData(cls):call_command('seed_demo',verbosity=0)
    def source(self,**kwargs):return NewsSource.objects.create(name='Test source',feed_url='https://publisher.example/rss',default_category=Category.objects.first(),enabled=True,rights_confirmed=True,**kwargs)
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS)
    def test_auto_publish_without_trust_is_draft(self,fetch):
        s=self.source(auto_publish=True);ingest(s);self.assertEqual(Article.objects.get(source=s).status,'draft')
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS)
    def test_trust_without_auto_publish_is_draft(self,fetch):
        s=self.source(trusted=True);ingest(s);self.assertEqual(Article.objects.get(source=s).status,'draft')
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS)
    def test_both_flags_publish(self,fetch):
        s=self.source(trusted=True,auto_publish=True);ingest(s);self.assertEqual(Article.objects.get(source=s).status,'published')
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS.replace(b'<pubDate>Sun, 18 Oct 2026 05:00:00 GMT</pubDate>',b''))
    def test_undated_stays_draft(self,fetch):
        s=self.source(trusted=True,auto_publish=True);ingest(s);a=Article.objects.get(source=s);self.assertEqual(a.status,'draft');self.assertIsNone(a.source_published_at)
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS)
    def test_title_and_guid_dedup(self,fetch):
        s=self.source();ingest(s);s.next_fetch_at=None;s.save()
        fetch.return_value=RSS.replace(b'publisher.example/story',b'publisher.example/other')
        self.assertEqual(ingest(s)['skipped'],1)
    @patch('apps.news.ingestion.fetch_bytes',return_value=b'<broken')
    def test_malformed_logs_failure(self,fetch):
        s=self.source()
        with self.assertRaises(ValueError):ingest(s)
        self.assertFalse(FetchRun.objects.get().success)
    @patch('apps.news.ingestion.fetch_bytes')
    def test_disabled_never_fetches(self,fetch):
        s=self.source();s.enabled=False;s.save()
        with self.assertRaises(ValueError):ingest(s)
        fetch.assert_not_called()
    @override_settings(NEWS_API_KEY='mock-not-a-real-key')
    @patch('apps.news.network.fetch_json',return_value={'status':'ok','articles':[{'title':'A source report','url':'https://publisher.example/report','publishedAt':'2026-10-18T05:00:00Z','description':'Excerpt'}]})
    def test_newsapi_normalization(self,fetch):
        s=self.source();s.feed_url='https://newsapi.org/v2/top-headlines?country=in'
        data=NewsAPIAdapter().fetch(s);self.assertEqual(data[0]['title'],'A source report');self.assertTrue(data[0]['published'].tzinfo)
        s.feed_url='https://untrusted.example/api'
        with self.assertRaises(ValueError):NewsAPIAdapter().fetch(s)

    def test_articles_order_by_source_publication_date(self):
        from datetime import timedelta
        now=timezone.now()
        older=Article.objects.create(title='Older source report',slug='older-source-report',category=Article.objects.first().category,author=Article.objects.first().author,excerpt='Older',body='Body',status='published',is_sample=False,published_at=now,source_published_at=now-timedelta(days=2),imported_at=now)
        newer=Article.objects.create(title='Newer source report',slug='newer-source-report',category=older.category,author=older.author,excerpt='Newer',body='Body',status='published',is_sample=False,published_at=now-timedelta(days=1),source_published_at=now-timedelta(hours=1),imported_at=now)
        ids=[x['id'] for x in self.client.get('/api/articles/').json()['results']]
        self.assertLess(ids.index(newer.id),ids.index(older.id))
