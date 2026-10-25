"""Fill missing image URLs on ALREADY-IMPORTED articles, when the source owner permits it.

Why this exists: a normal fetch skips articles it already has, so articles imported while
``allow_images`` was off can never receive an image later. This command re-reads the
feed and updates only ``remote_image_url`` (plus a blank alt text / credit) on matching
articles that currently have no image.

Safety: dry-run by default; ``--apply`` required to write. It never changes source
permissions, never creates or deletes articles, never overwrites an existing image,
and applies exactly the same host policy as ingestion (``apps.news.images``).
"""
import hashlib
from collections import Counter
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.news.ingestion import ADAPTERS
from apps.news.images import image_decision, OK
from apps.news.models import Article, NewsSource
from apps.news.network import fetch_bytes


class Command(BaseCommand):
    help = 'Dry-run by default: report/apply permitted feed images for existing articles of one source.'

    def add_arguments(self, parser):
        parser.add_argument('--source', type=int, required=True, help='NewsSource ID.')
        parser.add_argument('--apply', action='store_true', help='Write remote_image_url on matching articles.')

    def handle(self, *args, **opts):
        if not settings.NEWS_FETCH_ENABLED:
            raise CommandError('News fetching is disabled; set NEWS_FETCH_ENABLED=1 to read the feed.')
        try:
            source = NewsSource.objects.get(pk=opts['source'])
        except NewsSource.DoesNotExist:
            raise CommandError('Unknown source ID.')
        if not source.enabled or not source.rights_confirmed:
            raise CommandError('Source must be enabled and rights confirmed. No flags were changed.')
        adapter = ADAPTERS.get(source.adapter)
        if adapter is None:
            raise CommandError('Unsupported source adapter.')
        instance = adapter()
        rows = instance.fetch(source) if hasattr(instance, 'fetch') else instance.parse(fetch_bytes(source.feed_url))
        reasons, updated, already, unmatched = Counter(), 0, 0, 0
        for row in rows:
            digest = hashlib.sha256(row['url'].encode()).hexdigest()
            article = Article.objects.filter(source=source, source_url_hash=digest, is_sample=False).first()
            if not article:
                unmatched += 1
                continue
            if article.image_path or article.remote_image_url:
                already += 1
                continue
            url, reason = image_decision(row.get('image'), source.allow_images, source.image_hosts)
            reasons[reason] += 1
            if reason != OK or not opts['apply']:
                continue
            fields = {'remote_image_url': url}
            if not article.image_alt:
                fields['image_alt'] = article.title[:220]
            if not article.image_credit:
                fields['image_credit'] = source.name[:220]
            Article.objects.filter(pk=article.pk, remote_image_url='', image_path='').update(**fields)
            updated += 1
        self.stdout.write(f'SOURCE: {source.name} (id={source.pk}); feed entries={len(rows)}')
        self.stdout.write(f'MATCHED: already_have_image={already} missing_image={sum(reasons.values())} not_in_database={unmatched}')
        for reason, count in sorted(reasons.items()):
            self.stdout.write(f'  {reason}: {count}')
        if opts['apply']:
            self.stdout.write(self.style.SUCCESS(f'APPLIED: {updated} article(s) updated. Source permissions untouched.'))
        else:
            self.stdout.write('DRY RUN: nothing written. Re-run with --apply after the image policy is approved.')
