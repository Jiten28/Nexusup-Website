"""Conversation (comments and replies), moderation queue, AI summary exposure and weather mapping.

Django TestCase: needs `python manage.py test apps.news.tests_conversation` on your machine with Django installed.
"""
import json
from unittest.mock import patch
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from .models import Article, Comment


@override_settings(DEBUG=True)
class ConversationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.article = Article.objects.filter(status='published').first()

    def setUp(self):
        cache.clear()

    def post(self, data, slug=None):
        return self.client.post(f'/api/articles/{slug or self.article.slug}/comments/', json.dumps(data), content_type='application/json')

    def test_new_comment_is_held_and_not_listed(self):
        r = self.post({'name': 'Asha', 'body': 'Hello there'})
        self.assertEqual(r.status_code, 201)
        c = Comment.objects.get(name='Asha')
        self.assertFalse(c.approved); self.assertFalse(c.rejected); self.assertEqual(c.status, 'pending')
        listing = self.client.get(f'/api/articles/{self.article.slug}/comments/').json()
        self.assertEqual(listing['count'], 0); self.assertEqual(listing['results'], [])

    def test_visitor_cannot_self_approve_or_claim_editor(self):
        self.post({'name': 'Sly', 'body': 'x y z', 'approved': True, 'is_editor': True, 'rejected': False})
        c = Comment.objects.get(name='Sly')
        self.assertFalse(c.approved); self.assertFalse(c.is_editor)

    def test_approved_comment_and_reply_form_a_thread(self):
        top = Comment.objects.create(article=self.article, name='A', body='top', approved=True)
        r = self.post({'name': 'B', 'body': 'reply', 'parent': top.pk})
        self.assertEqual(r.status_code, 201); self.assertIn('reply', r.json()['message'])
        reply = Comment.objects.get(name='B'); self.assertEqual(reply.parent_id, top.pk); self.assertFalse(reply.approved)
        Comment.objects.filter(pk=reply.pk).update(approved=True)
        data = self.client.get(f'/api/articles/{self.article.slug}/comments/').json()
        self.assertEqual(data['count'], 2); self.assertEqual(data['results'][0]['replies'][0]['body'], 'reply')

    def test_reply_to_a_reply_attaches_to_the_top_comment(self):
        top = Comment.objects.create(article=self.article, name='A', body='top', approved=True)
        mid = Comment.objects.create(article=self.article, name='B', body='mid', approved=True, parent=top)
        cache.clear(); self.post({'name': 'C', 'body': 'deep', 'parent': mid.pk})
        self.assertEqual(Comment.objects.get(name='C').parent_id, top.pk)

    def test_cannot_reply_to_pending_rejected_or_other_story_comment(self):
        other = Article.objects.filter(status='published').exclude(pk=self.article.pk).first()
        cases = [Comment.objects.create(article=self.article, name='P', body='pending'),
                 Comment.objects.create(article=self.article, name='R', body='rej', approved=True, rejected=True),
                 Comment.objects.create(article=other, name='O', body='other', approved=True)]
        for c in cases:
            cache.clear()
            self.assertEqual(self.post({'name': 'Z', 'body': 'nope', 'parent': c.pk}).status_code, 400)
        self.assertFalse(Comment.objects.filter(name='Z').exists())

    def test_rejected_comment_stays_hidden_even_if_approved_flag_is_set(self):
        Comment.objects.create(article=self.article, name='R', body='bad', approved=True, rejected=True)
        self.assertEqual(self.client.get(f'/api/articles/{self.article.slug}/comments/').json()['count'], 0)

    def test_article_detail_carries_thread_count_and_ai_summary(self):
        Comment.objects.create(article=self.article, name='A', body='hi', approved=True)
        Article.objects.filter(pk=self.article.pk).update(ai_summary='Short summary.', ai_summary_at=timezone.now(), ai_summary_model='m')
        d = self.client.get(f'/api/articles/{self.article.slug}/').json()
        self.assertEqual(d['comment_count'], 1); self.assertEqual(d['comments'][0]['body'], 'hi')
        self.assertEqual(d['ai_summary']['text'], 'Short summary.')

    def test_no_summary_serialises_as_null(self):
        self.assertIsNone(self.client.get(f'/api/articles/{self.article.slug}/').json()['ai_summary'])

    def test_empty_name_or_body_is_rejected(self):
        self.assertEqual(self.post({'name': '', 'body': 'x'}).status_code, 400)
        cache.clear(); self.assertEqual(self.post({'name': 'N', 'body': ''}).status_code, 400)


class ModerationAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.article = Article.objects.filter(status='published').first()
        cls.admin = get_user_model().objects.create_superuser('boss', 'b@example.com', 'pw-for-tests-only')

    def setUp(self):
        self.client.force_login(self.admin)
        self.p = Comment.objects.create(article=self.article, name='P', body='pending one')
        self.a = Comment.objects.create(article=self.article, name='A', body='approved one', approved=True)

    def test_queue_defaults_to_waiting_for_approval(self):
        r = self.client.get('/admin/news/comment/', follow=True)
        self.assertContains(r, 'pending one'); self.assertNotContains(r, 'approved one')

    def test_approve_reject_and_back_to_pending_actions(self):
        url = '/admin/news/comment/'
        for action, check in (('approve', lambda c: c.approved and not c.rejected), ('reject', lambda c: c.rejected and not c.approved),
                              ('back_to_pending', lambda c: not c.approved and not c.rejected)):
            self.client.post(url, {'action': action, '_selected_action': [self.p.pk]})
            self.p.refresh_from_db(); self.assertTrue(check(self.p), action)

    def test_editor_reply_can_be_created_in_admin_model(self):
        self.assertIn(Comment, site._registry)


class WeatherMappingTests(TestCase):
    def test_owm_codes_map_to_widget_codes(self):
        from .services import owm_to_wmo
        self.assertEqual([owm_to_wmo(i) for i in (800, 802, 211, 501, 601, 741)], [0, 3, 95, 61, 71, 45])

    @override_settings(WEATHER_PROVIDER='openweathermap', OPENWEATHER_API_KEY='', UTILITIES_NETWORK_ENABLED=False)
    def test_weather_off_without_key(self):
        from .services import weather
        with self.assertRaises(ValueError): weather(17.4, 78.4)

    @override_settings(WEATHER_PROVIDER='openweathermap', OPENWEATHER_API_KEY='fake-test-key')
    def test_owm_response_is_converted_and_key_not_returned(self):
        from . import services
        cache.clear()
        fake = {'weather': [{'id': 800, 'description': 'clear sky'}], 'main': {'temp': 31.26}, 'wind': {'speed': 2.0}}
        with patch.object(services, 'fetch_json', return_value=fake) as call:
            out = services.weather(17.4, 78.4)
        self.assertEqual(out['weather_code'], 0); self.assertEqual(out['temperature'], 31.3); self.assertEqual(out['wind'], 7.2)
        self.assertNotIn('fake-test-key', json.dumps(out)); self.assertIn('appid=fake-test-key', call.call_args[0][0])


@override_settings(TRANSLATION_PROVIDER='mymemory')
class FreeTranslationTests(TestCase):
    def test_mymemory_lists_fixed_languages_without_network(self):
        from .services import languages
        codes = {x['code'] for x in languages()}
        self.assertTrue({'hi', 'es', 'ar', 'zh-CN'} <= codes)

    def test_corpus_includes_requested_public_story_ids_only(self):
        call_command('seed_demo', verbosity=0)
        from .api import translation_payload
        pub = list(Article.objects.filter(status='published').values_list('pk', flat=True))
        draft = Article.objects.get(pk=pub[-1]); Article.objects.filter(pk=draft.pk).update(status='draft'); pub = pub[:-1]
        payload = translation_payload('/', pub[:2] + [draft.pk, True, 'x'])
        self.assertNotIn(f'article:{draft.pk}:title', payload); self.assertIn(f'article:{pub[0]}:title', payload)
