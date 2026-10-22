# NexusUp implementation handover

## Outcome and limits

The supplied enhanced Django project was migrated incrementally into a portable React/Vite + Django/DRF application. This is a **locally verified implementation and deployment package**, not a claim that a client's production environment is deployed or fully accepted. Original sample records/media and migration history are preserved. No fabricated live news or provider credentials were added.

**Live Netlify now returns the deployed React shell with HTTP 200** for the homepage and `/stories`; a missing asset returns 404 as expected. The historical 404 is no longer reproducible, but remote deploy logs and the configured repository revision remain unavailable, so the exact external action that changed the state is unknown. Nothing was deployed or changed in Netlify/DNS during backend stabilization. See `docs/BACKEND_STABILIZATION.md` and `docs/verification/netlify-live-status.txt`.

## Implemented

### Structure and retained backend

- One existing Django project, moved to `backend/`; original app lives in `backend/apps/news`. The historical app label remains `news`, preserving database table names and migration dependencies. Categories/sources stay in that app instead of introducing redundant apps/table migrations just to resemble a target tree.
- `frontend/` contains the new public React application, shared components, page components, translation context, API/preference services, styles and assets.
- `database/` contains service/migration/backup documentation, not the production database.
- `docs/` contains the current audit, handover, deployment and exact file-change reports. Earlier documentation, deployment samples and superseded browser scripts are retained under `docs/archive/` and are not current operational instructions.
- Existing Django templates/routes remain as a fallback and compatibility surface. Production profiles serve React for public routes, and Django for API/admin/RSS/sitemap/health and backend static resources. A separate-origin frontend links backend-owned endpoints to the configured backend origin.
- The supplied `demo.sqlite3` was copied, not reset or reseeded; additive migrations were applied to the working copy. Original input archive remains unchanged outside this package. The older embedded recovery archive is retained. See `verification/preservation.json` and the source hashes in the file manifest.

### React interface and consolidation

- **Exactly one horizontal image-headline carousel**, manual by default, optional 6-second auto-advance, previous/next, Play/Pause, hover and keyboard-focus pause, reduced-motion handling and bounded horizontal scrolling. No cloned focus targets, vertical slider or separate scrolling ticker.
- The previous vertical image-slider and separate continuous marquee were consolidated in both the React UI and legacy fallback. Their obsolete JS initializers were removed. The old editor-pick repeat section has no repeated stories; React does not render that extra section.
- Centered primary editorial story with two supporting stories on each side on wide screens. Primary story is first in DOM/screen-reader order, with responsive CSS placement.
- Latest News uses 12-record backend batches and **Load More**, not infinite scrolling. It deduplicates appended records and hides the control at the end. Home carousel/feature/latest article IDs are disjoint. The ten-record sample dataset is intentionally not padded with invented stories; the homepage can have a sparse latest section after exclusions. More published database records fill the grid naturally.
- Responsive 4/3/2/1-column grid; search, category routes, direct article refresh, article details, related stories, comments, save/copy-link, footer routes, loading/empty/error/missing-image states.
- Original book logo, identity and media retained. Dark-mode logo has a neutral backing, not inverted publisher imagery.
- Ocean Blue, Vibrant Violet, Emerald, Sunset; light/dark are independently persisted with the existing preference keys. All eight combinations tested; body/muted/accent foreground pairs measured >=4.5:1 against their surfaces.
- Device-local date/time, language selector and all six original widgets retained. Calculator/units/calendar/world clock are local; currency/weather/translation are explicitly unavailable when unconfigured rather than returning made-up values. Weather requests location only after an action, with city/coordinates alternatives. The original safe calculator/parser and widget implementations are reused in a React lifecycle shell rather than replaced by stubs.
- Translation preserves original English and RTL direction handling; provider-supported language listing only. Coverage is deliberately partial and server bounded; some labels or additional paginated stories remain English. Provider errors keep original content. No universal-translation claim.

### Public API and editorial workflow

