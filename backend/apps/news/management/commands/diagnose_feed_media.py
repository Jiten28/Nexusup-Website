"""Read-only diagnostics for feed image/content availability and current source permissions."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.news.models import Article, NewsSource
from apps.news.ingestion import ADAPTERS
from apps.news.network import fetch_bytes

class Command(BaseCommand):
    help = 'Read-only: report source image permissions, feed candidates, and existing article media counts.'
    def add_arguments(self, parser): parser.add_argument('--source', type=int, required=True)
    def handle(self, *args, **opts):
        if not settings.NEWS_FETCH_ENABLED:
            raise CommandError('News fetching is disabled; set NEWS_FETCH_ENABLED=1 explicitly.')
        try: source=NewsSource.objects.get(pk=opts['source'])
        except NewsSource.DoesNotExist: raise CommandError('Unknown source ID.')
        if not source.enabled or not source.rights_confirmed:
            raise CommandError('Source must be enabled and rights confirmed. No source flags were changed.')
        adapter=ADAPTERS.get(source.adapter)
        if adapter is None: raise CommandError('Unsupported source adapter.')
        instance=adapter()
        rows=instance.fetch(source) if hasattr(instance,'fetch') else instance.parse(fetch_bytes(source.feed_url))
        matched=[]
        import hashlib
        for row in rows:
            digest=hashlib.sha256(row['url'].encode()).hexdigest()
            article=Article.objects.filter(source=source,source_url_hash=digest,is_sample=False).first()
            if article: matched.append((article,row))
        existing=Article.objects.filter(source=source,is_sample=False)
        feed_images=sum(bool(r.get('image')) for r in rows)
        feed_content=sum(bool((r.get('content') or '').strip()) for r in rows)
        missing_images=existing.filter(image_path='',remote_image_url='').count()
        fallback='Read the original publisher for the complete report. This entry contains feed metadata only.'
        missing_content=existing.filter(body__in=['',fallback]).count()
        self.stdout.write(f'SOURCE: {source.name} (id={source.pk}, adapter={source.adapter})')
        self.stdout.write(f'FEED: entries={len(rows)} with_image_candidates={feed_images} with_longer_content={feed_content}')
        self.stdout.write(f'DATABASE: imported_articles={existing.count()} missing_images={missing_images} metadata_only_bodies={missing_content} matched_by_source_url={len(matched)}')
        self.stdout.write(f'IMAGE_POLICY: allow_images={source.allow_images} approved_hosts={source.image_hosts!r}')
        if not source.allow_images:
            self.stdout.write(self.style.WARNING('Images cannot be backfilled until the source owner verifies rights and explicitly enables image reuse.'))
        elif not source.image_hosts:
            self.stdout.write(self.style.WARNING('No image hostnames are approved. Review publisher terms and feed candidates before adding exact permitted hosts.'))
        if feed_images==0:
            self.stdout.write(self.style.WARNING('This feed response contains no recognized image candidates. The parser will not scrape article pages automatically.'))
        if feed_content==0:
            self.stdout.write(self.style.WARNING('This feed response contains no longer article content. Only feed summaries/source links are available without a separately authorized content source.'))
        self.stdout.write('READ ONLY: no article, source, or fetch-run records were changed.')
