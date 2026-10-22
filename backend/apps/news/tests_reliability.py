"""Backend reliability regressions. All news/translation provider calls are mocked."""
import io
from datetime import timedelta
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from django.core.management import call_command, CommandError
from django.core.cache import cache
from django.test import TestCase, SimpleTestCase, override_settings, RequestFactory
from django.utils import timezone
from django.contrib import admin
from .models import Article, Category, FetchRun, NewsSource
from .ingestion import ingest, RSSAdapter, NewsAPIAdapter
from .tests_newsapi import article
from . import services
from .translation_network import fetch_local_json

RSS = b'<rss version="2.0"><channel><title>Audit</title><item><title>Real fixture title</title><link>https://publisher.example/item</link><pubDate>Sun, 18 Oct 2026 05:00:00 GMT</pubDate></item></channel></rss>'


@override_settings(NEWS_FETCH_ENABLED=True, NEWS_API_KEY='test-placeholder', NEWS_API_MAX_PAGES=1)
class FetchReliabilityTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='World',slug='world')
        self.source = NewsSource.objects.create(name='Test',adapter='newsapi',feed_url='https://newsapi.org/v2/everything?q=test',default_category=self.category,enabled=True,rights_confirmed=True)

    @override_settings(NEWS_FETCH_ENABLED=False)
    @patch('apps.news.network.fetch_json')
    def test_service_global_disable_records_blocked_without_network(self, fetch):
        with self.assertRaisesRegex(ValueError,'disabled'): ingest(self.source)
        fetch.assert_not_called()
        self.assertEqual(FetchRun.objects.get().state,'blocked')
        self.source.refresh_from_db(); self.assertIsNone(self.source.last_attempt_at)

    @override_settings(NEWS_FETCH_ENABLED=False)
    def test_disabled_dry_run_is_completely_nonwriting(self):
        with self.assertRaises(ValueError): ingest(self.source,dry_run=True)
        self.assertFalse(FetchRun.objects.exists())

    def test_inactive_source_command_records_blocked(self):
        self.source.enabled=False; self.source.save()
        with self.assertRaises(CommandError): call_command('fetch_news',source=self.source.pk,stdout=io.StringIO(),stderr=io.StringIO())
        self.assertEqual(FetchRun.objects.get().state,'blocked')

    def test_no_eligible_source_is_not_silent_success(self):
        NewsSource.objects.update(enabled=False)
        with self.assertRaisesRegex(CommandError,'No eligible'): call_command('fetch_news')
        self.assertFalse(FetchRun.objects.exists())

    def test_unknown_source_is_not_success(self):
        with self.assertRaisesRegex(CommandError,'No source exists'): call_command('fetch_news',source=98765)

    @override_settings(NEWS_API_KEY='')
    def test_missing_key_records_safe_failure(self):
        with self.assertRaisesRegex(ValueError,'NEWS_API_KEY'): ingest(self.source)
        run=FetchRun.objects.get(); self.assertEqual(run.state,'failed'); self.assertEqual(run.imported,0)

    @patch('apps.news.network.fetch_json')
    def test_provider_errors_record_once_and_redact(self, fetch):
        for status in [401,403,429]:
            with self.subTest(status=status):
                self.source.next_fetch_at=None;self.source.save(update_fields=['next_fetch_at'])
                before=FetchRun.objects.count()
                fetch.side_effect=HTTPError('https://example.invalid/secret',status,'secret-raw-body',{},None)
                with self.assertRaises(ValueError):ingest(self.source)
                run=FetchRun.objects.first()
                self.assertEqual(FetchRun.objects.count(),before+1)
                self.assertEqual(run.state,'failed');self.assertNotIn('secret',run.error);self.assertEqual(run.imported,0)

    @patch('apps.news.network.fetch_json')
    def test_same_batch_duplicates_and_rejections_reported(self, fetch):
        fetch.return_value={'status':'ok','totalResults':4,'articles':[article(),article(),None,{'title':42,'url':'https://publisher.example/invalid'}]}
        self.assertEqual(ingest(self.source),{'imported':1,'skipped':1})
        r=FetchRun.objects.get()
        self.assertEqual((r.fetched,r.parsed,r.rejected,r.duplicates,r.imported,r.published),(4,2,2,1,1,0))
        self.assertEqual(r.state,'success')

    @patch('apps.news.network.fetch_json')
    def test_rollback_counters_and_single_failure_run(self, fetch):
        fetch.return_value={'status':'ok','totalResults':2,'articles':[article(1),article(2)]}
        create=Article.objects.create;count=0
        def fail(**kwargs):
            nonlocal count
            count+=1
            if count==2:raise RuntimeError('sensitive database detail')
            return create(**kwargs)
        with patch.object(Article.objects,'create',side_effect=fail):
            with self.assertRaises(ValueError):ingest(self.source)
        r=FetchRun.objects.get()
        self.assertEqual((r.state,r.imported,r.published),('failed',0,0))
        self.assertEqual(r.fetched,2); self.assertFalse(Article.objects.exists())
        self.source.refresh_from_db();self.assertIsNone(self.source.last_success_at)

    @patch('apps.news.network.fetch_json')
    def test_future_date_not_auto_published(self, fetch):
        self.source.auto_publish=True;self.source.trusted=True;self.source.save()
        row=article();row['publishedAt']=(timezone.now()+timedelta(days=1)).isoformat()
        fetch.return_value={'status':'ok','articles':[row]}
        ingest(self.source);self.assertEqual(Article.objects.get().status,'draft')
        self.assertEqual(FetchRun.objects.get().published,0)

    def test_deferred_run_no_network_and_no_success(self):
        self.source.next_fetch_at=timezone.now()+timedelta(hours=1);self.source.save()
        with patch('apps.news.network.fetch_json') as fetch:
            self.assertTrue(ingest(self.source)['deferred']);fetch.assert_not_called()
        self.assertEqual(FetchRun.objects.get().state,'deferred')
        self.assertFalse(FetchRun.objects.get().success)

    @override_settings(NEWS_API_KEY='')
    @patch('apps.news.ingestion.fetch_bytes',return_value=RSS)
    def test_rss_does_not_need_newsapi_key(self, fetch):
        self.source.adapter='rss';self.source.feed_url='https://feeds.bbci.co.uk/news/world/rss.xml';self.source.save()
        result=ingest(self.source,dry_run=True)
        self.assertEqual(result['would_import'],1);self.assertEqual(fetch.call_count,1)
        self.assertFalse(FetchRun.objects.exists());self.assertFalse(Article.objects.exists())
        self.source.refresh_from_db();self.assertIsNone(self.source.last_attempt_at)

    def test_wrong_adapter_and_bad_query_rejected_before_network(self):
        self.source.feed_url='https://feeds.bbci.co.uk/news/world/rss.xml'
        with patch('apps.news.network.fetch_json') as fetch:
            with self.assertRaises(ValueError):NewsAPIAdapter().fetch(self.source)
            self.source.feed_url='https://newsapi.org/v2/everything'
            with self.assertRaisesRegex(ValueError,'selector'):NewsAPIAdapter().fetch(self.source)
            fetch.assert_not_called()

    def test_html_is_not_a_successful_empty_feed(self):
        with self.assertRaisesRegex(ValueError,'RSS or Atom'):RSSAdapter().parse(b'<html><body>Access denied</body></html>')

    def test_admin_has_explicit_permission_gated_action(self):
        action=admin.site._registry[NewsSource].fetch_selected_sources
        self.assertEqual(action.allowed_permissions,['change'])


