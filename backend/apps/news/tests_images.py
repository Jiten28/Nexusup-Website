"""Image policy tests. Plain unittest: no Django, database or network needed."""
import unittest
from apps.news.images import (best_candidate, image_decision, approved_remote_image, safe_https_url,
                              OK, NO_IMAGE, UNSAFE, NOT_ENABLED, NO_HOSTS, HOST_NOT_APPROVED)


class SafeUrlTests(unittest.TestCase):
    def test_accepts_plain_https_only(self):
        self.assertEqual(safe_https_url(' https://ichef.bbci.co.uk/a.jpg '), 'https://ichef.bbci.co.uk/a.jpg')
        for bad in ['', None, 5, 'http://x.example/a.jpg', 'javascript:alert(1)', 'data:image/png;base64,AA',
                    'https://user:pw@x.example/a.jpg', 'https://x.example:bad/a.jpg', '//x.example/a.jpg',
                    'https://x.example/' + 'a' * 1000]:
            self.assertEqual(safe_https_url(bad), '', bad)


class CandidateTests(unittest.TestCase):
    def test_first_valid_wins_without_widths(self):
        c = [('http://insecure.example/a.jpg', None), ('https://a.example/1.jpg', None), ('https://a.example/2.jpg', None)]
        self.assertEqual(best_candidate(c), 'https://a.example/1.jpg')

    def test_widest_declared_wins_and_ties_keep_feed_order(self):
        c = [('https://a.example/240.jpg', '240'), ('https://a.example/1200.jpg', '1200'), ('https://a.example/1200b.jpg', 1200)]
        self.assertEqual(best_candidate(c), 'https://a.example/1200.jpg')

    def test_bad_width_does_not_crash_and_empty_is_empty(self):
        self.assertEqual(best_candidate([('https://a.example/x.jpg', 'wide')]), 'https://a.example/x.jpg')
        self.assertEqual(best_candidate([]), '')

    def test_urls_are_never_rewritten(self):
        url = 'https://ichef.bbci.co.uk/ace/standard/240/cpsprodpb/a.jpg'
        self.assertEqual(best_candidate([(url, 240)]), url)


class PolicyTests(unittest.TestCase):
    URL = 'https://ichef.bbci.co.uk/a.jpg'

    def test_default_deny_reasons(self):
        self.assertEqual(image_decision('', True, ['ichef.bbci.co.uk']), ('', NO_IMAGE))
        self.assertEqual(image_decision('http://x.example/a.jpg', True, ['x.example']), ('', UNSAFE))
        self.assertEqual(image_decision(self.URL, False, ['ichef.bbci.co.uk']), ('', NOT_ENABLED))
        self.assertEqual(image_decision(self.URL, True, []), ('', NO_HOSTS))
        self.assertEqual(image_decision(self.URL, True, ['other.example']), ('', HOST_NOT_APPROVED))

    def test_exact_host_match_is_case_insensitive_and_not_a_suffix_match(self):
        self.assertEqual(image_decision(self.URL, True, ['ICHEF.BBCI.CO.UK']), (self.URL, OK))
        self.assertEqual(approved_remote_image(self.URL, True, ['bbci.co.uk']), '')
        self.assertEqual(approved_remote_image('https://evil.example/ichef.bbci.co.uk/a.jpg', True, ['ichef.bbci.co.uk']), '')

    def test_malformed_host_list_is_ignored(self):
        self.assertEqual(image_decision(self.URL, True, [None, '', 5]), ('', NO_HOSTS))


if __name__ == '__main__':
    unittest.main()
