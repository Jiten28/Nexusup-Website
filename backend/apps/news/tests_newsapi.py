"""Deterministic NewsAPI/configuration regression tests; no live HTTP calls."""
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings

from config.environment import load_project_environment
from .ingestion import ingest, NewsAPIAdapter, NewsAPIError
from .models import Article, Category, FetchRun, NewsSource


def article(number=1, title=None):
    return {
        'title': title or f'Provider report {number}',
        'url': f'https://publisher.example/reports/{number}?utm_source=newsapi',
        'description': 'Attributed summary',
        'publishedAt': '2026-10-18T05:00:00Z',
        'urlToImage': 'https://images.example/report.jpg',
        'source': {'name': 'Example Publisher'},
    }


@override_settings(NEWS_FETCH_ENABLED=True, NEWS_API_KEY='test-secret-key', NEWS_API_MAX_PAGES=1)
class NewsAPIIngestionTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='World', slug='world')
        self.source = NewsSource.objects.create(
            name='NewsAPI QA',
            feed_url='https://newsapi.org/v2/everything?q=india',
            adapter='newsapi',
            enabled=True,
            rights_confirmed=True,
            default_category=category,
        )

    def ready(self):
        NewsSource.objects.filter(pk=self.source.pk).update(next_fetch_at=None)
        self.source.refresh_from_db()

    @override_settings(NEWS_API_KEY='')
    def test_missing_api_key_has_clear_safe_diagnostic(self):
        with self.assertRaisesRegex(NewsAPIError, 'NEWS_API_KEY'):
            NewsAPIAdapter().fetch(self.source)

    def test_valid_response_writes_attributed_dated_article_once(self):
        payload = {'status': 'ok', 'totalResults': 1, 'articles': [article()]}
        with patch('apps.news.network.fetch_json', return_value=payload) as fetch:
            self.assertEqual(ingest(self.source), {'imported': 1, 'skipped': 0})
        endpoint = fetch.call_args.args[0]
        self.assertNotIn('test-secret-key', endpoint)
        self.assertEqual(fetch.call_args.kwargs['headers'], {'X-Api-Key': 'test-secret-key'})
        saved = Article.objects.get(source=self.source)
        self.assertEqual(saved.publisher_name, 'Example Publisher')
        self.assertEqual(saved.canonical_source_url, 'https://publisher.example/reports/1')
        self.assertIsNotNone(saved.source_published_at)
        self.assertEqual(saved.status, 'draft')
        self.ready()
        with patch('apps.news.network.fetch_json', return_value=payload):
            self.assertEqual(ingest(self.source), {'imported': 0, 'skipped': 1})
        self.assertEqual(Article.objects.filter(source=self.source).count(), 1)

    def test_invalid_credentials_401_and_403(self):
        for status in (401, 403):
            self.ready()
            error = HTTPError('https://newsapi.org/v2/everything', status, 'denied', {}, None)
            with self.subTest(status=status), patch('apps.news.network.fetch_json', side_effect=error):
                with self.assertRaisesRegex(ValueError, 'rejected the configured credentials'):
                    ingest(self.source, dry_run=True)

    def test_rate_limit_429(self):
        error = HTTPError('https://newsapi.org/v2/everything', 429, 'limited', {}, None)
        with patch('apps.news.network.fetch_json', side_effect=error):
            with self.assertRaisesRegex(ValueError, 'rate limit'):
                ingest(self.source, dry_run=True)

    def test_timeout_and_provider_outage(self):
        for failure in (TimeoutError(), URLError('offline')):
            with self.subTest(failure=type(failure).__name__), patch('apps.news.network.fetch_json', side_effect=failure):
                with self.assertRaisesRegex(ValueError, 'timed out|unavailable'):
                    ingest(self.source, dry_run=True)

    def test_invalid_json_and_unexpected_shape(self):
        failures = [
            json.JSONDecodeError('bad', 'x', 0),
            {'status': 'ok', 'articles': 'not-a-list'},
            {'status': 'error', 'articles': []},
        ]
        for failure in failures:
            effect = failure if isinstance(failure, Exception) else None
            with self.subTest(failure=repr(failure)), patch(
                'apps.news.network.fetch_json',
                side_effect=effect,
                return_value=None if effect else failure,
            ):
                with self.assertRaisesRegex(ValueError, 'invalid JSON|unexpected response shape'):
                    ingest(self.source, dry_run=True)

    def test_empty_response_records_success_without_articles(self):
        with patch('apps.news.network.fetch_json', return_value={'status': 'ok', 'totalResults': 0, 'articles': []}):
            self.assertEqual(ingest(self.source), {'imported': 0, 'skipped': 0})
        self.assertFalse(Article.objects.filter(source=self.source).exists())
        self.assertTrue(FetchRun.objects.get(source=self.source).success)

    def test_malformed_articles_are_skipped(self):
        rows = [None, {}, {'title': '[Removed]', 'url': 'https://publisher.example/removed'}]
        with patch('apps.news.network.fetch_json', return_value={'status': 'ok', 'totalResults': 3, 'articles': rows}):
            self.assertEqual(ingest(self.source), {'imported': 0, 'skipped': 0})

    def test_dry_run_reports_plan_and_makes_no_database_changes(self):
        payload = {'status': 'ok', 'totalResults': 1, 'articles': [article()]}
        before = {
            'articles': Article.objects.count(),
            'runs': FetchRun.objects.count(),
            'users': get_user_model().objects.count(),
            'attempt': self.source.last_attempt_at,
        }
        with patch('apps.news.network.fetch_json', return_value=payload):
            result = ingest(self.source, dry_run=True)
        self.assertEqual(result, {'eligible': 1, 'would_import': 1, 'imported': 0, 'skipped': 0, 'dry_run': True})
        self.source.refresh_from_db()
        self.assertEqual(before, {
            'articles': Article.objects.count(),
            'runs': FetchRun.objects.count(),
            'users': get_user_model().objects.count(),
            'attempt': self.source.last_attempt_at,
        })

    def test_unexpected_mid_batch_failure_rolls_back_entire_article_batch(self):
        payload = {'status': 'ok', 'totalResults': 2, 'articles': [article(1), article(2)]}
        create = Article.objects.create
        calls = 0

        def fail_second(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError('database write interrupted')
            return create(**kwargs)

        with patch('apps.news.network.fetch_json', return_value=payload), patch.object(
            Article.objects, 'create', side_effect=fail_second
        ):
            with self.assertRaisesRegex(ValueError, 'fetch/parse failed'):
                ingest(self.source)
        self.assertFalse(Article.objects.filter(source=self.source).exists())
        self.assertFalse(get_user_model().objects.filter(username='news-feed-editor').exists())
        run = FetchRun.objects.get(source=self.source)
        self.assertFalse(run.success)
        self.assertNotIn('database write interrupted', run.error)

    def test_secret_redacted_from_stored_error_command_and_log(self):
        error = HTTPError('https://newsapi.org/v2/everything', 401, 'test-secret-key', {}, None)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch('apps.news.network.fetch_json', side_effect=error), self.assertLogs('apps.news.ingestion', 'WARNING') as logs:
            with self.assertRaises(CommandError):
                call_command('fetch_news', source=self.source.pk, stdout=stdout, stderr=stderr)
        self.source.refresh_from_db()
        combined = self.source.last_error + stdout.getvalue() + stderr.getvalue() + ''.join(logs.output)
        self.assertNotIn('test-secret-key', combined)
        self.assertNotIn('X-Api-Key', combined)
        self.assertIn('rejected the configured credentials', combined)

    @override_settings(NEWS_API_MAX_PAGES=2)
    def test_bounded_pagination(self):
        first = {'status': 'ok', 'totalResults': 101, 'articles': [article(i) for i in range(1, 101)]}
        second = {'status': 'ok', 'totalResults': 101, 'articles': [article(101)]}
        with patch('apps.news.network.fetch_json', side_effect=[first, second]) as fetch:
            rows = NewsAPIAdapter().fetch(self.source)
        self.assertEqual(len(rows), 101)
        self.assertEqual(fetch.call_count, 2)
        self.assertIn('page=1', fetch.call_args_list[0].args[0])
        self.assertIn('page=2', fetch.call_args_list[1].args[0])


class EnvironmentLoadingTests(TestCase):
    def test_dotenv_loads_in_development_without_overriding_process(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text('NEWS_API_KEY=file-value\nNEWS_FETCH_ENABLED=1\n')
            with patch.dict(os.environ, {'NEWS_API_KEY': 'process-value'}, clear=False):
                os.environ.pop('NEWS_FETCH_ENABLED', None)
                load_project_environment(path)
                self.assertEqual(os.environ['NEWS_API_KEY'], 'process-value')
                self.assertEqual(os.environ['NEWS_FETCH_ENABLED'], '1')
                os.environ.pop('NEWS_FETCH_ENABLED', None)

    def test_dotenv_loading_is_not_tied_to_debug_mode(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text('DOTENV_PRODUCTION_PROBE=loaded\n')
            with patch.dict(os.environ, {'DJANGO_DEBUG': '0'}, clear=False):
                os.environ.pop('DOTENV_PRODUCTION_PROBE', None)
                load_project_environment(path)
                self.assertEqual(os.environ['DOTENV_PRODUCTION_PROBE'], 'loaded')
                os.environ.pop('DOTENV_PRODUCTION_PROBE', None)


class FetchDisabledTests(TestCase):
    @override_settings(NEWS_FETCH_ENABLED=False)
    def test_command_refuses_when_fetching_disabled(self):
        with self.assertRaisesRegex(CommandError, 'News fetching is disabled'):
            call_command('fetch_news')