LANGUAGES=[{'code':'en','name':'English','targets':['en','hi','bn','ur']},{'code':'hi','name':'Hindi'},{'code':'bn','name':'Bengali'},{'code':'ur','name':'Urdu'},{'code':'ta','name':'Tamil'}]

@override_settings(TRANSLATION_PROVIDER='libre',LIBRETRANSLATE_URL='http://127.0.0.1:5000',TRANSLATION_API_KEY='')
class TranslationReliabilityTests(SimpleTestCase):
    def setUp(self):cache.clear()

    @patch('apps.news.translation_network.fetch_local_json')
    def test_english_pairs_and_no_unsupported_language_claim(self, fetch):
        fetch.return_value=LANGUAGES
        self.assertEqual([r['code'] for r in services.supported_languages()],['en','hi','bn','ur'])
        with self.assertRaisesRegex(ValueError,'not supported'):services.translate_texts(['Hello'],'ta')

    @patch('apps.news.translation_network.fetch_local_json')
    def test_three_languages_mocked_and_cached(self, fetch):
        values={'hi':'नमस्ते','bn':'হ্যালো','ur':'سلام'}
        def respond(base,path,data=None,**kw):return LANGUAGES if path=='/languages' else {'translatedText':[values[data['target']]]}
        fetch.side_effect=respond
        for code,text in values.items():
            with self.subTest(language=code):
                self.assertEqual(services.translate_texts(['Hello'],code),[text])
                before=fetch.call_count;self.assertEqual(services.translate_texts(['Hello'],code),[text]);self.assertEqual(fetch.call_count,before)
        for call in fetch.call_args_list:
            if len(call.args)>2 and call.args[2] is not None:self.assertNotIn('api_key',call.args[2])

    @patch('apps.news.translation_network.fetch_local_json')
    def test_endpoint_switch_invalidates_capabilities(self, fetch):
        fetch.return_value=LANGUAGES;services.supported_languages()
        with override_settings(LIBRETRANSLATE_URL='http://127.0.0.1:5001'):services.supported_languages()
        self.assertEqual(fetch.call_count,2)

    @patch('apps.news.translation_network.fetch_local_json')
    def test_outage_and_timeout_safe(self, fetch):
        for exc in [TimeoutError('private-token'),OSError('private-token')]:
            cache.clear();fetch.side_effect=exc
            with self.assertRaisesRegex(ValueError,'provider unavailable') as got:services.supported_languages()
            self.assertNotIn('private-token',str(got.exception))

    @patch('apps.news.translation_network.fetch_local_json')
    def test_malformed_languages(self, fetch):
        for value in [{},[{'code':1,'name':'Bad'}],[{'code':'en','name':'English','targets':'hi'}]]:
            cache.clear();fetch.return_value=value
            with self.assertRaises(ValueError):services.supported_languages()

    @patch('apps.news.translation_network.fetch_local_json')
    def test_malformed_translation_not_cached(self, fetch):
        def respond(base,path,data=None,**kw):return LANGUAGES if path=='/languages' else {'translatedText':[123]}
        fetch.side_effect=respond
        for _ in range(2):
            with self.assertRaisesRegex(ValueError,'Invalid translation'):services.translate_texts(['Hello'],'hi')
        self.assertEqual(fetch.call_count,3)  # capabilities cached, bad translations retried

    @patch('apps.news.translation_network.fetch_local_json')
    def test_input_limits_and_english_passthrough(self, fetch):
        self.assertEqual(services.translate_texts(['Hello'],'en'),['Hello']);fetch.assert_not_called()
        for value in ['Hello',[42],['x'*5001],['x']*257]:
            with self.assertRaises(ValueError):services.translate_texts(value,'hi')
        fetch.assert_not_called()

    @patch('apps.news.translation_network.HTTPConnection')
    def test_loopback_only_no_private_lan_or_credentials(self, connection):
        for base in ['http://192.168.1.2:5000','http://evil.example:5000','http://user:password@127.0.0.1:5000','http://127.0.0.1:5000?key=secret']:
            with self.assertRaises(ValueError):fetch_local_json(base,'/languages')
        connection.assert_not_called()

    @patch('apps.news.translation_network.HTTPConnection')
    def test_redirect_is_not_followed_and_body_is_bounded(self, connection):
        response=connection.return_value.getresponse.return_value
        response.status=302
        with self.assertRaises(ValueError):fetch_local_json('http://127.0.0.1:5000','/languages')
        response.status=200;response.read.return_value=b' ' * 11
        with self.assertRaises(ValueError):fetch_local_json('http://127.0.0.1:5000','/languages',max_bytes=10)

    @patch('apps.news.translation_network.HTTPConnection')
    def test_local_post_no_proxies_no_dns_no_key(self, connection):
        response=connection.return_value.getresponse.return_value;response.status=200;response.read.return_value=b'{"translatedText":["hello"]}'
        self.assertEqual(fetch_local_json('http://localhost:5000','/translate',{'q':['Hello']}),{'translatedText':['hello']})
        connection.assert_called_once_with('127.0.0.1',5000,timeout=15)
        self.assertEqual(connection.return_value.request.call_args.args[0],'POST')

