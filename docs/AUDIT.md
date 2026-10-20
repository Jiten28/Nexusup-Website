# NexusUp — Stage 1 audit and migration plan

**Status: audit only. No application source, deployment settings, media, or existing database records changed. Stages 2–9 are not yet implemented.**

## 1. Audited baseline and recovery

The available input is the latest delivered `NexusUp_Enhanced_Django.zip`, not an independently supplied newer production repository. The archive has 131 files and passes ZIP integrity checks.

- Archive SHA-256: `5799c4cb0055ba7a2cb2d2e75f714216dce45a9915ba7a57e120d56091a253cc`.
- Embedded untouched earlier recovery ZIP SHA-256: `aab866652e71ec005d6897fc36fa24381995791a2f9e596566bed39c37f77308`.
- Existing local Git checkpoints: `aa4d491` (original demo) and `d008b5a` (enhancement). Working tree is clean. Git history is available locally, but `.git` is intentionally absent from the delivered ZIP.
- Existing isolated release extraction matches every archive member byte-for-byte, both before and after audit tests. Existing database and seven media files remain unchanged.
- No reset, reseed, schema application, source enabling, package installation, deployment, DNS modification, or paid service activation was performed. Test seed operations occurred only in temporary test databases.

## 2. What exists

### Application

Python/Django 5.2.18, Django templates, ordinary CSS and vanilla JavaScript. One Django app, `news`, contains Category, Article, NewsSource, FetchRun, Comment and ContactMessage. There is no React, Vite, TypeScript, React Router or Django REST Framework in the package.

Django project modules: settings, root URLs and WSGI. Two existing `news` migrations are applied. Public views implement homepage, article detail/related stories, category archive, substring search, pagination, contact and informational pages. Existing Django admin manages all six models, comments and central featuring.

Existing JSON routes are utilities/translation only: `/api/currency/`, `/api/cities/`, `/api/weather/`, `/api/languages/`, `/api/translate/`. There is no article/category/tag/featured/related-news REST API. No Tag model exists.

### Database and content

- Actual development engine: SQLite, `demo.sqlite3`, 241,664 bytes; integrity check is `ok`; no foreign-key violations.
- Ten published articles, all marked illustrative samples; three currently have the existing featured flag.
- Twelve categories, two disabled/unapproved BBC India/World candidate sources, zero fetch runs, comments and contact submissions.
- Production configuration selects Django's MySQL backend through `DB_ENGINE=mariadb`, environment credentials, utf8mb4 and strict SQL mode. Production requirements list mysqlclient and Gunicorn.
- No MariaDB server process/client or installed mysqlclient was found in this environment. No service endpoint/credentials were supplied. **MariaDB connectivity/migrations are not verified.** No switch to PostgreSQL is proposed.

### UI and assets

Seven original dated media images and the existing book logo. Current public layout contains a vertical image-headline slider, continuous scrolling text Headlines strip, category chips, large center story/two smaller stories each side, Latest News grid, editorial picks and footer. Both animation components have controls/reduced-motion code; these are baseline features, not the new acceptance target.

Existing controls: independent persisted appearance/four palettes, local device date/time, language selector, six header widgets, mobile navigation, browser-local saves and copy-link feedback. CSS is layered as `site.css` plus a later `magazine.css`; three scripts operate directly on the DOM.

Media uses `/media/YYYY/MM/...` and a DEBUG-only `/wp-content/uploads/` compatibility alias. Production static/media serving is not configured as an actual host service. No upload-storage provider is connected; article media primarily uses stored paths or approved remote URLs.

### Ingestion and integrations

RSS/Atom parser, source management, canonical URL/hash dedup, source-category mapping, permission-gated remote image references, draft-default imports, per-source fetch intervals, per-item transactions, DB claim, fetch logs and management commands are present. Registry supports future adapters, but only RSS is implemented. No homepage-triggered fetching.

`deploy/news-fetch.cron.example` is an uninstalled scheduler example, not an active job. Sources and network integrations ship disabled. Weather/currency use cached server adapters; Google Cloud/LibreTranslate adapters are partial localization and require configuration. No private provider key is bundled.

