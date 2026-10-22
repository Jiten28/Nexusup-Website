"""Offline integration/regression tests; provider responses are deterministic fixtures."""
from datetime import timedelta
from unittest.mock import patch,Mock
import json
from django.test import TestCase,override_settings,Client
from django.core.management import call_command,CommandError
from django.core.cache import cache
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from .models import Article,Category,NewsSource,FetchRun
from .ingestion import ingest,normalize_url,RSSAdapter
from . import services,network

RSS=b'''<?xml version="1.0"?><rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>QA Feed</title><item><title>Test India report</title><link>https://publisher.example/story?utm_source=rss&amp;x=1</link><guid>qa-1</guid><description>&lt;b&gt;Attributed excerpt&lt;/b&gt;</description><pubDate>Sun, 18 Oct 2026 05:00:00 GMT</pubDate><category>technology</category><media:content url="https://images.example/story.jpg" type="image/jpeg"/></item></channel></rss>'''
ATOM=b'''<feed xmlns="http://www.w3.org/2005/Atom"><title>QA</title><entry><id>atom-1</id><title>Atom report</title><link href="https://publisher.example/atom"/><updated>2026-10-18T05:00:00Z</updated><summary>Atom summary</summary></entry></feed>'''

@override_settings(DEBUG=True, NEWS_FETCH_ENABLED=True)
class EnhancementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo',verbosity=0)
        call_command('configure_sources',verbosity=0)
    def setUp(self):
        cache.clear()
        self.source=NewsSource.objects.first()
        self.source.enabled=True;self.source.rights_confirmed=True
        self.source.save()
    def ready(self):
        NewsSource.objects.filter(pk=self.source.pk).update(next_fetch_at=None)
        self.source.refresh_from_db()
    def test_single_horizontal_carousel_and_images(self):
        r=self.client.get('/')
        self.assertContains(r,'data-component="horizontal-headlines"')
        self.assertNotContains(r,'data-component="image-slider"')
        self.assertNotContains(r,'data-component="headlines-marquee"')
        self.assertTrue(all(p.image_src for p in r.context['slides']))
        for control in ['data-horizontal="prev"','data-horizontal="next"','data-horizontal="pause"']:
            self.assertContains(r,control)
    def test_source_configuration_validation(self):
        from django.core.exceptions import ValidationError
        self.source.category_map=['invalid']
        with self.assertRaises(ValidationError):self.source.full_clean()
        self.source.category_map={};self.source.image_hosts='invalid'
        with self.assertRaises(ValidationError):self.source.full_clean()
        self.source.image_hosts=[];self.source.interval_minutes=1
        with self.assertRaises(ValidationError):self.source.full_clean()
    def test_home_never_fetches_network(self):
        with patch('apps.news.network.fetch_bytes',side_effect=AssertionError('Network on homepage')):
            self.assertEqual(self.client.get('/').status_code,200)
    def test_category_candidates_idempotent_and_disabled(self):
        n=NewsSource.objects.count();call_command('configure_sources',verbosity=0)
        self.assertEqual(n,NewsSource.objects.count())
        for slug in ['india','world','politics','sports','entertainment','health-and-lifestyle']:
            self.assertEqual(self.client.get('/category/'+slug+'/').status_code,200)
    def test_normalize_tracking_query_and_fragment(self):
        self.assertEqual(normalize_url('https://PUBLISHER.example/story?utm_medium=x&b=2&a=1#top'),'https://publisher.example/story?a=1&b=2')
        for value in ['javascript:alert(1)','http://127.0.0.1/','https://localhost/','https://user:pw@host.example/','https://host.example:8000/']:
            with self.assertRaises(ValueError):normalize_url(value)
    def test_rss_atom_and_no_full_article(self):
        row=RSSAdapter().parse(RSS)[0]
        self.assertEqual(row['excerpt'],'Attributed excerpt')
        self.assertEqual(row['published'].year,2026)
        self.assertEqual(RSSAdapter().parse(ATOM)[0]['url'],'https://publisher.example/atom')
        with self.assertRaises(Exception):RSSAdapter().parse(b'<!DOCTYPE a [<!ENTITY x "bad">]><a>&x;</a>')
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS)
    def test_dedup_review_image_permissions_and_feature_preserved(self,fetch):
        featured=list(Article.objects.filter(featured=True).values_list('pk',flat=True))
        self.assertEqual(ingest(self.source)['imported'],1)
        post=Article.objects.get(source=self.source)
        self.assertEqual(post.status,'draft');self.assertFalse(post.featured);self.assertFalse(post.is_sample)
        self.assertEqual(post.remote_image_url,'')
        self.assertEqual(post.canonical_source_url,'https://publisher.example/story?x=1')
        self.assertNotIn('Attributed excerpt',post.body)
        self.assertEqual(featured,list(Article.objects.filter(featured=True).values_list('pk',flat=True)))
        self.ready();self.assertEqual(ingest(self.source)['skipped'],1)
        self.assertEqual(Article.objects.filter(source=self.source).count(),1)
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS)
    def test_category_map_and_permitted_image(self,fetch):
        self.source.category_map={'technology':'technology'};self.source.allow_images=True
        self.source.image_hosts=['images.example'];self.source.auto_publish=True;self.source.trusted=True;self.source.save()
        ingest(self.source)
        post=Article.objects.get(source=self.source)
        self.assertEqual(post.category.slug,'technology');self.assertTrue(post.image_src.startswith('https://images.example/'))
        self.assertEqual(post.status,'published')
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS)
    def test_dry_run_no_writes(self,fetch):
        n=Article.objects.count();self.assertEqual(ingest(self.source,dry_run=True)['eligible'],1)
        self.assertEqual(n,Article.objects.count());self.assertEqual(FetchRun.objects.count(),0)
    @patch('apps.news.ingestion.fetch_bytes',side_effect=TimeoutError('secret-provider-value'))
    def test_failure_keeps_stored_content_and_sanitizes(self,fetch):
        n=Article.objects.count()
        with self.assertRaises(ValueError):ingest(self.source)
        self.assertEqual(n,Article.objects.count());self.source.refresh_from_db()
        self.assertNotIn('secret-provider-value',self.source.last_error)
        self.assertFalse(FetchRun.objects.get().success)
        self.assertEqual(self.client.get('/').status_code,200)
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS)
    def test_fetch_claim_interval_and_rights_gate(self,fetch):
        ingest(self.source);self.source.refresh_from_db()
        self.assertTrue(ingest(self.source)['deferred']);self.assertEqual(fetch.call_count,1)
        self.source.rights_confirmed=False
        with self.assertRaises(ValueError):ingest(self.source)
    @override_settings(NEWS_FETCH_ENABLED=False)
    def test_management_command_opt_in(self):
        with self.assertRaises(CommandError):call_command('fetch_news')
    def test_breaking_samples_excluded_and_expiry(self):
        post=Article.objects.first();post.breaking_until=timezone.now()+timedelta(hours=1);post.save()
        self.assertFalse(list(self.client.get('/').context['breaking']))
        post.is_sample=False;post.save();self.assertIn(post,list(self.client.get('/').context['breaking']))
        post.breaking_until=timezone.now()-timedelta(seconds=1);post.save()
        self.assertFalse(list(self.client.get('/').context['breaking']))
    def test_admin_central_feature_action(self):
        editor=get_user_model().objects.create_user(username='qa-feature-admin',is_staff=True,is_superuser=True)
        self.client.force_login(editor);post=Article.objects.last()
        self.assertEqual(self.client.post('/admin/news/article/',{'action':'make_central','_selected_action':[post.pk]}).status_code,302)
        self.assertEqual(list(Article.objects.filter(featured=True).values_list('pk',flat=True)),[post.pk])
    @override_settings(UTILITIES_NETWORK_ENABLED=False,TRANSLATION_PROVIDER='disabled')
    def test_disabled_providers_have_explicit_errors(self):
        for path in ['/api/currency/','/api/weather/?lat=17&lon=78','/api/cities/?name=Delhi','/api/languages/']:
            r=self.client.get(path);self.assertEqual(r.status_code,503);self.assertIn('error',r.json())
    @override_settings(UTILITIES_NETWORK_ENABLED=True)
    @patch('apps.news.services.fetch_json',return_value={'rate':.012,'date':'2026-10-18'})
    def test_currency_provider_caching_and_validation(self,fetch):
        a=services.currency('INR','USD');b=services.currency('INR','USD')
        self.assertEqual(a,b);self.assertEqual(fetch.call_count,1)
        self.assertEqual(services.currency('USD','USD')['rate'],1)
        with self.assertRaises(ValueError):services.currency('XXX','USD')
    @override_settings(UTILITIES_NETWORK_ENABLED=True)
    @patch('apps.news.services.fetch_json',return_value={'current':{'temperature_2m':27,'weather_code':0,'wind_speed_10m':8,'time':'2026-10-18T05:00'}})
    def test_weather_timestamp_cache_and_coordinates(self,fetch):
        self.assertTrue(services.weather(17,78)['time'].endswith('Z'))
        services.weather(17,78);self.assertEqual(fetch.call_count,1)
        for lat,lon in [('nan',78),(91,78),(17,181)]:
            with self.assertRaises(ValueError):services.weather(lat,lon)
    def test_translation_csrf_and_private_path_rejection(self):
        strict=Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post('/api/translate/',data='{}',content_type='application/json').status_code,403)
        from .api import translation_payload
        for path in ['https://elsewhere.example/','/admin/','/api/weather/']:
            with self.assertRaises(ValueError):translation_payload(path)
        post=Article.objects.first();post.status='draft';post.save()
        self.assertNotIn(f'article:{post.pk}:title',translation_payload('/'))
    @patch('apps.news.services.translate_texts',side_effect=lambda texts,target:['Translated '+t for t in texts])
    def test_translation_bounded_server_corpus(self,translate):
        r=self.client.post('/api/translate/',data=json.dumps({'path':'/','language':'hi','texts':['UNTRUSTED CLIENT TEXT']}),content_type='application/json')
        self.assertEqual(r.status_code,200);self.assertIn('ui:home',r.json()['texts'])
        self.assertNotIn('UNTRUSTED CLIENT TEXT',translate.call_args.args[0])
        self.assertEqual(self.client.post('/api/translate/',data='{}',content_type='application/json').status_code,429)
    @override_settings(TRANSLATION_PROVIDER='google',TRANSLATION_API_KEY='test-only-placeholder')
    @patch('apps.news.services.fetch_json')
    def test_google_language_adapter(self,fetch):
        fetch.return_value={'data':{'languages':[{'language':'en','name':'English'},{'language':'hi','name':'Hindi'}]}}
        self.assertEqual(services.supported_languages()[1]['code'],'hi')
        fetch.return_value={'data':{'translations':[{'translatedText':'नमस्ते'}]}}
        self.assertEqual(services.translate_texts(['Hello'],'hi'),['नमस्ते'])
    @override_settings(TRANSLATION_PROVIDER='libre',LIBRETRANSLATE_URL='https://translate.example',TRANSLATION_API_KEY='')
    @patch('apps.news.services.fetch_json')
    def test_libre_language_pairs(self,fetch):
        fetch.return_value=[{'code':'en','name':'English','targets':['en','hi']},{'code':'hi','name':'Hindi'},{'code':'xx','name':'Unsupported'}]
        self.assertEqual([x['code'] for x in services.supported_languages()],['en','hi'])
        fetch.return_value={'translatedText':['नमस्ते']}
        self.assertEqual(services.translate_texts(['Hello'],'hi'),['नमस्ते'])
    @patch('apps.news.network.socket.getaddrinfo')
    def test_private_dns_and_unsafe_schemes_blocked(self,dns):
        dns.return_value=[(2,1,6,'',('127.0.0.1',443))]
        with self.assertRaises(ValueError):network.validate_url('https://feed.example/rss')
        with self.assertRaises(ValueError):network.pinned_connection(('feed.example',443))
        for path in ['http://feed.example/','https://user:secret@feed.example/','https://feed.example:8000/']:
            with self.assertRaises(ValueError):network.validate_url(path)