@override_settings(NEWS_FETCH_ENABLED=True, NEWS_API_KEY='test-placeholder', NEWS_API_MAX_PAGES=1)
class CommandAndDiagnosticsTests(TestCase):
    def setUp(self):
        cat=Category.objects.create(name='World',slug='world')
        self.source=NewsSource.objects.create(name='Test',adapter='newsapi',feed_url='https://newsapi.org/v2/everything?q=test',default_category=cat,enabled=True,rights_confirmed=True)

    @patch('apps.news.network.fetch_json',return_value={'status':'ok','articles':[article()]})
    def test_command_dry_run_all_model_state_unchanged(self, fetch):
        from django.contrib.auth import get_user_model
        before=list(NewsSource.objects.values());users=get_user_model().objects.count()
        out=io.StringIO();call_command('fetch_news',source=self.source.pk,dry_run=True,stdout=out)
        self.assertIn('would_import',out.getvalue())
        self.assertEqual(before,list(NewsSource.objects.values()))
        self.assertFalse(Article.objects.exists());self.assertFalse(FetchRun.objects.exists())
        self.assertEqual(get_user_model().objects.count(),users)

    def test_status_never_prints_key_or_query_values(self):
        self.source.feed_url='https://newsapi.org/v2/everything?q=private-query&apiKey=private-url-key';self.source.save()
        out=io.StringIO();call_command('backend_status',sources=True,stdout=out)
        self.assertNotIn('test-placeholder',out.getvalue());self.assertNotIn('private-query',out.getvalue());self.assertNotIn('private-url-key',out.getvalue())
        self.assertIn('"NEWS_API_KEY_present": true',out.getvalue())

    @patch('apps.news.ingestion.fetch_bytes')
    def test_rss_401_403_429_and_timeout_records(self, fetch):
        self.source.adapter='rss';self.source.feed_url='https://publisher.example/rss';self.source.save()
        for failure in [HTTPError('https://publisher.example/rss',401,'secret',{},None),HTTPError('https://publisher.example/rss',403,'secret',{},None),HTTPError('https://publisher.example/rss',429,'secret',{},None),TimeoutError('secret')]:
            self.source.next_fetch_at=None;self.source.save(update_fields=['next_fetch_at']);fetch.side_effect=failure
            with self.assertRaises(ValueError):ingest(self.source)
            r=FetchRun.objects.first();self.assertEqual(r.state,'failed');self.assertNotIn('secret',r.error)

    @patch('apps.news.network.fetch_json',return_value={'status':'ok','articles':[]})
    def test_running_record_exists_during_network(self, fetch):
        def response(*args,**kwargs):
            self.assertEqual(FetchRun.objects.get().state,'running')
            return {'status':'ok','articles':[]}
        fetch.side_effect=response;ingest(self.source)
        self.assertEqual(FetchRun.objects.get().state,'success')

    @override_settings(TRANSLATION_PROVIDER='libre')
    @patch('apps.news.services.translate_texts',side_effect=lambda texts,target:texts)
    def test_translation_endpoint_no_session_writes_and_limits(self, translate):
        from django.contrib.sessions.models import Session
        from django.core.cache import cache
        cache.clear()
        r=self.client.post('/api/translate/',data='{"path":"/","language":"hi"}',content_type='application/json')
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['source'],'en')
        self.assertFalse(Session.objects.exists())
        self.assertEqual(self.client.post('/api/translate/',data='{}',content_type='application/json').status_code,429)