## 3. What works — checks freshly executed in Stage 1

| Check | Result |
| --- | --- |
| ZIP integrity and archive/extracted-copy comparison | Passed; no changed members |
| SQLite integrity / foreign-key check | Passed |
| Current `python manage.py check` | No issues |
| Current `python manage.py makemigrations --check --dry-run` | No changes detected |
| Current `python manage.py migrate --check` | No unapplied migrations |
| Current `python manage.py test -v 1` | **43 passed**, temporary test DB |
| Earlier baseline `python manage.py test -v 0` | **21 passed**, separate temporary test DB |
| `python manage.py check --deploy` under packaged development defaults | Six security warnings; not production-ready defaults |
| Source/database/media preservation after tests | All packaged members unchanged |

Production-check warnings: W004 (HSTS not set in debug), W008 (HTTPS redirect not enabled in debug), W009 (demo secret), W012 (session secure cookie), W016 (CSRF secure cookie), W018 (DEBUG). Production settings conditionally set several protections, but no real production environment/proxy/database was available to validate. This is not a successful production deployment check.

The current 43 tests include routes/search/pagination, draft/future exclusion, manual admin publishing, moderation, CSRF, escaping, media paths, ingestion dedup/dry-run/failure handling, existing auto_publish behavior, featuring, disabled services, mocked Google/Libre adapters and private-network blocking. They do **not** prove a separate trusted-source policy; that policy does not yet exist.

Packaged prior evidence records 89 browser checks. Those are **historical**, not freshly reexecuted Stage 1 browser acceptance tests. React production build, Netlify output/route refreshes, live provider credentials and MariaDB integration remain untested because the required frontend/deployment/services do not exist or are unavailable.

## 4. Confirmed gaps and risks

1. **Netlify artifact gap:** no frontend directory, package.json/build script, Vite config, built index.html, netlify.toml or SPA redirect file exists in this ZIP. Conventional Django templates are not a built React site. A static publishing/build mismatch is plausible, but the live 404's actual cause is **not confirmed** without the deployed site/repository/settings/logs.
2. **Publishing trust gap:** enabled and rights-confirmed sources use `auto_publish` directly. There is no separate trusted flag. Add trusted independently; default new/existing sources to untrusted until explicitly approved, and require enabled + rights-confirmed + trusted + auto_publish + eligibility. Recheck current source state at work/publication boundaries.
3. **Homepage repetition:** the same queryset fills slider, Headlines, hero/supporting cards, latest and editorial picks. There is no section-level exclusion or frontend Load More. Header/category/archive lists serve different navigation contexts; consolidate only verified redundant UI, not all category links blindly.
4. **Animation mismatch:** new instructions supersede the old two-animation requirement. Replace the vertical slider and scrolling text strip with exactly one horizontal image carousel, with restrained optional auto-advance, manual controls and reduced-motion support. No separate animated breaking ticker.
5. **Ingestion limits:** URL-only dedup; provider GUID is stored but not a dedup constraint; no normalized-title fallback; only RSS adapter; no bounded retry/backoff policy beyond waiting for next interval; feed cap 100; URL normalization upgrades HTTP to HTTPS; invalid/missing publication dates need stricter eligibility treatment. Existing per-row transaction safety must be retained, not replaced by a fetch-wide destructive transaction.
6. **Frontend/API gap:** add DRF read-only published article/category/tag/featured/related endpoints, pagination and explicit filters/validation. Preserve existing utilities and moderation/contact flows when React is introduced. Public endpoints must not leak source credentials, source policy controls, drafts or private submissions.
7. **Split-host security gap:** no frontend-origin CORS/CSRF settings, shared production cache/rate limits, MariaDB TLS settings or operational structured logging. Demo uses process-local caches and session-only cooldowns. `DEBUG` currently defaults to on; production must explicitly fail safely.
8. **Media gap:** DEBUG routes do not establish persistent production media. API image URLs need an approved media/backend origin, no localhost leakage, deterministic legacy path mapping and broken-image fallback. No duplicate article-image directory is needed.
9. **SEO/editorial gap:** demo noindex, sample RSS/footer/policy text and assumptions are intentional current safeguards. Do not remove sample disclaimers until real content/launch configuration is approved. React migration must explicitly address per-article canonical/Open Graph/SEO behavior; SPA fallback alone does not provide server-rendered metadata.
10. **Maintainability gap:** compressed one-line modules, dynamic Django imports and some unused imports should be cleaned while preserving behavior. Requirements are few and materially used; no dependency has been proven safe to delete wholesale.

