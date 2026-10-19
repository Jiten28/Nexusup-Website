from datetime import timedelta
from pathlib import Path
from django.test import TestCase,Client,override_settings
from django.core.management import call_command
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import Article,Comment,ContactMessage

@override_settings(DEBUG=True)
class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo',verbosity=0)
    def setUp(self):
        cache.clear()
        self.article=Article.objects.first()
    def test_core_routes(self):
        for url in ['/','/stories/','/search/','/category/cricket/','/category/business/','/about/','/privacy/','/terms/','/contact/','/admin/login/','/feed/','/sitemap.xml','/robots.txt','/ads.txt',self.article.get_absolute_url()]:
            with self.subTest(url=url): self.assertEqual(self.client.get(url).status_code,200)
    def test_unknown_routes(self):
        for url in ['/story/missing/','/category/missing/']:
            self.assertEqual(self.client.get(url).status_code,404)
    def test_search_and_empty_state(self):
        self.assertContains(self.client.get('/search/',{'q':'portfolio'}),'balanced portfolio')
        self.assertContains(self.client.get('/search/',{'q':'nonexistentzz'}),'Nothing here just yet')
    def test_search_escapes_markup(self):
        r=self.client.get('/search/',{'q':'<script>alert(1)</script>'})
        self.assertNotContains(r,'<script>alert(1)</script>')
    def test_category_filter(self):
        r=self.client.get('/category/business/')
        self.assertEqual(r.context['result_count'],1)
        self.assertTrue(all(x.category.slug=='business' for x in r.context['page_obj']))
    def test_pagination(self):
        r=self.client.get('/stories/',{'page':'2'})
        self.assertEqual(r.context['page_obj'].number,2)
        self.assertEqual(len(r.context['page_obj']),4)
        self.assertEqual(self.client.get('/stories/',{'page':'bad'}).status_code,200)
    def test_drafts_and_scheduled_hidden_everywhere(self):
        self.article.status='draft';self.article.save()
        future=Article.objects.exclude(pk=self.article.pk).first()
        future.published_at=timezone.now()+timedelta(days=3);future.save()
        for post in [self.article,future]:
            self.assertEqual(self.client.get(post.get_absolute_url()).status_code,404)
            for url in ['/','/stories/','/feed/','/sitemap.xml']:
                self.assertNotContains(self.client.get(url),post.title)
    def test_comment_moderation_and_throttle(self):
        path=self.article.get_absolute_url()
        self.assertEqual(self.client.post(path,{'name':'Sample Reader','body':'Fictional comment'}).status_code,302)
        self.assertFalse(Comment.objects.get().approved)
        self.assertNotContains(self.client.get(path),'Fictional comment')
        self.client.post(path,{'name':'Sample Reader','body':'second comment'})
        self.assertEqual(Comment.objects.count(),1)
        Comment.objects.update(approved=True)
        self.assertContains(self.client.get(path),'Fictional comment')
    def test_stored_comment_escapes_html(self):
        Comment.objects.create(article=self.article,name='Example',body='<script>alert(1)</script>',approved=True)
        r=self.client.get(self.article.get_absolute_url())
        self.assertContains(r,'&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(r,'<script>alert(1)</script>')
    def test_csrf_enforced(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(c.post('/contact/',{'name':'Demo','email':'demo@example.invalid','message':'Fictional'}).status_code,403)
        self.assertEqual(c.post(self.article.get_absolute_url(),{'name':'Demo','body':'Fictional'}).status_code,403)
    def test_contact_local_storage_no_mail(self):
        from django.core import mail
        r=self.client.post('/contact/',{'name':'Demo Person','email':'demo@example.invalid','message':'Fictional demo message'})
        self.assertEqual(r.status_code,302)
        self.assertEqual(ContactMessage.objects.count(),1)
        self.assertEqual(len(mail.outbox),0)
    def test_form_validation_and_honeypot(self):
        for data in [{'name':'Demo','email':'invalid','message':'text'},{'name':'Demo','email':'demo@example.invalid','message':'text','website':'spam'}]:
            r=self.client.post('/contact/',data)
            self.assertEqual(r.status_code,200)
        self.assertEqual(ContactMessage.objects.count(),0)
    def test_seed_idempotent(self):
        before=Article.objects.count();call_command('seed_demo',verbosity=0)
        self.assertEqual(Article.objects.count(),before)
    def test_sample_labels_noindex_and_canonical(self):
        r=self.client.get(self.article.get_absolute_url())
        self.assertContains(r,'Illustrative sample, not news reporting')
        self.assertContains(r,'noindex,nofollow')
        self.assertContains(r,'http://127.0.0.1:8000'+self.article.get_absolute_url())
    def test_all_media_paths_exist_and_safe(self):
        for article in Article.objects.exclude(image_path=''):
            article.full_clean()
            p=(settings.MEDIA_ROOT/article.image_path).resolve()
            self.assertTrue(p.is_relative_to(settings.MEDIA_ROOT.resolve()))
            self.assertTrue(p.is_file())
    def test_ads_disabled_and_optional_exact_reference(self):
        self.assertNotContains(self.client.get('/ads.txt'),'pub-4403090676624554')
        with override_settings(ADS_TXT_ENABLED=True):
            self.assertEqual(self.client.get('/ads.txt').content,(settings.BASE_DIR/'docs/reference-ads.txt').read_bytes())
    def test_public_pages_do_not_reference_providers(self):
        for url in ['/','/stories/',self.article.get_absolute_url()]:
            r=self.client.get(url)
            for host in ['googletagmanager.com','googlesyndication.com','gtranslate.net','fonts.googleapis.com']:
                self.assertNotContains(r,host)
    def test_admin_requires_auth_and_demo_author_cannot_login(self):
        self.assertEqual(self.client.get('/admin/').status_code,302)
        u=get_user_model().objects.get(username='demo-editor')
        self.assertFalse(u.has_usable_password());self.assertFalse(u.is_staff)
    def test_robots_blocks_indexing(self):
        self.assertContains(self.client.get('/robots.txt'),'Disallow: /')
    def test_reading_minutes_nonzero(self):
        self.assertGreaterEqual(self.article.reading_minutes,1)
    def test_authenticated_editor_can_publish_and_moderate(self):
        editor=get_user_model().objects.create_user(username='qa-admin',is_staff=True,is_superuser=True)
        self.client.force_login(editor)
        post=self.article;post.status='draft';post.save()
        r=self.client.post(f'/admin/news/article/{post.pk}/change/',{
            'title':post.title,'slug':post.slug,'category':post.category_id,'author':post.author_id,
            'excerpt':post.excerpt,'body':post.body,'image_path':post.image_path,'image_alt':post.image_alt,
            'image_credit':post.image_credit,'status':'published','published_at_0':timezone.localtime().strftime('%Y-%m-%d'),
            'published_at_1':'00:00:00','is_sample':'on','legacy_wordpress_id':'','seo_description':'','_save':'Save'})
        self.assertEqual(r.status_code,302)
        post.refresh_from_db();self.assertEqual(post.status,'published')
        comment=Comment.objects.create(article=post,name='Fictional reader',body='Fictional comment')
        r=self.client.post('/admin/news/comment/',{'action':'approve','_selected_action':[str(comment.pk)]})
        self.assertEqual(r.status_code,302)
        comment.refresh_from_db();self.assertTrue(comment.approved)
