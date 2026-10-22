"""Credential-free diagnostics. No database connection unless --sources is requested."""
import importlib
import os
import json
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Print non-secret effective backend configuration; --sources adds read-only source metadata.'

    def add_arguments(self, parser):
        parser.add_argument('--sources', action='store_true')

    def handle(self, *args, **options):
        module_name = getattr(settings, 'SETTINGS_MODULE', None) or os.environ.get('DJANGO_SETTINGS_MODULE')
        module = importlib.import_module(module_name) if module_name else None
        db = settings.DATABASES['default']
        data = {
            'settings_module':module_name,
            'settings_file':str(Path(module.__file__).resolve()) if module else 'Programmatically configured; no module identified',
            'backend_root':str(settings.BASE_DIR),
            'dotenv_exists':(settings.BASE_DIR / '.env').is_file(),
            'DEBUG':settings.DEBUG,
            'database_engine':db['ENGINE'],
            'database_name':str(Path(db['NAME']).resolve()) if db['ENGINE'].endswith('sqlite3') and str(db['NAME']) != ':memory:' else str(db['NAME']),
            'NEWS_FETCH_ENABLED':settings.NEWS_FETCH_ENABLED,
            'NEWS_API_KEY_present':bool(settings.NEWS_API_KEY),
            'translation_provider':settings.TRANSLATION_PROVIDER,
            'translation_key_present':bool(settings.TRANSLATION_API_KEY),
            'note':'Enabling a source does not execute or schedule ingestion. No secret values are displayed.',
        }
        if options['sources']:
            from apps.news.models import NewsSource
            data['sources'] = []
            for source in NewsSource.objects.order_by('pk'):
                parsed = urlsplit(source.feed_url)
                data['sources'].append({
                    'id':source.pk,'name':source.name,'adapter':source.adapter,
                    'endpoint_host':parsed.hostname,'endpoint_path':parsed.path,
                    'url_contains_credentials':bool(parsed.username or parsed.password or any(k.lower() in ('apikey','key','token') for k,v in parse_qsl(parsed.query))),
                    'enabled':source.enabled,'rights_confirmed':source.rights_confirmed,
                    'trusted':source.trusted,'auto_publish':source.auto_publish,
                    'next_fetch_at':source.next_fetch_at.isoformat() if source.next_fetch_at else None,
                    'last_success_at':source.last_success_at.isoformat() if source.last_success_at else None,
                    'last_error_present':bool(source.last_error),
                })
        self.stdout.write(json.dumps(data, indent=2))