| Endpoint | Purpose |
|---|---|
| `GET /api/articles/` | Published-only pagination; `q`, `category`, `tag`, `featured=1`, bounded `exclude`/`page_size` |
| `GET /api/articles/<slug>/` | Published detail, provenance, approved comments only |
| `GET /api/articles/<slug>/related/` | Same-category published related stories |
| `GET /api/home/` | Non-overlapping carousel and editorial selections |
| `GET /api/categories/`, `/api/tags/` | Public taxonomy |
| `GET /api/csrf/` | Masked CSRF token/cookie for existing protected form workflows |
| `POST /api/contact/` | Validated message to protected DB inbox; no outbound email |
| `POST /api/articles/<slug>/comments/` | Validated, moderated comment submission |
| Existing utility/translation endpoints | Retained adapters, bounded/cached data and honest errors |
| `/health/live/`, `/health/ready/` | Process status and sanitized DB connectivity readiness |

Public article APIs are read-only and omit drafts, future publication, private fetch settings and credentials. Admin/manual articles, category editing, central featuring, source controls, approved comments and contact inbox remain protected by Django authentication/permissions.

RSS/Atom ingestion is retained and extended with an optional NewsAPI metadata adapter, backend-only API key, normalized publisher attribution, canonical URL uniqueness, normalized title uniqueness and source GUID dedup. Fetching is separate from page rendering. Sources require enablement and confirmed reuse rights. Auto-publication additionally requires **trusted + auto_publish + valid source date**. Otherwise imports stay drafts. Featured placement is never set by ingestion. Permitted image hosts/attribution rules remain explicit.

Invalid dates/feeds/network failures are handled safely; bounded GET retries apply only to transient failures. Failed source fetches record sanitized logs and do not remove stored stories. Source intervals/claims and database constraints prevent repeated imports; the job is callable independently through `fetch_news`, host scheduler/cron or optional Compose scheduler.

### Portability and security

- Same-origin and separate-origin API configurations; no Netlify-only functions/APIs. Vite's development proxy preserves Host so CSRF form submissions work without bypassing protection.
- Fail-closed production DEBUG/secrets/allowed-host/MariaDB configuration; secure cookies, HTTPS redirect, HSTS and explicit origins. Remote database TLS requires a CA and identity verification configuration; real driver/server compatibility and negotiated cipher must be verified at the target host.
- Production requirements and Gunicorn command; optional Docker/Compose/MariaDB/nginx topology, persistent volumes, configurable local or S3-compatible media, host-driven logging, optional shared Redis cache.
- Optional Netlify profile matches actual `frontend/dist` build output, with frontend-only route fallbacks. Backend/asset/media/admin routes are not swallowed by a catch-all redirect.
- Environment examples contain placeholders only. No real client secrets or credentials were introduced. Production image excludes SQLite, environment files, recovery archives and generated local caches.

## Executed checks

Current logs are in `docs/verification/`, not the historical archive.

| Check | Result and scope |
|---|---|
| Original enhanced baseline regression | 43 existing tests passed before refactoring (Stage 1 audit evidence) |
| Final Django tests | **63 tests passed**, temporary isolated SQLite test database |
| Django system check | No issues |
| Migration consistency | No changes detected |
| Additive migrations on copied existing SQLite | Applied successfully; no data reset |
| Django static collection | Executed successfully; production static storage pipeline exercised locally |
| Frontend config tests | **2 tests passed** |
| React production build | Passed; `dist/index.html`, hashed assets, logo and `_redirects` verified |
| Browser acceptance | **31 checks passed**, no page JavaScript errors |
| Focused interaction/routing/contrast | **11 additional checks passed** |
| Responsive widths | 360, 390, 768, 1024, 1440; no whole-document horizontal overflow; appropriate grid columns |
| Themes and widgets | Eight appearance/palette combinations, all six widgets, provider-disabled states |
| Carousel behavior | Explicit-play advance, hover pause, keyboard-focus pause after pointer leaves, reduced-motion disabling |
| API/forms | Draft/future exclusion, pagination/filtering/tags, related stories, sanitized health failure, CORS allowed/denied origins, CSRF enforcement, moderation; browser contact submission passed after proxy Host fix |
| Built-route verification | Local HTTP verification proxy: built-asset article refresh, API/admin/RSS/sitemap/health, reserved resource 404s without SPA fallback |
| Missing images/API/empty/pagination edge states | Tested with explicitly labeled browser interception fixtures; fixtures are not application datasets |
| Production-security harness | HTTPS redirect/cookies/debug checks passed with a **SQLite in-memory override**, not MariaDB. Intentional `security.W021` HSTS preload warning remains; preload requires owner approval |
| Fail-closed startup | Missing production secret rejected |
| Frontend production dependency audit | npm reported 0 vulnerabilities at the time of the check; not a security guarantee for future dependency releases |
| Live Netlify | HTTP 404 remains; no live fix claimed |

