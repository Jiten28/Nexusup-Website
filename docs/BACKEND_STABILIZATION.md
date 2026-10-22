# NexusUp backend stabilization record

## Scope and preservation

This pass changed Django/backend configuration, ingestion tests, environment templates and operational documentation only. It did not modify React, frontend dependencies, Django templates, Django static CSS/JS, assets, layout, routing or visual behavior. The working tree was already dirty when this pass began; all unrelated and prior frontend changes were preserved.

## Reproduced defects and fixes

| Defect | Root cause | Implemented fix |
|---|---|---|
| A local `backend/.env` did not affect Django | Settings read only `os.environ`; the example incorrectly said to export values manually | `python-dotenv` now loads exactly `backend/.env` before settings are evaluated, with `override=False`; process/host secrets always win |
| NewsAPI missing-key output was generic | Adapter failure was wrapped into one generic ingestion error | Added explicit safe diagnostics for missing key, 401/403, 429, timeout/outage, invalid JSON, malformed shape and other HTTP failures |
| Provider key appeared in the URL | Adapter used an `apiKey` query parameter | Credential now uses `X-Api-Key`; cross-host credential redirects are blocked; stored errors and logs contain only safe diagnostics |
| NewsAPI fetched at most one implicit page with no configurable policy | Adapter forced only `pageSize=100` | Added bounded `NEWS_API_MAX_PAGES` (1–5, default 1), explicit page numbers and stop conditions |
| Dry-run output did not show dedup impact | It returned only raw eligible count | Dry-run now reports eligible, would-import and skipped and creates no user, article, source timestamp or FetchRun |
| A mid-batch failure could leave partial imports | Each article had its own transaction | A source batch now uses an outer atomic transaction; duplicate races retain inner savepoints |
| HSTS was enabled for a year and all subdomains by default | Production settings hard-coded an unverified domain policy | HSTS defaults to zero/no subdomains/no preload and must be enabled gradually after domain verification |
| MariaDB options lacked bounded connection/read/write timeouts | Only connection reuse and strict SQL mode were configured | Added validated timeouts, read-committed isolation, CA/certificate path validation and documented TLS boundary |
| Public DRF reads had no application throttle | REST defaults had no throttle classes | Added an environment-configurable anonymous rate (`API_ANON_RATE`, default `120/minute`); Redis/reverse-proxy sharing is still required for multi-worker enforcement |
| Historical Netlify 404 | Historical static-host/project mismatch was plausible, but remote evidence was unavailable | Repository configuration is already correct; current live homepage and SPA route return 200. Exact remote change remains unknown |

## Local development — Windows PowerShell

```powershell
cd C:\path\to\NexusUp\backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit backend\.env locally. It is gitignored.
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate
python manage.py test
```

To avoid a file, set process variables directly:

```powershell
$env:DJANGO_DEBUG = "1"
$env:DB_ENGINE = "sqlite"
$env:DJANGO_SECRET_KEY = "local-only-secret"
$env:NEWS_FETCH_ENABLED = "0"
python manage.py check
```

Safe NewsAPI setup and dry run:

```powershell
# Store the real value only in backend\.env or the host secret manager:
# NEWS_API_KEY=<private key>
# NEWS_FETCH_ENABLED=1
# NEWS_API_MAX_PAGES=1
python manage.py fetch_news --source 123 --dry-run
# Run without --dry-run only after inspecting the plan and source rights:
python manage.py fetch_news --source 123
```

The source must use adapter `newsapi`, an official `https://newsapi.org/v2/top-headlines` or `/v2/everything` URL without `apiKey`, and must be enabled with rights confirmed. Fetching remains disabled by default. No scheduler is enabled automatically.

## Production requirements and verification boundary

- Use host/process secrets where possible. A private `backend/.env` works in production but is not preferred; environment values override it.
- Require `DJANGO_DEBUG=0`, a generated secret of at least 50 characters, explicit allowed hosts, HTTPS site URL, MariaDB settings and approved CSRF/CORS origins.
- Remote MariaDB requires a real CA file unless the owner explicitly approves `DB_TLS_REQUIRED=0` for an isolated local/private database network.
- Run backup, `showmigrations`, `migrate --plan`, migrations, `collectstatic`, actual production `check --deploy`, readiness and restore verification in the real environment.
- `MEDIA_STORAGE=local` requires a persistent mounted `MEDIA_ROOT`. Optional S3 support remains unverified without provider credentials.
- Configure private Redis through `CACHE_URL` or enforce shared reverse-proxy quotas before multi-worker/public launch.
- Scheduler jobs need the same secret environment as the app. The per-source database claim prevents overlap, but operators must monitor FetchRun freshness and provider quotas.
- MariaDB, object storage, Redis, scheduler execution and a live NewsAPI credential were not available locally and are not claimed as verified.

