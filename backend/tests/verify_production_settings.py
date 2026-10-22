"""Offline production-security harness. NO MariaDB connectivity is claimed.
Run from backend: python tests/verify_production_settings.py
"""
import os,sys,secrets,importlib,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.update(DJANGO_DEBUG='0',DJANGO_SECRET_KEY=secrets.token_urlsafe(64),DJANGO_ALLOWED_HOSTS='news.example.com',SITE_URL='https://news.example.com',FRONTEND_URL='https://news.example.com',DB_ENGINE='mariadb',DB_NAME='offline_harness',DB_USER='offline_harness',DB_PASSWORD='offline-only-not-a-credential',DB_HOST='db.example.com',DB_SSL_CA=__file__,SECURE_HSTS_SECONDS='3600')
module=importlib.import_module('config.settings')
values={k:v for k,v in vars(module).items() if k.isupper()}
# This deliberate override permits security middleware checks WITHOUT a MariaDB driver/service.
values['DATABASES']={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
from django.conf import settings
settings.configure(**values)
import django
django.setup()
from django.core.management import call_command
from django.test import Client
call_command('check',deploy=True,fail_level='ERROR')
client=Client(HTTP_HOST='news.example.com')
assert client.get('/health/live/').status_code==301
assert client.get('/health/live/',secure=True).status_code==200
assert settings.DEBUG is False and settings.CSRF_COOKIE_SECURE and settings.SESSION_COOKIE_SECURE
assert settings.SECURE_HSTS_SECONDS==3600 and settings.SECURE_SSL_REDIRECT
print(json.dumps({'security_checks':'pass','https_redirect':'pass','secure_cookies':'pass','production_debug':False,'hsts_test_seconds':3600,'hsts_preload':False,'database':'SQLite in-memory override for security harness ONLY','MariaDB_verified':False}))
