import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
BASE_DIR = Path(__file__).resolve().parent.parent
from .environment import load_project_environment
load_project_environment(BASE_DIR / '.env')

def env_list(name, default=''):
    return [value.strip() for value in os.getenv(name, default).split(',') if value.strip()]

def env_int(name, default, minimum=None, maximum=None):
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ImproperlyConfigured(f'{name} must be an integer.') from exc
    if minimum is not None and value < minimum:
        raise ImproperlyConfigured(f'{name} must be at least {minimum}.')
    if maximum is not None and value > maximum:
        raise ImproperlyConfigured(f'{name} must be at most {maximum}.')
    return value

DEBUG = os.getenv('DJANGO_DEBUG', '0') == '1'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('Set DJANGO_SECRET_KEY for non-demo use.')
    SECRET_KEY = 'local-demo-only-not-for-production-7478f562'
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1],testserver')
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','django.contrib.sitemaps','apps.news.apps.NewsConfig','rest_framework','corsheaders']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','corsheaders.middleware.CorsMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','apps.news.context.site']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite')
if DB_ENGINE == 'mariadb':
    required = ['DB_NAME','DB_USER','DB_PASSWORD','DB_HOST']
    if any(not os.getenv(key) for key in required):
        raise ImproperlyConfigured('MariaDB requires DB_NAME, DB_USER, DB_PASSWORD and DB_HOST.')
    DATABASES = {'default':{'ENGINE':'django.db.backends.mysql','NAME':os.environ['DB_NAME'],'USER':os.environ['DB_USER'],'PASSWORD':os.environ['DB_PASSWORD'],'HOST':os.environ['DB_HOST'],'PORT':os.getenv('DB_PORT','3306'),'CONN_MAX_AGE':env_int('DB_CONN_MAX_AGE',60,0,3600),'OPTIONS':{'charset':'utf8mb4','init_command':"SET sql_mode='STRICT_TRANS_TABLES'",'isolation_level':'read committed','connect_timeout':env_int('DB_CONNECT_TIMEOUT',10,1,120),'read_timeout':env_int('DB_READ_TIMEOUT',30,1,600),'write_timeout':env_int('DB_WRITE_TIMEOUT',30,1,600)}}}
elif DB_ENGINE == 'sqlite' and DEBUG:
    DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':Path(os.getenv('SQLITE_PATH') or BASE_DIR/'demo.sqlite3')}}
else:
    raise ImproperlyConfigured('Production requires DB_ENGINE=mariadb. SQLite is demo-only.')
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'en-in'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
STATIC_URL = os.getenv('STATIC_URL','/static/')
STATICFILES_DIRS = [BASE_DIR/'static']
STATIC_ROOT = Path(os.getenv('STATIC_ROOT',str(BASE_DIR/'staticfiles')))
MEDIA_URL = os.getenv('MEDIA_URL','/media/')
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT',str(BASE_DIR/'media')))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
SITE_URL = os.getenv('SITE_URL','http://127.0.0.1:8000').rstrip('/')
if not DEBUG and (not SITE_URL.startswith('https://') or '127.0.0.1' in SITE_URL):
    raise ImproperlyConfigured('Production requires an approved HTTPS SITE_URL.')
