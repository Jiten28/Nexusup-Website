# Portable deployment and operations

## 1. Supported environments and prerequisites

| Option | Required capability | Does not require |
|---|---|---|
| Static frontend + Python host | Node build locally/CI; static host with route rewrites; Python WSGI process; persistent MariaDB; media storage; host scheduler | Netlify, Docker, SSH if provider supports console/CI jobs |
| Linux VPS, primary method | Python 3.12/3.13, Node 22+, web server/TLS, MariaDB 10.5+ (11.4 LTS profile), mysqlclient system libraries, persistent disks, scheduled jobs | A particular cloud provider or Docker |
| Optional Compose | Docker Engine/Compose v2, image-build capability, disk volumes, trusted HTTPS edge, ability to execute one-off migration/backup commands | A managed database or Netlify |
| Static-only/shared PHP host | Can serve built frontend only | Cannot run the full system without a separate Python backend and database |

If there is no shell access, perform npm builds in CI/local and upload `frontend/dist/`. The Python host must offer equivalent dependency installation, WSGI configuration, migration/static-file commands and a scheduler. A conventional static host cannot run Django/MariaDB. If the host cannot supply any of these services, use a compatible backend host; do not pretend frontend functions replace them.

**Verification boundary:** React build, SQLite migrations/tests, local HTTP/browser integration and production-security settings harness were exercised. Actual MariaDB, Docker, nginx, object storage and externally hosted scheduling require the client's infrastructure and remain unverified here. Do not use this guide as evidence those services are running.

## 2. Primary non-Docker deployment

1. Select public frontend and backend origins and persistent paths. Obtain MariaDB credentials over a private channel; no credentials in Git or Vite variables.
2. Create an isolated Python environment, install backend dependencies:

```sh
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-production.txt
# Debian-family build prerequisites if mysqlclient has no wheel:
# build-essential pkg-config default-libmysqlclient-dev python3-dev
# RPM-family hosts need their equivalent MariaDB client/development packages.
```

3. Set backend environment variables in the host's secret manager/process configuration. Start from `.env.production.example` at project root; environment files are not automatically loaded by Django. POSIX shell example ONLY for an owner-controlled file with trusted shell syntax: `set -a; . /secure/nexusup.env; set +a`. Quote values and set restrictive file permissions. Never source an untrusted environment file.
4. Use `DJANGO_DEBUG=0`, a unique random secret (>=50 characters), explicit `DJANGO_ALLOWED_HOSTS`, `DB_ENGINE=mariadb`, and HTTPS `SITE_URL` (backend) and `FRONTEND_URL` (public site). Missing required production values stop startup. No SQLite fallback in production.
5. Set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. Remote database: `DB_TLS_REQUIRED=1`, `DB_SSL_CA=/secure/ca.pem`; optional `DB_SSL_CERT`/`DB_SSL_KEY` for mutual TLS. Hostname verification is enabled when a CA is supplied. Disable TLS explicitly only for an isolated local/socket or private Compose network, not for an untrusted network. No database ports should be public.
6. Back up the existing database/media first. Review migrations; do not seed or reset:

```sh
python manage.py check
python manage.py showmigrations
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy --fail-level ERROR
# Host command or equivalent service unit/process manager:
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 60 --access-logfile -
```

Run Gunicorn under a non-root service account and host supervisor. Do not use `runserver` for production. Choose worker count based on memory/load, not this example alone. Do not use development demo launcher in deployment.

7. Frontend build independently:

```sh
cd frontend
npm ci
# Same origin: leave VITE_API_BASE_URL empty.
# Separate origin: export VITE_API_BASE_URL=https://api.example.com
npm run build
```

Upload the **contents** of `dist/` to the static document root. `VITE_API_BASE_URL` is the backend origin, without `/api` or a trailing slash. This is public build-time configuration; changing it requires rebuilding the frontend. No production bundle should point to localhost. No server key belongs in a `VITE_*` variable.

