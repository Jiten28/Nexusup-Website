"""Category visibility, candidate sources, image backfill and the translation corpus.

Real (migrated, throwaway) test database; the only mocked call is the feed download.
"""
import hashlib
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from .models import Article, Category, NewsSource

FEED = b'''<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>T</title>
<item><title>Backfill story</title><link>https://publisher.example/story</link><description>Summary</description>
<pubDate>Sun, 18 Oct 2026 05:00:00 GMT</pubDate>
<media:thumbnail url="https://images.example/a.jpg" width="240" height="135"/></item></channel></rss>'''
STORY_HASH = hashlib.sha256(b'https://publisher.example/story').hexdigest()


@override_settings(DEBUG=True, NEWS_FETCH_ENABLED=True)
class CoverageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        call_command('configure_sources', verbosity=0)

    def real(self, slug, **extra):
        sample = Article.objects.filter(is_sample=True).first()
        values = dict(title=f'Real {slug} story', slug=f'real-{slug}-{Article.objects.count()}',
                      category=Category.objects.get(slug=slug), author=sample.author, excerpt='Summary',
                      body='Body', is_sample=False, status='published',
                      published_at=timezone.now() - timedelta(hours=1))
        values.update(extra)
        return Article.objects.create(**values)

    def test_category_counts_reflect_what_the_public_site_shows(self):
        self.real('technology')
        self.real('technology', status='draft', slug='draft-technology')
        counts = {c['slug']: c['article_count'] for c in self.client.get('/api/categories/').json()}
        self.assertEqual(counts['technology'], 1)  # drafts are not counted
        self.assertEqual(counts['cricket'], 0)     # samples are hidden once real news exists
        self.assertEqual(self.client.get('/api/articles/', {'category': 'cricket'}).json()['count'], 0)

    def test_new_candidate_sources_are_disabled_and_unapproved(self):
        before = NewsSource.objects.count()
        call_command('configure_sources', verbosity=0)
        self.assertEqual(before, NewsSource.objects.count())  # idempotent
        self.assertGreaterEqual(before, 10)
        for source in NewsSource.objects.all():
            self.assertFalse(source.enabled)
            self.assertFalse(source.rights_confirmed)
            self.assertFalse(source.auto_publish)
            self.assertFalse(source.allow_images)

    def _source_and_article(self, **source_flags):
        source = NewsSource.objects.create(name='Fixture publisher', feed_url='https://publisher.example/rss',
                                           default_category=Category.objects.get(slug='world'),
                                           enabled=True, rights_confirmed=True, **source_flags)
        article = self.real('world', source=source, source_url_hash=STORY_HASH,
                            canonical_source_url='https://publisher.example/story')
        return source, article

    @patch('apps.news.management.commands.backfill_images.fetch_bytes', return_value=FEED)
    def test_backfill_is_dry_run_by_default_and_respects_policy(self, fetch):
        source, article = self._source_and_article(allow_images=True, image_hosts=['images.example'])
        out = StringIO()
        call_command('backfill_images', source=source.pk, stdout=out)
        article.refresh_from_db()
        self.assertEqual(article.remote_image_url, '')
        self.assertIn('DRY RUN', out.getvalue())
        call_command('backfill_images', source=source.pk, apply=True, stdout=StringIO())
        article.refresh_from_db(); source.refresh_from_db()
        self.assertEqual(article.remote_image_url, 'https://images.example/a.jpg')
        self.assertEqual(article.image_credit, 'Fixture publisher')
        self.assertTrue(source.allow_images)  # permissions untouched
        # An image that is already set is never overwritten.
        Article.objects.filter(pk=article.pk).update(remote_image_url='https://images.example/keep.jpg')
        call_command('backfill_images', source=source.pk, apply=True, stdout=StringIO())
        article.refresh_from_db()
        self.assertEqual(article.remote_image_url, 'https://images.example/keep.jpg')

    @patch('apps.news.management.commands.backfill_images.fetch_bytes', return_value=FEED)
    def test_backfill_writes_nothing_when_images_are_not_permitted(self, fetch):
        source, article = self._source_and_article()  # allow_images False, no hosts
        out = StringIO()
        call_command('backfill_images', source=source.pk, apply=True, stdout=out)
        article.refresh_from_db()
        self.assertEqual(article.remote_image_url, '')
        self.assertIn('source_allow_images_is_off', out.getvalue())

    def test_translation_corpus_contains_every_ui_string(self):
        from .api import translation_payload
        from .ui_strings import UI_STRINGS
        payload = translation_payload('/')
        for key, text in UI_STRINGS.items():
            self.assertEqual(payload[key], text)

    def test_news_report_is_read_only_and_never_prints_the_key(self):
        before = Article.objects.count()
        with override_settings(NEWS_API_KEY='super-secret-test-key'):
            out = StringIO()
            call_command('news_report', stdout=out)
        self.assertNotIn('super-secret-test-key', out.getvalue())
        self.assertIn('READ ONLY', out.getvalue())
        self.assertEqual(before, Article.objects.count())
