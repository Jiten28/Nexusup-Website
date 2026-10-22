# Windows PowerShell setup and run guide

## Identity and safety

Extract the ZIP into a NEW folder. Do not extract over a different working tree or replace your Windows database.
Open the extracted `NexusUp` folder in VS Code. This export is a sandbox snapshot; it is not proven to be the
copy currently serving your Windows admin. All application source is preserved; see KNOWN_ISSUES.md.

The bundled backend/demo.sqlite3 is the reviewed sample snapshot (10 sample articles, two disabled BBC candidates,
zero imported articles/fetch runs, one inactive attribution user with an unusable password). No working admin login ships.
It was rebuilt in export staging to remove unused pages; logical table data was verified unchanged.
Do not replace an existing local/production database with this sample file. Keep private backups outside Git/ZIPs.

## Dependencies

- Python 3.12 or 3.13 with the Windows `py` launcher.
- Node.js 22+ and npm; dependencies are locked in frontend/package-lock.json.
- Local SQLite is included with Python; no external database service is required for the local setup.
- Install local Python packages from backend/requirements.txt. Optional storage packages are in requirements-storage.txt.
- MariaDB production needs a real MariaDB service and a compatible mysqlclient/native build environment.
  Gunicorn in requirements-production.txt targets Linux; do not install that production profile for local Windows development.

## 1. Backend (new PowerShell terminal at extracted NexusUp root)

```powershell
Set-Location .\backend
py -3.13 -m venv .venv
# If only Python 3.12 is installed, substitute py -3.12 above.
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
if (-not (Test-Path .\.env)) { Copy-Item .\.env.example .\.env }
# Open backend/.env in VS Code and enter private settings locally. Do not share the populated file.
```

The direct interpreter path avoids PowerShell activation/execution-policy issues. Set these LOCAL process values
so inherited values do not accidentally select another database or integration. They apply only to this terminal:

```powershell
$env:DJANGO_SETTINGS_MODULE = 'config.settings'
$env:DJANGO_DEBUG = '1'
$env:DB_ENGINE = 'sqlite'
$env:SQLITE_PATH = Join-Path (Get-Location).Path 'demo.sqlite3'
$env:DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1'
$env:SITE_URL = 'http://127.0.0.1:8000'
$env:FRONTEND_URL = 'http://127.0.0.1:5173'
$env:NEWS_FETCH_ENABLED = '0'
$env:UTILITIES_NETWORK_ENABLED = '0'
$env:TRANSLATION_PROVIDER = 'disabled'
# Generates a fresh secret into this process without printing it.
$env:DJANGO_SECRET_KEY = & .\.venv\Scripts\python.exe -c 'import secrets; print(secrets.token_urlsafe(64))'
.\.venv\Scripts\python.exe manage.py check
```

For a stable private secret, store a separately generated value in backend/.env using a private editor; process values
win over .env. The process-generated secret above changes after repeating setup, invalidating old sessions.

### Database setup: choose ONE path

A. **Included sample snapshot:** already contains migrations through news/0004. After check, inspect the plan:

```powershell
.\.venv\Scripts\python.exe manage.py showmigrations --plan
```

Do not run migrations against another project's records merely to try this export. For this new extracted copy only,
review any pending migration before explicitly applying it. Creating an admin below writes to the selected database.

B. **Fresh empty local database:** select a new unused absolute SQLITE_PATH in the terminal and/or private .env,
then intentionally initialize that new database:

```powershell
# Run only against a NEW database you chose, never an unidentified existing database.
.\.venv\Scripts\python.exe manage.py migrate
```

This creates no real articles. Optional `seed_demo` creates labeled sample articles and categories, NOT real news;
`configure_sources` creates disabled source candidates/categories. Neither is run automatically by this export.
Do not invoke either against your real database without reviewing and approving its writes.

### Create your own admin and start

