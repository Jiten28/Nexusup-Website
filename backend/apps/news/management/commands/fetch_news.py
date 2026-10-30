from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.news.models import NewsSource, FetchRun
from apps.news.ingestion import ingest


class Command(BaseCommand):
    help = 'Explicitly fetch eligible sources once. Enabling a source does not schedule or run it.'

    def add_arguments(self, parser):
        parser.add_argument('--source', type=int, help='Existing NewsSource database ID (not a name or URL).')
        parser.add_argument('--dry-run', action='store_true', help='Network/parse only; no database writes or fetch-run records.')

    def handle(self, *args, **options):
        sources = NewsSource.objects.select_related('default_category')
        if options['source'] is not None:
            sources = sources.filter(pk=options['source'])
            if not sources.exists():
                raise CommandError('No source exists for the supplied ID; check the database selected by this process.')
        else:
            if not settings.NEWS_FETCH_ENABLED:
                raise CommandError('News fetching is disabled. Review rights before setting NEWS_FETCH_ENABLED=1.')
            sources = sources.filter(enabled=True, rights_confirmed=True)
            if not sources.exists():
                raise CommandError('No eligible sources: review source selection and rights; no flags were changed.')
        failures = 0
        for source in sources:
            try:
                result = ingest(source, dry_run=options['dry_run'])
                self.stdout.write(f'source_id={source.pk}: {result}')
                if not options['dry_run']:
                    run = FetchRun.objects.filter(pk=getattr(source, '_last_fetch_run_id', None)).first()
                    if run:
                        self.stdout.write(f'run_id={run.pk} state={run.state} fetched={run.fetched} parsed={run.parsed} rejected={run.rejected} duplicates={run.duplicates} saved={run.imported} published={run.published}')
            except ValueError as exc:
                failures += 1
                self.stderr.write(f'source_id={source.pk}: {exc}')
        if settings.AI_SUMMARY_AFTER_FETCH and not options['dry_run']:
            from apps.news import enrich
            out, problems = enrich.enrich_batch()
            self.stdout.write(f'extra steps: {out}')
        if failures:
            raise CommandError(f'{failures} source fetch(es) failed or were blocked; stored content retained.')
