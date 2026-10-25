"""Read-only status report: categories, freshness, images, sources and recent fetch runs.

No network, no writes, no secrets (key presence only). Run it first when a page looks
empty or stale: it shows exactly where articles are, and why images are missing.
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count, Max, Q
from django.utils import timezone
from apps.news.images import NOT_ENABLED, NO_HOSTS
from apps.news.models import Article, Category, FetchRun, NewsSource


class Command(BaseCommand):
    help = 'Read-only report of categories, article freshness, image coverage, sources and fetch history.'

    def handle(self, *args, **options):
        now = timezone.now()
        out = self.stdout.write
        out(f'DATABASE: {settings.DATABASES["default"]["NAME"]}')
        out(f'FETCH_ENABLED={settings.NEWS_FETCH_ENABLED} NEWS_API_KEY_present={bool(settings.NEWS_API_KEY)} TRANSLATION_PROVIDER={settings.TRANSLATION_PROVIDER}')
        out('')
        out('CATEGORIES (public = published, not future-dated, real articles)')
        out(f'{"slug":<22}{"public":>7}{"drafts":>8}{"samples":>8}{"w/image":>8}  newest public article')
        pub = Q(article__is_sample=False, article__status='published', article__published_at__lte=now)
        rows = Category.objects.annotate(
            public=Count('article', filter=pub),
            drafts=Count('article', filter=Q(article__is_sample=False, article__status='draft')),
            samples=Count('article', filter=Q(article__is_sample=True)),
            with_image=Count('article', filter=pub & (~Q(article__remote_image_url='') | ~Q(article__image_path=''))),
            newest=Max('article__source_published_at', filter=pub),
        ).order_by('position', 'name')
        for c in rows:
            age = f'{c.newest:%Y-%m-%d %H:%M} UTC ({(now - c.newest).total_seconds() / 3600:.1f}h ago)' if c.newest else '-'
            out(f'{c.slug:<22}{c.public:>7}{c.drafts:>8}{c.samples:>8}{c.with_image:>8}  {age}')
        out('')
        out('SOURCES')
        for s in NewsSource.objects.order_by('pk'):
            n = Article.objects.filter(source=s).count()
            if not s.allow_images:
                image_state = NOT_ENABLED
            elif not s.image_hosts:
                image_state = NO_HOSTS
            else:
                image_state = 'images allowed on ' + ', '.join(s.image_hosts)
            out(f'  id={s.pk} {s.name} adapter={s.adapter} enabled={s.enabled} rights={s.rights_confirmed} trusted={s.trusted} auto_publish={s.auto_publish} articles={n}')
            out(f'     category={s.default_category.slug} interval={s.interval_minutes}m next_fetch_at={s.next_fetch_at} last_success_at={s.last_success_at}')
            out(f'     image policy: {image_state}')
            if s.last_error:
                out(f'     last_error: {s.last_error}')
        out('')
        out('RECENT FETCH RUNS (newest first)')
        for r in FetchRun.objects.select_related('source').order_by('-started_at')[:8]:
            out(f'  {r.started_at:%Y-%m-%d %H:%M} src={r.source_id} {r.state} fetched={r.fetched} saved={r.imported} published={r.published} dup={r.duplicates} {r.error}')
        out('')
        out('READ ONLY: nothing was changed.')