```powershell
# This writes a new user to the selected local database; enter credentials interactively.
.\.venv\Scripts\python.exe manage.py createsuperuser
# --noreload avoids a second autoreloader process while identifying the active server.
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

Admin: http://127.0.0.1:8000/admin/ . No admin password is supplied in the ZIP.
If you see unexpected source flags or records, stop and verify the interpreter, project root and SQLITE_PATH.
Do not use backend/scripts/run_demo.sh for a read-only audit: it installs packages and runs migrations.

## 2. Frontend (second PowerShell terminal at extracted NexusUp root)

```powershell
Set-Location .\frontend
npm.cmd ci
$env:DEV_BACKEND_URL = 'http://127.0.0.1:8000'
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open http://127.0.0.1:5173/ . Use the SAME host spelling (`127.0.0.1`) consistently for the local workflow.
The Vite proxy forwards /api and /media. Do not set VITE_API_BASE_URL unless deliberately using a separate API origin;
review existing shell/frontend environment values if the UI contacts an unexpected server.
Django's port-8000 homepage is a separate legacy template, not the React preview.
Do not use `npm run demo` to verify live news: explicit demo mode can display labeled frontend fixtures.

## 3. Environment variable names (no private values)

backend/.env.example is a safe, correctly line-separated template. Django loads backend/.env, not root .env;
Compose separately expects root .env. Existing process variables take precedence.

- Django/site: DJANGO_DEBUG, DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, SITE_URL.
- Database: DB_ENGINE, SQLITE_PATH, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT,
  DB_CONN_MAX_AGE, DB_CONNECT_TIMEOUT, DB_READ_TIMEOUT, DB_WRITE_TIMEOUT,
  DB_TLS_REQUIRED, DB_SSL_CA, DB_SSL_CERT, DB_SSL_KEY.
- Ingestion: NEWS_FETCH_ENABLED (keep 0), NEWS_API_KEY (private; blank is fine for RSS), NEWS_API_MAX_PAGES.
- Utilities/translation: UTILITIES_NETWORK_ENABLED (keep 0), OPEN_METEO_API_KEY,
  TRANSLATION_PROVIDER (disabled), TRANSLATION_API_KEY, LIBRETRANSLATE_URL.
- Frontend/cookies: FRONTEND_URL, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS,
  CORS_ALLOW_CREDENTIALS, COOKIE_SAMESITE. Use http://127.0.0.1:5173 for the local allowed/trusted origins.
- Proxy/security: TRUST_PROXY_HTTPS, SECURE_HSTS_SECONDS, SECURE_HSTS_INCLUDE_SUBDOMAINS, SECURE_HSTS_PRELOAD.
- Assets/storage: ADS_TXT_ENABLED, MEDIA_STORAGE, MEDIA_URL, STATIC_URL; optional MEDIA_ROOT, STATIC_ROOT.
- Optional S3: AWS_STORAGE_BUCKET_NAME, AWS_S3_ENDPOINT_URL, AWS_S3_REGION_NAME, AWS_QUERYSTRING_AUTH,
  plus private credentials/host identity. S3 is not required for local setup.
- Cache/logging: CACHE_URL (private if containing credentials), API_ANON_RATE, LOG_LEVEL.
- Frontend: DEV_BACKEND_URL (Vite proxy), VITE_API_BASE_URL (optional public backend origin only).
  Never create VITE_ variables for secrets.
- Compose-only DB_ROOT_PASSWORD is private; production examples contain placeholders, not usable credentials.

MariaDB branch uses DB_ENGINE=mariadb and DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT, with TLS settings.
Production requires non-debug settings, a fresh private secret, explicit hosts and HTTPS SITE_URL. See docs/DEPLOYMENT.md.
MariaDB connectivity is NOT verified in this export. Do not start the Compose ingestion profile.

## 4. Tests and review (commands not executed for export)

Read-only Node unit/config tests, from frontend:

```powershell
node --test tests/config.test.js tests/demo.test.js
```

Django tests WRITE to an isolated test database, even if providers are mocked. Run only after confirming the
selected project/environment and approving disposable test database writes:

```powershell
# From backend, in the isolated local configuration above:
.\.venv\Scripts\python.exe manage.py test apps.news.tests_newsapi --verbosity 2
```

Do not run browser suites against an unidentified active installation: they interact with UI and generate outputs.
No test pass is claimed for packaging. ZIP CRCs, source hashes, SQLite integrity and logical data identity are verified.

## 5. News and carousel status

Keep fetching disabled; do not run fetch_news (including --dry-run, which CAN contact live feeds).
Do not change rights/trust/auto_publish flags. Manual live ingestion requires separate source-rights review and approval.
The zero-fetch and compact-carousel fixes remain proposed, not implemented. See KNOWN_ISSUES.md and CHANGELOG.md.
Reference images and preview assets are preserved; inclusion is not evidence of publication rights.