## 5. Redundancy and consolidation plan — nothing removed yet

| Existing area | Finding | Proposed handling |
| --- | --- | --- |
| docs/, docs/previews/, docs/enhancement/ | 64 files, ~25.7 MB uncompressed, mixed historical/current reports and screenshots | One current docs entry point; preserve historical evidence under an archive or separate recovery artifact, not active configuration |
| site.css + magazine.css | 34 exactly overlapping selector groups and repeated appearance tokens | Consolidate tested tokens/styles into frontend; keep required legacy fallback styles until compatibility is verified |
| scripts/browser_qa.cjs + enhancement_qa.cjs + supplemental.cjs | Overlapping browser checks, ad hoc sandbox paths | One maintained test entry point with portable config; archive prior evidence/scripts only after coverage mapping |
| root config/, news/, templates/, static/, media/ | Legitimate Django runtime resources, not disposable clutter | Move together under backend; update all imports, settings, commands and references |
| deploy/news-fetch.cron.example | Scheduler example only | Consolidate deployment instructions/config with backend host setup; install only on an authorized host |
| recovery/ | Real recoverable source archive/hash manifest | Preserve; relocate as an explicitly mapped recovery artifact, never delete |
| docs/reference-ads.txt | Read at runtime by `/ads.txt` when enabled | Move to a backend resource and update the consumer; do not discard as documentation |
| news/demo_data.json | Used by optional seed command | Retain with command; never auto-seed production |
| media/YYYY/MM files | Seven unique content assets | Retain bytes and relative paths in one media root |
| __init__.py files | Necessary package/migration markers | Retain; identical empty files are not useless duplicates |

No exact duplicate nonempty files were found. Redundancy here is layered styling, repeated behavior/content and accumulated evidence, not proof that arbitrary folders are unused. Build outputs/caches/virtualenvs are already absent from the delivered ZIP; future frontend dist/coverage/log/secret exclusions must be added.

## 6. Before and proposed after tree

### Actual before

```text
NexusUp_Enhanced_Django/
├── config/                 # Django settings, URLs, WSGI
├── news/                   # all domain models, forms, admin, APIs, services, tests
│   ├── management/commands/
│   └── migrations/         # 0001 and 0002; preserve
├── templates/news/         # server-rendered public UI
├── static/{css,js,img}/
├── media/YYYY/MM/          # seven original assets
├── docs/{previews,enhancement}/
├── deploy/                 # example cron only
├── recovery/               # original source ZIP and manifests
├── scripts/                # browser QA, media restore, demo runner
├── demo.sqlite3
├── manage.py
├── requirements.txt
├── requirements-production.txt
├── .env.example
└── README.md, START_HERE.md, .gitignore
```

### Proposed after — NOT yet created

```text
NexusUp/
├── frontend/
│   ├── src/{components,pages,layouts,services,hooks,context,styles,assets}/
│   ├── public/             # stable public assets and SPA fallback where appropriate
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example        # public API/media origin only; no privileged secrets
├── backend/
│   ├── manage.py
│   ├── config/
│   ├── apps/news/          # retain existing app label `news` and DB table identity
│   │   ├── migrations/     # existing history plus additive migrations
│   │   └── management/commands/
│   ├── services/ingestion/ # only if moving existing service improves separation
│   ├── tests/              # maintained regression/integration tests
│   ├── templates/          # required legacy compatibility during migration
│   ├── static/             # backend/legacy assets only; admin collected separately
│   ├── media/YYYY/MM/      # existing local assets; production persistent storage
│   ├── demo.sqlite3        # retained development data; ignored for future commits
│   ├── requirements.txt
│   └── .env.example
├── database/
│   ├── README.md
│   └── backup-restore.md   # documents a real MariaDB service, not file-based DB storage
├── docs/
│   ├── README.md           # single active architecture/deployment entry point
│   └── archive/            # mapped historical reports/evidence/recovery material
├── netlify.toml            # only after actual frontend build is verified
├── README.md
└── .gitignore
```

