# Export changelog

Base commit: `b91202bdef8bbcf066dc497710f38eef84f598f5`
Branch: `master`

This is a working-tree snapshot on top of the base, not a new Git commit or release. Frontend package version: 1.0.0.
Entries compare the current tree with the base, regardless of author. They do not claim every pre-existing/user edit was authored by the assistant.
The recent audit-only turns did not implement the proposed ingestion/carousel fixes. This export adds documentation only in staging.

## Modified tracked files

- `backend/.env.example` — Expanded safe local environment template for dotenv, NewsAPI, database timeout/TLS, origins, storage, cache and logging settings.
- `backend/apps/news/admin.py` — Updated editorial/source trust controls and moderation/admin presentation.
- `backend/apps/news/feeds.py` — Adjusted feed/sitemap behavior and article/source handling.
- `backend/apps/news/ingestion.py` — Added NewsAPI metadata adapter, bounded pagination, safe provider diagnostics, publisher attribution, deduplication and atomic batch handling; known audit defects retained.
- `backend/apps/news/management/commands/fetch_news.py` — Command reports failed sources and returns a command error rather than silently succeeding on provider failures.
- `backend/apps/news/migrations/0001_initial.py` — Updated baseline field definitions; existing migration history is retained as found, not rewritten during export.
- `backend/apps/news/migrations/0002_article_breaking_until_article_canonical_source_url_and_more.py` — Updated ingestion-related migration definitions as present in the working tree.
- `backend/apps/news/models.py` — Added publisher attribution, unique nullable title hash and editorial/source model changes.
- `backend/apps/news/network.py` — Hardened outbound HTTPS destination/redirect handling and bounded retry behavior.
- `backend/apps/news/tests.py` — Adjusted core site regression expectations.
- `backend/apps/news/tests_enhancements.py` — Updated source/editorial and legacy presentation regression tests.
- `backend/apps/news/views.py` — Updated legacy homepage allocation and presentation query handling.
- `backend/config/settings.py` — Added explicit dotenv loading, API/CORS/storage/cache/provider configuration and production safeguards.
- `backend/config/urls.py` — Added REST endpoints and health routes while preserving legacy routes and admin.
- `backend/demo.sqlite3` — Working sample database differs from base. Export contains a rebuilt, free-page-cleaned snapshot with identical logical table data; no private user credentials/sessions ship.
- `backend/requirements-production.txt` — Added optional production Redis client dependency.
- `backend/requirements.txt` — Updated/pinned backend dependencies including DRF, CORS and python-dotenv.
- `backend/scripts/run_demo.sh` — Updated local launcher; it still installs dependencies and runs migrations and is not read-only.
- `backend/static/css/magazine.css` — Adjusted retained Django magazine styles.
- `backend/static/js/magazine.js` — Adjusted retained legacy animation/interaction logic.
- `backend/templates/news/animations.html` — Updated retained animation/carousel template markup.

## Deleted tracked files

- `backend/scripts/browser_qa.cjs` — Absent from current working tree; corresponding historical test is retained under docs/archive/legacy-tests/.
- `backend/scripts/enhancement_qa.cjs` — Absent from current working tree; corresponding historical test is retained under docs/archive/legacy-tests/.

## Created / untracked source, configuration and documentation files

