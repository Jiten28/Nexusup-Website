"""Canonical routing and real-news discovery regressions; isolated test database only."""
from django.core.management import call_command
from django.test import TestCase, SimpleTestCase, override_settings
from django.utils import timezone
from .models import Article, NewsSource, Category


@override_settings(DEBUG=True, PUBLIC_FRONTEND_MODE='react', FRONTEND_URL='http://localhost:5173')
class FrontendEntryTests(SimpleTestCase):
    def test_public_routes_keep_path_query_and_use_configured_origin(self):
        for path in ('/', '/stories/', '/search/', '/category/world/', '/story/a-story/', '/contact/', '/sources/', '/about/', '/privacy/', '/terms/'):
            with self.subTest(path=path):
                response=self.client.get(path, {'q':'a & b'})
                self.assertEqual(response.status_code,302)
                self.assertEqual(response['Location'],'http://localhost:5173'+path+'?q=a+%26+b')
                self.assertEqual(response['Cache-Control'],'no-store')
    @override_settings(FRONTEND_URL='http://testserver')
    def test_same_origin_fails_closed_without_redirect_loop_or_demo(self):
        response=self.client.get('/')
        self.assertEqual(response.status_code,503)
        self.assertNotIn('Location',response)
        self.assertNotContains(response,'LOCAL REDESIGN DEMO',status_code=503)
    @override_settings(FRONTEND_URL='https://public.example')
    def test_deployment_uses_configured_origin_not_development_address(self):
        self.assertEqual(self.client.get('/story/a/')['Location'],'https://public.example/story/a/')
    def test_backend_routes_are_not_redirected_to_react(self):
        self.assertEqual(self.client.get('/health/live/').status_code,200)
        self.assertEqual(self.client.get('/admin/').url,'/admin/login/?next=/admin/')
        self.assertEqual(self.client.get('/api/not-a-route/').status_code,404)


@override_settings(DEBUG=True)
class NewsDiscoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo',verbosity=0)
    def real_article(self,**kwargs):
        sample=Article.objects.first()
        values=dict(title='Independent real news regression fixture',slug='real-regression',category=sample.category,author=sample.author,excerpt='Provider summary',body='Metadata, not a full article.',is_sample=False,status='published',published_at=timezone.now(),canonical_source_url='https://publisher.example/report')
        values.update(kwargs)
        return Article.objects.create(**values)
    def test_real_news_replaces_samples_in_discovery_without_modifying_them(self):
        sample_ids=set(Article.objects.values_list('id',flat=True))
        real=self.real_article()
        listing=self.client.get('/api/articles/').json()
        self.assertEqual(listing['count'],1)
        self.assertEqual([a['id'] for a in listing['results']],[real.id])
        home=self.client.get('/api/home/').json()
        self.assertEqual({a['id'] for a in home['featured']+home['carousel']},{real.id})
        self.assertEqual(set(Article.objects.filter(is_sample=True).values_list('id',flat=True)),sample_ids)
        sample=Article.objects.filter(is_sample=True).first()
        self.assertEqual(self.client.get(f'/api/articles/{sample.slug}/').status_code,200)
        self.assertEqual(self.client.get('/api/articles/',{'q':sample.title}).json()['count'],0)
    def test_draft_or_future_real_article_does_not_hide_labeled_samples(self):
        from datetime import timedelta
        self.real_article(status='draft')
        self.real_article(slug='future-regression',published_at=timezone.now()+timedelta(days=1))
        results=self.client.get('/api/articles/').json()['results']
        self.assertTrue(results)
        self.assertTrue(all(a['is_sample'] for a in results))
    def test_imported_metadata_keeps_image_attribution_and_dates(self):
        source=NewsSource.objects.create(name='Approved fixture publisher',feed_url='https://publisher.example/rss',default_category=Category.objects.first())
        article=self.real_article(source=source,remote_image_url='https://images.publisher.example/a.jpg',image_credit='Publisher permission fixture',source_published_at=timezone.now())
        data=self.client.get(f'/api/articles/{article.slug}/').json()
        self.assertEqual(data['content_kind'],'feed_summary')
        self.assertEqual(data['image'],article.remote_image_url)
        self.assertEqual(data['canonical_source_url'],article.canonical_source_url)
        self.assertEqual(data['source_name'],source.name)
        self.assertEqual(data['image_credit'],article.image_credit)
        self.assertIsNotNone(data['date'])
        article.remote_image_url='';article.save()
        self.assertEqual(self.client.get(f'/api/articles/{article.slug}/').json()['image'],'')
    def test_related_does_not_mix_sample_and_real_stories(self):
        first=self.real_article();other=self.real_article(slug='real-second')
        data=self.client.get(f'/api/articles/{first.slug}/related/').json()['results']
        self.assertEqual([a['id'] for a in data],[other.id])

    def test_admin_source_controls_and_fetch_history_on_migrated_test_database(self):
        from django.contrib.auth import get_user_model
        from .models import FetchRun
        user=get_user_model().objects.create_superuser(username='qa-admin',password=None)
        self.client.force_login(user)
        source=NewsSource.objects.create(name='QA admin source',feed_url='https://publisher.example/rss',default_category=Category.objects.first())
        FetchRun.objects.create(source=source,state='failed',error='QA failure fixture',success=False)
        response=self.client.get('/admin/news/newssource/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'fetch_selected_sources')
        response=self.client.get('/admin/news/fetchrun/')
        self.assertContains(response,'QA failure fixture')
        self.assertEqual(self.client.get('/admin/news/article/').status_code,200)
