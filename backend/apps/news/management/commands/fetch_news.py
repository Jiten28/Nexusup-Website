from django.core.management.base import BaseCommand,CommandError
from django.conf import settings
from apps.news.models import NewsSource
from apps.news.ingestion import ingest
class Command(BaseCommand):
    help='Fetch eligible enabled/rights-confirmed sources on a scheduler. Never called by homepage.'
    def add_arguments(self,p):
        p.add_argument('--source',type=int)
        p.add_argument('--dry-run',action='store_true')
    def handle(self,*args,**o):
        if not settings.NEWS_FETCH_ENABLED:raise CommandError('News fetching is disabled. Set NEWS_FETCH_ENABLED=1 only after reviewing source rights and network policy.')
        sources=NewsSource.objects.filter(enabled=True,rights_confirmed=True).select_related('default_category')
        if o['source']:sources=sources.filter(pk=o['source'])
        if o['source'] and not sources.exists():raise CommandError(f'No eligible enabled source found for ID {o["source"]}.')
        failures=0
        for source in sources:
            try:self.stdout.write(f'{source.name}: {ingest(source,dry_run=o["dry_run"])}')
            except ValueError as e:
                failures+=1;self.stderr.write(f'{source.name}: {e}')
        if failures:raise CommandError(f'{failures} source fetch(es) failed; stored content was retained.')
