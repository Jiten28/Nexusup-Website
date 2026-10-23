"""Verification-only GET server for an existing SQLite snapshot; never a production server."""
import os,sys
from pathlib import Path
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))
os.environ.update(DJANGO_SETTINGS_MODULE='config.settings',DJANGO_DEBUG='1',DB_ENGINE='sqlite',NEWS_FETCH_ENABLED='0',UTILITIES_NETWORK_ENABLED='0',TRANSLATION_PROVIDER='disabled',MEDIA_STORAGE='local',DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1,testserver',PUBLIC_FRONTEND_MODE='react',FRONTEND_URL='http://localhost:5173',PYTHONDONTWRITEBYTECODE='1',SQLITE_PATH=':memory:')
from django.conf import settings
# Use only an explicit, existing SQLite snapshot. Do not use immutable mode for a live database.
snapshot=Path(os.environ.get('QA_SQLITE_PATH',str(BACKEND/'demo.sqlite3'))).resolve()
if not snapshot.is_file():
    raise SystemExit('QA_SQLITE_PATH must identify an existing SQLite snapshot; no database is created.')
settings.DATABASES['default'].update(NAME=snapshot.as_uri()+'?mode=ro',OPTIONS={'uri':True})
import django;django.setup()
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from wsgiref.simple_server import make_server,WSGIServer,WSGIRequestHandler
from socketserver import ThreadingMixIn
app=StaticFilesHandler(get_wsgi_application())
def readonly(environ,start_response):
 if environ['REQUEST_METHOD'] not in ('GET','HEAD','OPTIONS'):
  start_response('405 Method Not Allowed',[('Content-Type','text/plain')]);return [b'Read-only verification server']
 return app(environ,start_response)
class Server(ThreadingMixIn,WSGIServer):daemon_threads=True
class Quiet(WSGIRequestHandler):
 def log_message(self,*args):pass
print('Read-only SQLite verification server on 127.0.0.1:8000',flush=True)
make_server('127.0.0.1',8000,readonly,server_class=Server,handler_class=Quiet).serve_forever()
