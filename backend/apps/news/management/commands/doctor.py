"""One-command health check: tells you what is wrong and the exact next step. Read-only.

    python manage.py doctor                 # settings, sources, articles, pictures, translation
    python manage.py doctor --check-images  # also request 3 stored picture URLs and report the HTTP result
Never prints passwords or API keys.
"""
import urllib.request
from collections import Counter
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from apps.news.models import Article, Category, NewsSource


class Command(BaseCommand):
    help = 'Read-only health check with plain-language fixes.'

    def add_arguments(self, parser):
        parser.add_argument('--check-images', action='store_true', help='Request up to 3 stored picture URLs and report the result.')

    def handle(self, *args, **opts):
        self.problems = 0
        def ok(msg): self.stdout.write(self.style.SUCCESS('  OK    ') + msg)
        def warn(msg, fix=''):
            self.problems += 1
            self.stdout.write(self.style.WARNING('  CHECK ') + msg)
            if fix: self.stdout.write('        -> ' + fix)
        head = lambda t: self.stdout.write(f'\n{t}')

        head('Database')
        try:
            connection.ensure_connection()
            ok(f"connected: {connection.vendor} ({connection.settings_dict['NAME']})")
        except Exception as exc:
            warn(f'cannot connect: {type(exc).__name__}', 'check DB_* values in backend/.env; for MariaDB run: database/scripts/db status'); return
        if connection.vendor == 'sqlite' and not settings.DEBUG:
            warn('SQLite in production mode', 'set DB_ENGINE=mariadb')

        head('Settings')
        (ok if settings.NEWS_FETCH_ENABLED else warn)('fetching enabled (NEWS_FETCH_ENABLED=1)' if settings.NEWS_FETCH_ENABLED else 'fetching is OFF',
            '' if settings.NEWS_FETCH_ENABLED else 'set NEWS_FETCH_ENABLED=1 in backend/.env and restart')
        self.stdout.write(f'        allowed hosts: {", ".join(settings.ALLOWED_HOSTS)}')
        self.stdout.write(f'        frontend url: {settings.FRONTEND_URL}')

        head('Sources')
        sources = list(NewsSource.objects.select_related('default_category'))
        if not sources:
            warn('no sources yet', 'Admin -> News sources -> "Add recommended sources"')
        for s in sources:
            arts = Article.objects.filter(source=s, is_sample=False)
            total, pics = arts.count(), arts.exclude(remote_image_url='', image_path='').count()
            state = 'on ' if (s.enabled and s.rights_confirmed) else 'off'
            self.stdout.write(f'  [{state}] {s.name}: {total} stories, {pics} with picture; images {"allowed" if s.allow_images else "blocked"}, hosts={s.image_hosts or "none"}')
            if s.enabled and s.rights_confirmed and total == 0 and not s.last_success_at:
                warn(f'{s.name} is approved but has never been fetched', 'Admin -> News sources -> tick it -> "2. Fetch now"')
            if s.last_error:
                warn(f'{s.name} last error: {s.last_error[:160]}')
            if s.enabled and s.rights_confirmed and total and not pics:
                if not s.allow_images:
                    warn(f'{s.name}: stories have no pictures because "Allow images" is off', 'only if you have permission: action "1. Approve", then "2b. Get pictures for stories already saved"')
                elif not s.image_hosts:
                    warn(f'{s.name}: "Allow images" is on but the picture hosts list is empty', 'action "2b. Get pictures for stories already saved" fills it from the feed')
                else:
                    warn(f'{s.name}: picture hosts are set but no story has a picture', 'action "2b. Get pictures for stories already saved"; if still empty the feed may not include pictures or lists other hosts (see: python manage.py backfill_images --source %d)' % s.pk)

        head('Stories')
        published = Article.objects.published()
        real = published.filter(is_sample=False).count()
        samples = published.filter(is_sample=True).count()
        drafts = Article.objects.filter(status='draft', is_sample=False).count()
        ok(f'{real} published real stories; {drafts} drafts waiting; {samples} sample stories ({"hidden" if real else "shown because no real story is published"})')
        if drafts and not real:
            warn('stories exist only as drafts', 'Admin -> Articles -> tick drafts -> "Publish selected articles now"')
        empty = [c.name for c in Category.objects.all() if not published.filter(category=c, is_sample=False).exists()]
        if empty:
            self.stdout.write(f'        categories with no published story (hidden on the site): {", ".join(empty)}')
        by_src = Counter(published.filter(is_sample=False).values_list('source__name', flat=True))
        for name, n in by_src.most_common(): self.stdout.write(f'        {name or "manual"}: {n}')

        head('Translation')
        provider = settings.TRANSLATION_PROVIDER
        if provider == 'disabled':
            warn('translation is disabled', 'see README section 7: start LibreTranslate, then set TRANSLATION_PROVIDER=libre in backend/.env')
        else:
            try:
                from apps.news.services import languages
                langs = languages()
                ok(f'provider "{provider}" reachable; {len(langs)} languages: ' + ', '.join(l['code'] for l in langs[:12]))
            except Exception as exc:
                warn(f'provider "{provider}" is not responding: {exc}', 'start it (docker compose -f backend/translate/compose.yaml up -d) and wait for the models to download')

        if opts['check_images']:
            head('Picture check (3 stored URLs)')
            urls = list(Article.objects.exclude(remote_image_url='').values_list('remote_image_url', flat=True)[:3])
            if not urls: warn('no stored picture URLs to test')
            for url in urls:
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'NexusUp-doctor'})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        ok(f'{r.status} {r.headers.get("Content-Type")} {url[:90]}')
                except Exception as exc:
                    warn(f'{type(exc).__name__}: {url[:90]}', 'the publisher refused or the URL is dead; the site then shows its placeholder')
        self.stdout.write('\n' + ('Everything looks fine.' if not self.problems else f'{self.problems} item(s) to look at (marked CHECK).'))