### Reproduce locally

```sh
cd backend
DJANGO_DEBUG=1 .venv/bin/python manage.py test -v 1
DJANGO_DEBUG=1 .venv/bin/python manage.py check
DJANGO_DEBUG=1 .venv/bin/python manage.py makemigrations --check --dry-run
DJANGO_DEBUG=1 .venv/bin/python manage.py collectstatic --noinput
.venv/bin/python tests/verify_production_settings.py
cd ../frontend
npm ci
npm test
npm run build
# On a local/staging sample instance with both servers running:
# npx playwright install chromium  # only if no compatible browser is installed
npm run test:browser
# Or CHROMIUM=/path/to/chromium npm run test:browser
```

Browser tests use the preserved sample data and submit a clearly labeled QA contact message; run only on an isolated local/staging copy, not a client's production database. `QA_BASE_URL`, `QA_BACKEND_URL`, `QA_OUT` and `CHROMIUM` configure the test runner. `tests/routing.cjs` additionally requires an actual same-origin staging proxy (`QA_BUILT_URL`) and checks the preserved sample story routes. The verification-only proxy used in this environment was not a production server and is not an nginx/Docker/TLS acceptance claim. Mocked provider/browser-fixture tests do not establish live-provider licensing, quotas, availability or billing.

## Preservation checklist

- [x] Original ten article records, twelve categories and disabled source candidates retained; all original article/category/source fields compared against baseline.
- [x] Original 0001/0002 migrations preserved byte-for-byte; same app label/tables.
- [x] Seven media file paths and SHA-256 values preserved; deterministic WordPress media alias documented.
- [x] Existing routes/forms/admin/contact/comment/source workflows retained.
- [x] Device date/time, independent themes/palettes, six widgets, language control, saved-story keys and copy-link feature retained.
- [x] No new automatic publication of previously untrusted sources; new trust flag defaults false.
- [x] Temporary browser QA contact submissions removed from the delivery copy only, without clearing user records or reseeding.
- [x] Unchanged input archive and historical recovery materials retained; exact move/change manifest supplied.

## Remaining client/host acceptance gates

1. Provide a compatible Python host, actual MariaDB service/credentials, approved domains and TLS edge. MariaDB driver import, connectivity, migrations, Unicode/collation/unique constraints, SSL identity verification and backup/restore **have not been executed against MariaDB** here.
2. Run optional Docker build/Compose/nginx profile on the actual host; no Docker daemon/nginx binary was available locally. Verify volume ownership, persistence and direct asset/media requests. Object storage and Redis need real services if chosen.
3. Review publisher/feed/API/excerpt/image rights and current plan coverage. Configure backend keys and enable only approved sources. Existing source candidates remain disabled. No live authenticated news/translation/weather API was verified.
4. Install/activate the selected scheduler and prove two off-traffic run intervals, logs, restart recovery and disabled-source behavior. A cron example/loop configuration alone is not proof of a working host scheduler.
5. For separate real origins, verify HTTPS CORS/CSRF and browser cookie policies. Same-site API or same-origin proxy is preferred; third-party-cookie blocking can affect unrelated domains.
6. Configure shared quotas/rate limiting before enabling publicly accessible paid providers or multiworker forms; optional Redis is configurable, but no shared service was connected here.
7. Complete legal/privacy/retention/editorial/media-license review; onboard a real admin securely; approve indexability/robots/ads policy. Preview remains deliberately noindex and ads disabled.
8. Inspect the actual Netlify revision, build/deploy logs and published files, then perform an authorized deployment and verify the remote homepage/article refresh/API. Current live 404 is not marked fixed.

## Package use

The handover ZIP includes source, environment examples, deployment profiles, original development data/media, current test evidence, historical recovery material and verified prebuilt `frontend/dist` assets for a **same-origin** profile. Generated dependencies, virtual environments, Git internals, collected static outputs, bytecode, caches and real environment files are excluded. Rebuild frontend assets for a separate backend origin. A prebuilt frontend is not a running Django or MariaDB service.

Start with root `README.md`; follow `DEPLOYMENT.md` for the chosen host, then `database/backup-restore.md` before touching existing production data. No production data should be dropped, overwritten, reset or reseeded as part of deployment.