Do not split the existing Category/NewsSource models into new Django apps solely to match an example tree. Keeping their current `news` app label avoids unnecessary table/content-type/migration churn. Any move needs an AppConfig/import audit and passing regression tests before proceeding. The detailed file-by-file move/removal manifest will be generated against the preserved baseline during Stage 2; this tree is a plan, not an already completed refactor.

## 7. Feature-preservation checklist for implementation

- [ ] Existing article/category/search URLs and pagination behavior, with React route compatibility.
- [ ] Article detail, related stories, reading time, canonical/Open Graph, RSS and sitemap.
- [ ] Comments with moderation and validated contact submissions; protected Django admin.
- [ ] Independent themes/palettes and existing browser storage keys/saved-story state.
- [ ] Six utility widgets, language/original-content restore and device-local time.
- [ ] Source management, fetch history, manual entry, scheduled visibility and editorial featuring.
- [ ] Existing database records, app identity, migration history and dated media paths.
- [ ] Responsive navigation/accessibility and honest unavailable/loading/empty states.
- [ ] Explicit replacement of two old animations by the one approved horizontal carousel.
- [ ] Distinct section article pools and controlled backend-paginated Load More.

These are acceptance obligations, not claims that the React versions have already passed.

## 8. Implementation order after audit

2. Move existing backend as a unit; keep app label/table identity, database, migrations/media; update imports and references; rerun baseline checks. Record each consolidation before removal.
3. Add React + Vite and DRF API contracts. Proposed TypeScript for typed API records; no heavy UI library. Existing DOM utilities can be ported incrementally rather than embedding a second competing frontend.
4. Add environment-driven MariaDB TLS/connection checks and backup/restore/migration documentation. Retain SQLite development data; test actual MariaDB only with a compatible available service.
5. Add explicit trusted-source policy, publication eligibility, stronger dedup, adapter contract, bounded retry/backoff and host-supported scheduling; preserve manual editorial control and safe stored-content fallbacks.
6. Port recognizable layout/branding, exactly one contained horizontal image carousel, disjoint story pools, Load More, themes, widgets, translation and media fallbacks. Manual carousel navigation by default; optional restrained autoplay with pause/reduced-motion rules.
7. Verify `npm run build` and actual dist/index.html; configure Netlify base frontend/build npm run build/publish dist only if confirmed by the produced project. Add route fallback without swallowing API/admin/feed/media requests. Diagnose live 404 from deploy logs, not assumptions.
8. Run regressions, API/security/ingestion policy tests, frontend build/route tests, five widths/eight themes, framework deployment checks and available MariaDB tests. Preserve real SEO/metadata compatibility and document blocked live checks.
9. Deliver source ZIP, exact added/moved/changed/removed manifest, tests and deployment/rollback instructions. No live deployment without separate authorization.

## 9. Inputs and approval boundaries

Needed to diagnose the **actual Netlify deployment**: public Netlify site URL, latest deploy log (redact secrets), and repository/branch/base/build/publish settings. If deployed code differs from this ZIP, supply that revision/archive before refactoring it.

Needed for **live MariaDB validation and host scheduling**: chosen Python host/MariaDB service/version, TLS requirements and an approved private connection method. Do not paste passwords or privileged keys into chat.

Needed for **real news/translation/weather activation**: approved provider/source rights, trust policy, any commercial subscriptions and private credentials. Existing data remains available without these.

No additional approval is needed merely to prepare the local refactor within this request. Production deployment, DNS changes, external account creation, purchases or enabling source publication still require explicit authorization. These access gaps do not justify claiming live success or replacing the database.
