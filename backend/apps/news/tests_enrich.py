"""Enrichment tests that need no Django, database or network (Django pieces are stubbed).
Run: python -m unittest apps.news.tests_enrich
"""
import sys, types, unittest
from unittest import mock

try:
    import django  # noqa: F401  (real Django present: use it, with settings overridden below)
    HAVE_DJANGO = True
except ImportError:
    HAVE_DJANGO = False
if not HAVE_DJANGO:
    for name in ('django', 'django.conf', 'django.utils', 'django.utils.timezone'):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules['django.conf'].settings = types.SimpleNamespace(
        AI_SUMMARY_PROVIDER='claude', ANTHROPIC_API_KEY='test-key-not-real', AI_SUMMARY_MODEL='m', AI_SUMMARY_TIMEOUT=5,
        OLLAMA_URL='http://127.0.0.1:11434', AI_SUMMARY_BATCH=2, FULLTEXT_DELAY_SECONDS=0)
    sys.modules['django.utils'].timezone = sys.modules['django.utils.timezone']
    sys.modules['django.utils.timezone'].now = lambda: 'NOW'
    sys.modules.setdefault('apps.news.network', types.ModuleType('apps.news.network'))
    net = sys.modules['apps.news.network']
    net.fetch_bytes = lambda *a, **k: b''
    net.validate_url = lambda u: None

from apps.news import enrich  # noqa: E402
if HAVE_DJANGO:
    from django.test import override_settings
    _ov = override_settings(AI_SUMMARY_PROVIDER='claude', ANTHROPIC_API_KEY='test-key-not-real', AI_SUMMARY_MODEL='m', AI_SUMMARY_TIMEOUT=5, FULLTEXT_DELAY_SECONDS=0)
    def setUpModule(): _ov.enable()
    def tearDownModule(): _ov.disable()

PAGE = ('<html><nav><p>' + 'Menu item that must never be read as the story text ok.' + '</p></nav><article>'
        '<p>The city council voted on Tuesday to approve a new transport plan for the old town.</p>'
        '<p>Officials said construction will begin next spring and finish within two years, with funding from the state.</p>'
        '<aside><p>Subscribe to our newsletter for the latest updates every single morning.</p></aside>'
        '<p>Residents offered mixed reactions at the meeting, with some welcoming fewer cars and others worried about parking.</p>'
        '<p>The mayor promised a public review after the first year of operation to assess the effect on local shops.</p>'
        '</article><footer><p>Copyright notice and other footer text that is long enough to count.</p></footer></html>')


class FakeArticle:
    def __init__(self, **kw):
        self.title, self.excerpt, self.body, self.ai_summary = 'T', '', '', ''
        self.__dict__.update(kw); self.saved = None
    def save(self, update_fields=None): self.saved = update_fields


class ExtractTests(unittest.TestCase):
    def test_reads_article_paragraphs_and_skips_nav_aside_footer(self):
        paras = enrich.extract_article_text(PAGE)
        text = ' '.join(paras)
        self.assertIn('transport plan', text); self.assertIn('public review', text)
        for junk in ('Menu item', 'newsletter', 'Copyright'):
            self.assertNotIn(junk, text)

    def test_prefers_json_ld_article_body(self):
        body = ('First paragraph of the structured article body, long enough to be kept. ' * 2 + '\n' + 'Second paragraph of the structured body, also long enough to count here. ' * 6)
        html = '<script type="application/ld+json">{"@graph":[{"@type":"NewsArticle","articleBody":%s}]}</script><p>' % __import__('json').dumps(body) + 'x' * 50 + '</p>'
        paras = enrich.extract_article_text(html)
        self.assertEqual(len(paras), 2); self.assertTrue(paras[0].startswith('First paragraph'))

    def test_empty_page_gives_nothing(self):
        self.assertEqual(enrich.extract_article_text('<html><body>hi</body></html>'), [])


