from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.news import enrich


class Command(BaseCommand):
    help = ('Read full article pages (only for sources that allow it) and write AI summaries for stories that have none. '
            'Bounded per run; safe to repeat. Secrets are never printed.')

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=settings.AI_SUMMARY_BATCH, help='Maximum stories per step this run.')
        parser.add_argument('--no-fulltext', action='store_true', help='Skip reading full article pages.')
        parser.add_argument('--no-summaries', action='store_true', help='Skip AI summaries.')
        parser.add_argument('--published-only', action='store_true')

    def handle(self, *args, **o):
        if not o['no_summaries'] and not enrich.provider_ready():
            self.stdout.write('AI summaries: not configured (set AI_SUMMARY_PROVIDER=claude plus ANTHROPIC_API_KEY, or =ollama, in backend/.env).')
        out, problems = enrich.enrich_batch(limit=max(1, min(o['limit'], 100)), fulltext=not o['no_fulltext'],
                                            summaries=not o['no_summaries'], only_published=o['published_only'])
        self.stdout.write(f"full pages read={out['fulltext']} summaries written={out['summarised']} skipped={out['skipped']} failed={out['failed']}")
        for title, why in problems[:20]:
            self.stdout.write(f'  - {title}: {why}')