8. Reverse proxy API/admin/health/RSS/sitemap/robots/ads to Gunicorn. Serve `/assets/` from frontend `dist/assets`, `/static/` from `STATIC_ROOT`, `/media/` from persistent `MEDIA_ROOT`, and `/wp-content/uploads/` as the same media alias if preserving WordPress URLs. Set missing static/media resources to 404; never send them to React. Serve the SPA fallback only for frontend routes. `docs/deploy/nginx-container.conf` shows routing responsibilities, but its `backend` upstream and paths are the Compose profile; adapt these for non-container paths.
9. Terminate TLS at the approved host edge. Set `TRUST_PROXY_HTTPS=1` only when Django is reachable exclusively through a proxy that overwrites `X-Forwarded-Proto`. A standalone internet-accessible backend must not trust spoofable forwarded headers. For a TLS-terminating nginx, set that header from `$scheme`. The Compose internal nginx hardcodes `https` because it is loopback-bound behind a trusted TLS edge; never expose that internal HTTP port publicly.

## 3. Same-origin and separate-origin profiles

### Same origin (recommended)

Serve React at `https://news.example.com`; reverse-proxy `/api/`, `/admin/`, `/health/`, `/feed/`, sitemap/robots/ads to Django. Leave `VITE_API_BASE_URL` empty. Set `SITE_URL` and `FRONTEND_URL` to that public origin; add it to `CSRF_TRUSTED_ORIGINS`. No cross-origin wildcard or CORS configuration is needed. The Vite development proxy and local verification proxy exercise this arrangement without production TLS/nginx.

### Separate origins

Frontend `https://www.example.com`; Django `https://api.example.com`:

- Build `VITE_API_BASE_URL=https://api.example.com`.
- Backend `SITE_URL=https://api.example.com`, `FRONTEND_URL=https://www.example.com`; RSS/sitemap story links use `FRONTEND_URL`.
- `DJANGO_ALLOWED_HOSTS=api.example.com`.
- `CORS_ALLOWED_ORIGINS=https://www.example.com`; `CSRF_TRUSTED_ORIGINS=https://www.example.com`.
- `CORS_ALLOW_CREDENTIALS=1` for contact/comment/translation operations. Public GETs omit cookies. Private form flow obtains `/api/csrf/` and includes its masked token and backend cookie; CSRF is not disabled.
- Same-site HTTPS subdomains generally work with `COOKIE_SAMESITE=Lax`. For truly cross-site hosts (e.g. Netlify + unrelated Python host), browser third-party-cookie policy may block forms even with correct CORS. Prefer a same-site API domain or same-origin proxy. If the approved environment supports cross-site cookies, set `COOKIE_SAMESITE=None` only with secure HTTPS cookies; still test in actual target browsers. Do not weaken CSRF or allow all origins.

Django tests exercised an allowed Origin, a denied Origin and CSRF success/failure. Real-browser different-domain TLS/cookie behavior still needs hosting verification.

## 4. Static files, persistent media and object storage

`STATIC_URL`, `STATIC_ROOT`, `MEDIA_URL`, `MEDIA_ROOT` are configurable. Whitenoise serves collected Django static resources; the web server may serve the same root instead. Vite assets are independent and must not be copied into Django's static source tree. Existing book logo is deliberately also in `frontend/public/` so the frontend can run on an independent static host.

Use a persistent media directory/volume that survives releases. Preserve the seven supplied `YYYY/MM/...` paths byte-for-byte and reference the same directory through both media and optional WordPress aliases. Do not put a new empty mount over populated uploads without copying/restoring them first. Article image paths resolve through Django's storage API. Remote images are referenced only when the source allows images and its explicit hostname allowlist matches; they are not scraped/downloaded.