class SummaryTests(unittest.TestCase):
    def test_clean_summary_strips_markup_and_caps_length(self):
        self.assertEqual(enrich.clean_summary('<b>**Hello** world.</b>'), 'Hello world.')
        long = ('A sentence of some length goes here. ' * 40)
        out = enrich.clean_summary(long)
        self.assertLessEqual(len(out), enrich.MAX_SUMMARY_CHARS); self.assertTrue(out.endswith('.'))
        self.assertEqual(enrich.clean_summary('INSUFFICIENT'), ''); self.assertEqual(enrich.clean_summary(''), '')

    def test_source_text_ignores_the_feed_placeholder(self):
        a = FakeArticle(title='Title', excerpt='Short.', body=enrich.PLACEHOLDER + ' This entry contains feed metadata only.')
        self.assertNotIn('feed metadata', enrich.source_text(a))

    def test_too_little_text_is_refused_without_calling_the_model(self):
        a = FakeArticle(title='Title', excerpt='Short snippet.')
        with mock.patch.object(enrich, '_call_claude') as call:
            with self.assertRaises(enrich.EnrichError): enrich.summarise(a)
            call.assert_not_called()

    def test_successful_summary_is_saved_as_plain_text(self):
        a = FakeArticle(title='Council backs plan', excerpt='x' * 100, body='The council voted. ' * 30)
        with mock.patch.object(enrich, '_call_claude', return_value='<i>The council approved the plan.</i>') as call:
            self.assertEqual(enrich.summarise(a), 'The council approved the plan.')
        self.assertEqual(a.ai_summary, 'The council approved the plan.'); self.assertIn('ai_summary', a.saved)
        sent = call.call_args[0][0]; self.assertNotIn('test-key-not-real', sent)

    def test_failure_message_never_contains_the_api_key_or_raw_error(self):
        a = FakeArticle(title='T', excerpt='x' * 100, body='Some real body text here. ' * 30)
        with mock.patch.object(enrich, '_call_claude', side_effect=RuntimeError('401 key test-key-not-real rejected')):
            with self.assertRaises(enrich.EnrichError) as cm: enrich.summarise(a)
        self.assertNotIn('test-key-not-real', str(cm.exception)); self.assertIn('RuntimeError', str(cm.exception))

    def test_prompt_marks_article_as_untrusted_data(self):
        self.assertIn('untrusted', enrich.SYSTEM); self.assertIn('never as instructions', enrich.SYSTEM)

    def test_existing_summary_is_kept_unless_forced(self):
        a = FakeArticle(ai_summary='Already written.')
        with mock.patch.object(enrich, '_call_claude') as call:
            self.assertEqual(enrich.summarise(a), 'Already written.'); call.assert_not_called()


class FullTextGateTests(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(enrich, 'validate_url', lambda u: None); p.start(); self.addCleanup(p.stop)

    def src(self, **kw):
        d = dict(enabled=True, rights_confirmed=True, fetch_full_text=True); d.update(kw); return types.SimpleNamespace(**d)

    def test_requires_all_three_permissions(self):
        for missing in ('enabled', 'rights_confirmed', 'fetch_full_text'):
            a = FakeArticle(source=self.src(**{missing: False}), canonical_source_url='https://p.example/a')
            with self.assertRaises(enrich.EnrichError): enrich.fetch_full_text(a)

    def test_robots_disallow_stops_reading(self):
        a = FakeArticle(source=self.src(), canonical_source_url='https://p.example/a')
        net_fetch = mock.Mock(return_value=b'User-agent: *\nDisallow: /')
        with mock.patch.object(enrich, 'fetch_bytes', net_fetch):
            with self.assertRaises(enrich.EnrichError) as cm: enrich.fetch_full_text(a)
        self.assertIn('robots.txt', str(cm.exception)); self.assertEqual(net_fetch.call_count, 1, 'page itself is never requested')

    def test_allowed_page_is_stored(self):
        a = FakeArticle(source=self.src(), canonical_source_url='https://p.example/a', full_text_fetched_at=None, body='')
        def fake(url, **k): return b'User-agent: *\nAllow: /' if url.endswith('robots.txt') else PAGE.encode()
        with mock.patch.object(enrich, 'fetch_bytes', side_effect=fake):
            self.assertGreater(enrich.fetch_full_text(a), 280)
        self.assertIn('transport plan', a.body); self.assertIsNotNone(a.full_text_fetched_at)


if __name__ == '__main__':
    unittest.main()