- `.dockerignore` — Optional deployment/build configuration; not executed or enabled by export.
- `.env.production.example` — Safe configuration template with placeholders; not a private environment file.
- `.gitignore` — Ignore rules for secrets, caches, dependencies, builds and runtime files.
- `README.md` — Project overview, local workflow and links to handover documentation.
- `backend/Dockerfile` — Optional deployment/build configuration; not executed or enabled by export.
- `backend/apps/news/migrations/0003_editorial_trust_tags_dedup.py` — Additive editorial trust/tag/deduplication schema migration.
- `backend/apps/news/migrations/0004_publisher_and_unique_title.py` — Publisher attribution and nullable unique title-hash migration preserving existing rows.
- `backend/apps/news/rest.py` — Read-only published article/category/tag/home APIs, health checks and moderated form endpoints.
- `backend/apps/news/tests_newsapi.py` — Mocked NewsAPI, dotenv, rollback, deduplication and safe-error regression tests.
- `backend/apps/news/tests_rest.py` — API, visibility, origin/CSRF and publication-trust regression tests.
- `backend/config/environment.py` — Explicit backend dotenv loader; process environment takes precedence.
- `backend/tests/verify_production_settings.py` — Offline production-security configuration harness; not active-runtime identification.
- `compose.yaml` — Optional deployment/build configuration; not executed or enabled by export.
- `database/README.md` — MariaDB configuration/preservation and backup/restore documentation.
- `database/backup-restore.md` — MariaDB configuration/preservation and backup/restore documentation.
- `docs/AUDIT.md` — Documentation, historical reference, deployment example or inventory: AUDIT.md.
- `docs/BACKEND_STABILIZATION.md` — Documentation, historical reference, deployment example or inventory: BACKEND_STABILIZATION.md.
- `docs/DEPLOYMENT.md` — Documentation, historical reference, deployment example or inventory: DEPLOYMENT.md.
- `docs/FILE_CHANGES.md` — Documentation, historical reference, deployment example or inventory: FILE_CHANGES.md.
- `docs/FRONTEND_DEMO.md` — Documentation, historical reference, deployment example or inventory: FRONTEND_DEMO.md.
- `docs/HANDOVER.md` — Documentation, historical reference, deployment example or inventory: HANDOVER.md.
- `docs/archive/legacy-tests/browser_qa.cjs` — Documentation, historical reference, deployment example or inventory: browser_qa.cjs.
- `docs/archive/legacy-tests/enhancement_qa.cjs` — Documentation, historical reference, deployment example or inventory: enhancement_qa.cjs.
- `docs/deploy/nginx-container.conf` — Documentation, historical reference, deployment example or inventory: nginx-container.conf.
- `docs/file-manifest.json` — Documentation, historical reference, deployment example or inventory: file-manifest.json.
- `frontend/.env.example` — Safe configuration template with placeholders; not a private environment file.
- `frontend/Dockerfile` — Optional deployment/build configuration; not executed or enabled by export.
- `frontend/index.html` — New working-tree file: index.html.
- `frontend/package-lock.json` — Locked npm dependency graph for reproducible frontend installs.
- `frontend/package.json` — Frontend package scripts, framework and dependency declarations.
- `frontend/public/_redirects` — Frontend public asset or static route configuration.
- `frontend/public/book.webp` — Frontend public asset or static route configuration.
- `frontend/public/preview/chip.webp` — Explicit opt-in demo illustration asset, not live-reporting data.
- `frontend/public/preview/city.webp` — Explicit opt-in demo illustration asset, not live-reporting data.
- `frontend/public/preview/cricket.webp` — Explicit opt-in demo illustration asset, not live-reporting data.
- `frontend/public/preview/mangrove.webp` — Explicit opt-in demo illustration asset, not live-reporting data.
- `frontend/public/preview/observatory.webp` — Explicit opt-in demo illustration asset, not live-reporting data.
- `frontend/public/preview/solar.webp` — Explicit opt-in demo illustration asset, not live-reporting data.
- `frontend/src/App.jsx` — React UI component/page/context for App.
- `frontend/src/components/Carousel.jsx` — React horizontal headline carousel with controls, interaction pause, six-second timer and reduced-motion handling; autoplay initially off.
- `frontend/src/components/StoryCard.jsx` — React UI component/page/context for StoryCard.
- `frontend/src/components/Widgets.jsx` — React UI component/page/context for Widgets.
- `frontend/src/components/legacyWidgets.js` — React supporting module for legacyWidgets.
- `frontend/src/context/Translation.jsx` — React UI component/page/context for Translation.
- `frontend/src/main.jsx` — React UI component/page/context for main.
- `frontend/src/pages/NewsPages.jsx` — React UI component/page/context for NewsPages.
- `frontend/src/preview/Preview.jsx` — React UI component/page/context for Preview.
- `frontend/src/preview/data.js` — React supporting module for data.
- `frontend/src/services/api.js` — React supporting module for api.
- `frontend/src/services/preferences.js` — React supporting module for preferences.
- `frontend/src/services/themes.js` — React supporting module for themes.
- `frontend/src/styles/site.css` — Public React layout, responsive styles, theme tokens and current image-led carousel sizing.
- `frontend/tests/browser.cjs` — Frontend regression test/harness: browser.cjs; execution safety depends on suite (see WINDOWS_SETUP.md).
- `frontend/tests/built-demo.cjs` — Frontend regression test/harness: built-demo.cjs; execution safety depends on suite (see WINDOWS_SETUP.md).
- `frontend/tests/config.test.js` — Frontend regression test/harness: config.test.js; execution safety depends on suite (see WINDOWS_SETUP.md).
- `frontend/tests/demo.cjs` — Frontend regression test/harness: demo.cjs; execution safety depends on suite (see WINDOWS_SETUP.md).
- `frontend/tests/demo.test.js` — Frontend regression test/harness: demo.test.js; execution safety depends on suite (see WINDOWS_SETUP.md).
- `frontend/tests/routing.cjs` — Frontend regression test/harness: routing.cjs; execution safety depends on suite (see WINDOWS_SETUP.md).
- `frontend/vite.config.js` — New working-tree file: vite.config.js.
- `netlify.toml` — Optional deployment/build configuration; not executed or enabled by export.

## Changed/new generated files omitted from export

Every omitted path/group and its reason is listed in OMISSIONS.md. The machine-readable manifest lists each changed/new file and whether it is included. No current source functionality was intentionally removed.

## Export-only additions (not written into the source workspace)

- `EXPORT/CHANGELOG.md` — This per-file working-tree changelog.
- `EXPORT/WINDOWS_SETUP.md` — PowerShell setup, database choices, environment names and run/test commands.
- `EXPORT/KNOWN_ISSUES.md` — Pending fixes, audit scope and historical-evidence caveats.
- `EXPORT/OMISSIONS.md` — Explicit exclusions and regenerated database explanation.
- `EXPORT/VERSION.json` — Base commit, branch, build provenance and validation details.
- `EXPORT/MANIFEST.json` — Per-file hashes/status and complete changed-file/exclusion inventory.