## Database operations

`database/backup-restore.md` is the authoritative backup/restore procedure. Before a release:

1. Back up MariaDB and media together.
2. Record checksums, release ID and current migration revision.
3. Run `python manage.py migrate --plan`.
4. Apply only reviewed migrations.
5. Roll back code only when the schema stays compatible; otherwise restore the matched database/media snapshot in an approved maintenance window.

SQLite is supported only with `DJANGO_DEBUG=1`. It is tested locally, including forward migration into a temporary database. SQLite results do not establish MariaDB production readiness.
Set `SQLITE_PATH` to an absolute disposable path for an isolated migration drill; otherwise development uses `backend/demo.sqlite3`.

## Verification matrix

- Baseline before this pass: `check` passed, `makemigrations --check --dry-run` reported no changes, and all 63 existing tests passed.
- Final Django verification: `check` passed; migration consistency reported no changes; all 78 tests passed in 1.201 seconds.
- Targeted post-dependency-upgrade verification: all 15 NewsAPI/configuration tests passed.
- Mocked NewsAPI tests: success, disabled fetch, missing key, 401/403, 429, timeout/outage, invalid JSON, unexpected shape, empty/malformed results, attribution/date/URL handling, repeated-run dedup, bounded pagination, dry-run, transaction rollback and secret redaction are covered.
- Real NewsAPI request: not run; no credential was supplied.
- Real NewsAPI database ingestion: not run; no credential/approved live source was supplied.
- SQLite database ingestion: covered using mocked provider responses.
- Temporary SQLite migration drill: all migrations applied; `news.0004` reversed to `0003` and reapplied; `PRAGMA integrity_check` returned `ok`; no foreign-key violations.
- Production-settings harness: passed HTTPS redirect, secure-cookie and debug-off assertions using the actual settings module, but deliberately substituted in-memory SQLite after settings import. It emitted only the expected HSTS include-subdomains/preload warnings. It is not a MariaDB connectivity claim.
- Static files: `collectstatic` produced 621 files in a disposable directory.
- Dependency consistency: `pip check` reported no broken requirements.
- Dependency audit: the first audit found `PYSEC-2026-2270` in `python-dotenv 1.1.1`; the dependency was upgraded to `1.2.2`, and the repeated `pip-audit -r backend/requirements.txt` reported no known vulnerabilities.
- Frontend regression only: all 8 existing Node tests passed; before/after hashes for all `frontend/`, `backend/static/` and `backend/templates/` files were identical.
- Live Netlify: read-only HTTP verification succeeded; see `docs/verification/netlify-live-status.txt`.
- MariaDB: configuration reviewed only; no server/credentials were supplied.

## Commands executed

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 1
python -m pip check
python -m pip_audit -r backend/requirements.txt --progress-spinner off
python manage.py migrate --noinput                    # disposable SQLite path
python manage.py migrate --plan                      # disposable SQLite path
python manage.py migrate news 0003 --noinput         # reversibility drill
python manage.py migrate news 0004 --noinput
python tests/verify_production_settings.py
python manage.py collectstatic --noinput              # disposable STATIC_ROOT
npm test                                              # frontend regression only
```

The first attempt with the system Python failed before execution because Django was not installed; verification then used the existing project-compatible virtual environment at `/data/nexusup-audit/.venv`. A first temporary dotenv smoke command was misconfigured because `DJANGO_SETTINGS_MODULE` was omitted; no application test was claimed from it. The corrected smoke test proved that `backend/.env` loads and that a process-level value wins, then removed the temporary file.

## Files changed by this stabilization pass

- `backend/config/environment.py`
- `backend/config/settings.py`
- `backend/apps/news/network.py`
- `backend/apps/news/ingestion.py`
- `backend/apps/news/management/commands/fetch_news.py`
- `backend/apps/news/tests_newsapi.py`
- `backend/tests/verify_production_settings.py`
- `backend/requirements.txt`
- `backend/.env.example`
- `.env.production.example`
- `docs/DEPLOYMENT.md`
- `docs/HANDOVER.md`
- `docs/BACKEND_STABILIZATION.md`
- `docs/verification/netlify-live-status.txt`

No migration was required for these fixes.