class LoopbackHTTPFixtureTests(SimpleTestCase):
    def test_real_loopback_transport_against_fixture_not_libretranslate(self):
        import threading,json
        from http.server import HTTPServer,BaseHTTPRequestHandler
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(LANGUAGES).encode())
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'translatedText':['fixture:'+x for x in data['q']]}).encode())
        server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with override_settings(TRANSLATION_PROVIDER='libre',LIBRETRANSLATE_URL=f'http://127.0.0.1:{server.server_port}',TRANSLATION_API_KEY=''):
                cache.clear();self.assertEqual(services.translate_texts(['Hello'],'hi'),['fixture:Hello'])
        finally:
            server.shutdown();server.server_close();thread.join(timeout=2)

class ArticleValidationBoundaryTests(SimpleTestCase):
    def test_overlong_story_url_is_rejected_before_database(self):
        from .ingestion import normalize_url
        with self.assertRaisesRegex(ValueError,'supported length'):normalize_url('https://publisher.example/'+'a'*1001)

    @override_settings(NEWS_API_KEY='test-placeholder',NEWS_API_MAX_PAGES=1)
    @patch('apps.news.network.fetch_json',return_value={'status':'ok','articles':[article()]*101})
    def test_newsapi_response_cannot_exceed_page_bound(self, fetch):
        from types import SimpleNamespace
        with self.assertRaisesRegex(ValueError,'response shape'):NewsAPIAdapter().fetch(SimpleNamespace(feed_url='https://newsapi.org/v2/everything?q=test'))