Optional S3-compatible object storage: install `backend/requirements-storage.txt`; set `MEDIA_STORAGE=s3`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME` and optional `AWS_S3_ENDPOINT_URL`. Supply standard AWS credentials or host identity privately. `AWS_QUERYSTRING_AUTH=1` is the private/signed default; make public access a deliberate bucket decision. Migrate existing file keys unchanged; test a real object, permissions, URL expiry and upload lifecycle before switching. Object storage was not connected or tested. Never execute uploaded content; web-server media should be data-only. No public upload API is added; current manual editorial media continues using safe relative paths.

## 5. Optional Compose topology

No Docker executable/service was available in the implementation environment. Treat this as a supplied, reviewed profile, not a tested deployment.

```sh
cp .env.production.example .env
# Fill unique secrets and actual hostnames privately. Ensure project permissions.
docker compose config --quiet
docker compose build
docker compose up -d db
# First deployment or approved upgrade: backup first, inspect migration plan.
docker compose run --rm backend python manage.py migrate --plan
docker compose run --rm backend python manage.py migrate --noinput
docker compose run --rm backend python manage.py collectstatic --noinput
docker compose run --rm backend python manage.py check --deploy --fail-level ERROR
docker compose up -d backend web
```

Place the site's trusted HTTPS edge in front of `127.0.0.1:8080`, forwarding the correct Host. MariaDB uses its own named persistent volume; media and collected Django static files have independent named volumes. The app image excludes SQLite, secrets and historical recovery archives; it does not import sample records into production. Migrations are deliberate one-off jobs, not database reset/seed actions in the startup command. Ensure UID 10001 can write the media/static volumes (rootless/container host ownership may require operator initialization). Never run `docker compose down -v` against production.

## 6. Ingestion and editorial controls

All outbound news collection is disabled until approved. Existing two candidate BBC sources remain disabled and rights-unconfirmed. No current feed or API license is implied by this package.

1. In protected Django admin add/edit NewsSource, choose `rss` or `newsapi`, default category, category map, >=5-minute source interval, and terms/reuse notes.
2. Verify rights and allowed excerpts/images. Confirm rights, enable the source. **Trust** and **auto-publish** are independent. Both must be true and the provider date valid for automatic publication. Undated, untrusted or approval-required imports remain drafts. Future-dated content remains non-public until publication time. Imports never choose featured placement.
3. RSS/Atom: public HTTPS feed URL. NewsAPI: official `/v2/top-headlines` or `/v2/everything` URL with approved search parameters; put the key only in `NEWS_API_KEY` on the backend. Never put it in the database source URL. Official adapter reads metadata/excerpts/links, not full article content. It retains publisher name, actual date and approved image reference. Requests are bounded to 100 entries per source pass; this is a rolling feed poll, not a guaranteed full archive/backfill. Query country/language coverage and commercial rights depend on the current provider plan; do not assume India availability from a static country example. Check current endpoint docs and plan terms: https://newsapi.org/docs/endpoints/top-headlines and https://newsapi.org/terms.
4. `NEWS_FETCH_ENABLED=1` is necessary to run the command. A dry run fetches/normalizes but creates no articles or fetch logs:

```sh
python manage.py fetch_news --source SOURCE_ID --dry-run
python manage.py fetch_news --source SOURCE_ID
```

5. Run independently of site traffic using host scheduler, cron or the optional Compose `ingestion` profile. Example cron (service user has configured environment):

```cron
*/15 * * * * /srv/nexusup/backend/.venv/bin/python /srv/nexusup/backend/manage.py fetch_news >> /var/log/nexusup-ingestion.log 2>&1
```

Cron does not automatically load application env variables. Use the host secret/env mechanism or a privately owned launcher; never put credentials in crontab. Rotate logs. Minimum interval claims prevent overlapping jobs for one source; URL/title uniqueness also protects concurrent article creation. GET fetches have bounded retries for transient network/502/503/504 failures, timeout and size caps. 429 is not retried immediately; a source remains deferred until its interval. Tune intervals to provider limits. Errors are sanitized in FetchRun/admin; existing stored articles remain available.

Optional Compose scheduler: **only after permissions/configuration verification**, `docker compose --profile ingestion up -d scheduler`. Loop runs a backend management command, not frontend visits. Failures are logged; the loop continues after 15 minutes.

### Required scheduler verification, not just an example file

With browser/site traffic stopped, record the source `last_attempt_at`, `next_fetch_at`, article count and latest FetchRun. Wait for two configured intervals. Confirm process/scheduler logs and two actual run attempts (successful or safely recorded provider failures); verify expected article dedup and review/publication status. Disable a source and verify no subsequent fetch. Restart/redeploy and confirm persistent content/media and scheduler recovery. Alert on missing/stale FetchRun. This requires the host scheduler and authorized provider and has **not** been performed here.

## 7. Utilities, translation, caching and abuse controls

Calculator, units, world clock and calendar run locally. Currency/weather require `UTILITIES_NETWORK_ENABLED=1`. Frankfurter reference-rate and Open-Meteo adapters have caching/timestamps and honest unavailable states; commercial weather may require `OPEN_METEO_API_KEY`. Review current commercial terms and attribution before enabling. Geolocation is user-triggered only; manual city/coordinates are retained.

Translation is opt-in: `TRANSLATION_PROVIDER=google` with backend `TRANSLATION_API_KEY`, or `libre` with an approved `LIBRETRANSLATE_URL` and key if needed. Existing Google Cloud v2/Libre adapters list the provider's actual languages. No universal coverage guarantee. Original English remains available; some labels and stories outside the bounded translation corpus remain English. Translated text uses React text nodes, never HTML injection. Translation uses a bounded server-derived public corpus, not arbitrary client text. Billing/quotas and provider processing/privacy must be approved. No paid service was activated.

Current locmem caching/throttles are suitable for local/single-process evaluation, not a global distributed quota. **Before public multiworker launch**, configure a host-provided Redis service with private `CACHE_URL=redis://...` (supported through Django RedisCache; production requirements include the client), or add reverse-proxy shared rate limits, and account-level provider quotas. Do not claim the included per-process limits prevent distributed abuse. Do not enable paid translation publicly without shared quotas. Forms remain CSRF-protected and comments moderated.

