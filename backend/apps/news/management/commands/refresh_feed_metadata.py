"""Backfill blank fields on already-imported articles from their own authorized feed.

Defaults to dry-run. Never publishes drafts, changes featured status, or overwrites
non-empty editorial content. Image URLs still require explicit source image permission
and an allow-listed HTTPS hostname.
"""
import hashlib
from urllib.parse import urlsplit
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.news.models import Article, NewsSource
from apps.news.ingestion import ADAPTERS
from apps.news.network import fetch_bytes

SUMMARY_FALLBACK = 'Read the original publisher for the complete report. This entry contains feed metadata only.'

class Command(BaseCommand):
    help = 'Dry-run or safely backfill missing image/content metadata on existing imported stories.'
    def add_arguments(self, parser):
        parser.add_argument('--source', type=int, required=True, help='Existing NewsSource ID')
        parser.add_argument('--apply', action='store_true', help='Write only missing metadata; default is dry-run')
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
        matched=changed=images=content=0
        apply=bool(opts['apply'])
        for row in rows:
            digest=hashlib.sha256(row['url'].encode()).hexdigest()
            article=Article.objects.filter(source=source,source_url_hash=digest,is_sample=False).first()
            if not article: continue
            matched+=1; updates={}
            if source.allow_images and not article.remote_image_url and row.get('image'):
                try:p=urlsplit(row['image'])
                except ValueError:p=None
                allowed={host.lower() for host in source.image_hosts}
                if p and p.scheme=='https' and p.hostname and p.hostname.lower() in allowed and not p.username and not p.password and len(row['image'])<=1000:
                    updates['remote_image_url']=row['image'];updates['image_alt']=article.title;updates['image_credit']=source.name;images+=1
            old_body=(article.body or '').strip()
            new_body=(row.get('content') or '').strip()
            if new_body and (not old_body or old_body==SUMMARY_FALLBACK):
                updates['body']=new_body[:50000];content+=1
            if not (article.excerpt or '').strip() and row.get('excerpt'):
                updates['excerpt']=row['excerpt'][:360]
            if updates:
                changed+=1
                if apply: Article.objects.filter(pk=article.pk).update(**updates)
        mode='APPLIED' if apply else 'DRY RUN (no writes)'
        self.stdout.write(f'{mode}: matched={matched} articles_with_changes={changed} image_candidates={images} content_candidates={content}')
        if not apply:self.stdout.write('Review source rights/image host allow-list, then rerun with --apply to fill blank fields only.')