ADS_TXT_ENABLED = os.getenv('ADS_TXT_ENABLED','0') == '1'
CACHES = {'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'nexusup-demo'}}
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Start at zero until HTTPS is verified on every production hostname.
    # Increase deliberately; do not enable includeSubDomains/preload without owner approval.
    SECURE_HSTS_SECONDS = env_int('SECURE_HSTS_SECONDS',0,0,63072000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS','0') == '1'
    SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD','0') == '1'

# External integrations are explicitly opt-in; no outbound request occurs on homepage render.
NEWS_FETCH_ENABLED = os.getenv('NEWS_FETCH_ENABLED','0') == '1'
UTILITIES_NETWORK_ENABLED = os.getenv('UTILITIES_NETWORK_ENABLED','0') == '1'
OPEN_METEO_API_KEY = os.getenv('OPEN_METEO_API_KEY','')
TRANSLATION_PROVIDER = os.getenv('TRANSLATION_PROVIDER','disabled')
TRANSLATION_API_KEY = os.getenv('TRANSLATION_API_KEY','')
LIBRETRANSLATE_URL = os.getenv('LIBRETRANSLATE_URL','http://127.0.0.1:5000').rstrip('/')
TRANSLATION_TIMEOUT = env_int('TRANSLATION_TIMEOUT',15,1,60)

# Portable origin, storage, database TLS and health settings.
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173' if DEBUG else SITE_URL).rstrip('/')
# React is canonical. The retained template application is an explicit compatibility mode.
PUBLIC_FRONTEND_MODE = os.getenv('PUBLIC_FRONTEND_MODE', 'react')
if PUBLIC_FRONTEND_MODE not in ('react', 'legacy'):
    raise ImproperlyConfigured('PUBLIC_FRONTEND_MODE must be react or legacy.')
from urllib.parse import urlsplit
_frontend_origin = urlsplit(FRONTEND_URL)
if (_frontend_origin.scheme not in (('http', 'https') if DEBUG else ('https',))
        or not _frontend_origin.netloc or _frontend_origin.username or _frontend_origin.password
        or _frontend_origin.path or _frontend_origin.query or _frontend_origin.fragment):
    raise ImproperlyConfigured('FRONTEND_URL must be an HTTP(S) origin without credentials, path, query or fragment.')
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS','0') == '1'
if os.getenv('TRUST_PROXY_HTTPS','0') == '1':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO','https')
NEWS_API_KEY = os.getenv('NEWS_API_KEY','')
NEWS_API_MAX_PAGES = env_int('NEWS_API_MAX_PAGES',1,1,5)
if DB_ENGINE == 'mariadb':
    ssl_options = {}
    for env, key in [('DB_SSL_CA','ca'),('DB_SSL_CERT','cert'),('DB_SSL_KEY','key')]:
        if os.getenv(env): ssl_options[key] = os.environ[env]
    if os.getenv('DB_SSL_CA'): ssl_options['check_hostname'] = True
    if not DEBUG and os.getenv('DB_TLS_REQUIRED','1')=='1' and not os.getenv('DB_SSL_CA'):
        raise ImproperlyConfigured('Production MariaDB requires DB_SSL_CA, or explicitly DB_TLS_REQUIRED=0 for an isolated local database network.')
    if os.getenv('DB_SSL_CA') and not Path(os.environ['DB_SSL_CA']).is_file():
        raise ImproperlyConfigured('DB_SSL_CA must name a readable CA certificate file.')
    for key in ('DB_SSL_CERT','DB_SSL_KEY'):
        if os.getenv(key) and not Path(os.environ[key]).is_file():
            raise ImproperlyConfigured(f'{key} must name a readable certificate file.')
    if ssl_options:
        DATABASES['default']['OPTIONS']['ssl'] = ssl_options
        if os.getenv('DB_SSL_CA'): DATABASES['default']['OPTIONS']['ssl_mode'] = 'VERIFY_IDENTITY'
if not DEBUG and not os.getenv('DJANGO_ALLOWED_HOSTS'):
    raise ImproperlyConfigured('Set explicit DJANGO_ALLOWED_HOSTS in production.')
if not DEBUG and (len(SECRET_KEY)<50 or SECRET_KEY.startswith(('local-demo','REPLACE_'))):
    raise ImproperlyConfigured('Production secret must be at least 50 characters, independently generated.')
MEDIA_STORAGE = os.getenv('MEDIA_STORAGE','local')
STORAGES = {'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
if MEDIA_STORAGE == 's3':
    INSTALLED_APPS += ['storages']
    STORAGES['default'] = {'BACKEND':'storages.backends.s3.S3Storage'}
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL') or None
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME') or None
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = os.getenv('AWS_QUERYSTRING_AUTH','1')=='1'
elif MEDIA_STORAGE != 'local':
    raise ImproperlyConfigured('MEDIA_STORAGE must be local or s3')
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.AllowAny'],
    'DEFAULT_AUTHENTICATION_CLASSES':[],
    'DEFAULT_RENDERER_CLASSES':['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_THROTTLE_CLASSES':['rest_framework.throttling.AnonRateThrottle'],
    'DEFAULT_THROTTLE_RATES':{'anon':os.getenv('API_ANON_RATE','120/minute')},
}
LOGGING = {'version':1,'disable_existing_loggers':False,'handlers':{'console':{'class':'logging.StreamHandler'}},'root':{'handlers':['console'],'level':os.getenv('LOG_LEVEL','INFO')}}

SESSION_COOKIE_SAMESITE = os.getenv('COOKIE_SAMESITE','Lax')
CSRF_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
if SESSION_COOKIE_SAMESITE == 'None' and DEBUG:
    raise ImproperlyConfigured('SameSite=None requires a production HTTPS arrangement')
# A host-provided shared cache makes form/provider throttles consistent across workers.
# Install the production Redis client only when using this profile.
if os.getenv('CACHE_URL'):
    CACHES = {'default':{'BACKEND':'django.core.cache.backends.redis.RedisCache','LOCATION':os.environ['CACHE_URL'],'TIMEOUT':300}}