## 8. Health, logs, backups, rollout and rollback

- `/health/live/`: process liveness, no DB query.
- `/health/ready/`: database connectivity check; sanitized 503 on failure. It does not verify every table, media, provider or scheduler.
- Set `LOG_LEVEL` (default INFO). Root logs go to stdout; host must retain/rotate them. Do not enable verbose outbound request logging with API-key query strings.
- Run `python manage.py check --deploy --fail-level ERROR` using actual production settings and installed mysqlclient. Production-check harness results do not replace actual MariaDB connectivity/migrations. `security.W021` remains an intentional warning because HSTS preload is opt-in (`SECURE_HSTS_PRELOAD=0`). Do not enable preload until all relevant subdomains permanently support HTTPS and the owner approves browser-list submission. The default includes subdomains, so review that policy with the owner as well.
- Follow `database/backup-restore.md` for DB + media backups. Back up before migrations and verify a restore in isolation.
- Release frontend and backend compatibly; keep last known-good image/build and immutable release ID. Apply additive migrations in a maintenance window if necessary. For rollback, prefer reverting code only when schema remains compatible. Otherwise restore the matched DB/media snapshot with approved downtime; never blindly reverse migrations on live data.

Smoke-test home, direct article refresh, unknown story 404, categories/search, Load More, all footer routes, admin login (existing auth), RSS/sitemap links, CSRF forms, media missing/valid paths and health. Restart services; confirm articles/media survive. For separate origins test allowed/denied Origin and target-browser cookies. For SPA/static hosts ensure `/api/missing`, `/admin/`, `/static/missing`, `/media/missing` never return the React HTML fallback.

## 9. Optional Netlify preview and current 404

Local verified configuration: root `netlify.toml`, base `frontend`, build `npm run build`, publish `dist`; real build output contains `index.html`, hashed CSS/JS, logo and `_redirects`. Redirects cover explicit frontend route families, not a catch-all that swallows `/api`, admin, RSS or files. Netlify hosts only the frontend. Set public `VITE_API_BASE_URL` to a reachable HTTPS Django origin before building. Backend RSS/admin links use that origin; they are not Netlify runtime functions.

The original package had no React/package.json/dist and could not serve a conventional Django application from static hosting. That is a credible architecture/publish mismatch, **not a proven root cause of the particular historical deploy**. Latest remote deploy logs, configured repository revision, site UI overrides and publishing metadata were unavailable. The public URL was read-only checked again; see `docs/verification/netlify-live-status.txt`. No remote settings/deploy/DNS changes were made and no live fix is claimed.

Operator verification: inspect actual latest deploy log and commit; confirm Netlify configuration is from that revision; clear conflicting UI base/publish settings; confirm build completes and inspect deployed files for root index.html and hashed assets. Test the deployed homepage plus a valid `/story/<slug>/` refresh; verify API calls hit the approved backend. Ensure reserved backend paths are not rewritten to HTML; link RSS/admin to the backend origin. If using another static host, reproduce these routing rules with its native web-server configuration, without rewriting application logic.

## 10. Launch gates still requiring the client

Real MariaDB migrations/restore/TLS test; production domain and TLS edge; persistent media or object store; host scheduler verification; provider rights/keys/coverage; shared throttles/quotas; legal identity/privacy/retention/editorial review; media licenses; secure admin onboarding; review preview noindex/robots and intentional ads-disabled state. These are explicit blockers to calling the package production-deployed, not hidden defaults.
