"""In-memory backend suite; deny non-loopback socket connections."""
import os,sys,socket,ipaddress
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.update(DJANGO_SETTINGS_MODULE='config.settings',DJANGO_DEBUG='1',DB_ENGINE='sqlite',SQLITE_PATH=':memory:',NEWS_FETCH_ENABLED='0',PYTHONDONTWRITEBYTECODE='1')
import django;django.setup()
original=socket.socket.connect;denied=[]
def local_only(self,address):
    try:allowed=isinstance(address,tuple) and ipaddress.ip_address(address[0]).is_loopback
    except ValueError:allowed=False
    if not allowed:
        denied.append(True);raise AssertionError('External network is prohibited in regression tests')
    return original(self,address)
from django.test.runner import DiscoverRunner
with patch('socket.socket.connect',new=local_only):
    failures=DiscoverRunner(verbosity=1).run_tests(['apps.news'])
print('EXTERNAL_CONNECTION_ATTEMPTS',len(denied));print('LOCAL_HTTP_FIXTURE_ONLY',True)
raise SystemExit(bool(failures or denied))
