# File changes and consolidation

The exact source inventory is `file-manifest.json`, with original/final SHA-256 hashes for every mapped file. No baseline source/media/recovery file was silently discarded. Original input ZIP remains unchanged outside this working copy; the embedded older recovery ZIP is retained in `docs/archive/recovery/`.

## Before (enhanced Django baseline)

```text
NexusUp_Enhanced_Django/
  config/                 Django project
  news/                   models, migrations, views, utilities, ingestion
  templates/              public Django templates
  static/                 CSS, JS, logo
  media/YYYY/MM/          seven original images
  scripts/                local launcher, media restore, historical browser tests
  deploy/                 historical cron/profile samples
  docs/                   audit and enhancement reports
  recovery/               earlier recovery ZIP
  manage.py
  demo.sqlite3
  requirements*.txt
  .env.example
  README.md / START_HERE.md
```

## After (portable full-stack package)

```text
NexusUp/
  frontend/
    src/
      App.jsx, main.jsx      shared public layout and routes
      components/           Carousel, StoryCard, Widgets, preserved widget logic
      pages/                NewsPages: home, listings, article, forms, info
      context/              bounded public translation context
      services/             configured API client and legacy-compatible preferences
      styles/               responsive magazine tokens/layout
    public/                 original logo; frontend-only route rules
    tests/                  config, browser and focused routing/contrast tests
    dist/                   verified prebuilt same-origin handover assets (Git ignored)
    package.json, package-lock.json, vite.config.js, Dockerfile, .env.example
  backend/
    config/                 one retained Django project
    apps/news/              one retained app; original label/tables; API and migrations
    templates/, static/     retained legacy fallback/resources; one consolidated strip
    media/YYYY/MM/          original paths and bytes preserved
    resources/              runtime ads reference, not an archived docs dependency
    scripts/                local-only launcher and opt-in validated media restore
    tests/                  explicit offline production-security harness
    demo.sqlite3            existing records, additive migrations only
    manage.py, requirements*.txt, Dockerfile, .env.example
  database/                 MariaDB setup, opt-in transfer, backup/restore docs
  docs/
    AUDIT.md                Stage 1 historical findings
    HANDOVER.md             current feature/status/test report
    DEPLOYMENT.md           current deployment source of truth
    FILE_CHANGES.md, file-manifest.json
    deploy/                 active nginx profile
    verification/           current logs, evidence and preview images
    archive/                historical docs, old deploy profiles/tests, recovery ZIP
  README.md, .gitignore, .dockerignore, .env.production.example
  compose.yaml, netlify.toml
```

## Consolidated, retained and excluded

| Area | Handling and reason |
|---|---|
| Django config/news | Moved under backend, imports updated; app label remains `news`. No redundant category/source apps. |
| Original 0001/0002 migrations | Copied byte-for-byte from input after Python-module moves; historical dependencies intact. |
| Existing SQLite and seven media files | Preserved in backend; no reset/reseed; only additive migrations and removal of this session's synthetic QA messages. Original fields and media hashes verified. |
| Runtime ads.txt declaration | Moved to backend/resources; view/test references corrected. Historical docs copy remains for audit. Advertising still disabled. |
| Vertical slider + continuous marquee | Replaced with one horizontal image strip; obsolete active JS initializers removed, behavior checks updated to the new agreed requirement. Original implementation remains recoverable from input/history. |
| Repeated featured/latest/editor blocks | React uses disjoint article IDs and omits redundant editor block; legacy home excludes used IDs and has no repeated picks. |
| Utility code | Preserved safe implementation in React lifecycle shell, not re-created as stubs. Legacy version remains only for Django fallback. |
| Backend templates/static | Retained for original-route compatibility and admin/fallback; not a second competing React build. |
| Logo duplication | One deliberate public copy lets the static frontend deploy independently; backend retains original for its fallback. Media images are not duplicated into frontend. |
| Older docs/deploy/recovery | Consolidated under docs/archive; clearly historical, no production entry points. |
| Two superseded browser scripts | Moved from backend/scripts to docs/archive/legacy-tests because they target the old two-animation UI. Current acceptance scripts live under frontend/tests. |
| Demo launcher | Kept local-only, DEBUG explicit; automatic seed step removed to avoid overwriting existing records. |
| Generated dependencies/caches | Virtualenv, node_modules, bytecode, Git internals, collected static output excluded from delivery/source inventory. |
| Vite dist | Git ignored but intentionally supplied as a verified prebuilt handover artifact. Rebuild with the selected API origin for separate hosting. |

## Exact mapped file actions

- `.env.example` → `backend/.env.example` — moved; modified.
- `.gitignore` → `docs/archive/baseline-.gitignore` — moved; unchanged.
- `README.md` → `docs/archive/baseline-README.md` — moved; unchanged.
- `START_HERE.md` → `docs/archive/baseline-START_HERE.md` — moved; unchanged.
- `demo.sqlite3` → `backend/demo.sqlite3` — moved; modified.
- `manage.py` → `backend/manage.py` — moved; unchanged.
- `requirements-production.txt` → `backend/requirements-production.txt` — moved; modified.
- `requirements.txt` → `backend/requirements.txt` — moved; modified.
- `config/__init__.py` → `backend/config/__init__.py` — moved; unchanged.
- `config/settings.py` → `backend/config/settings.py` — moved; modified.
- `config/urls.py` → `backend/config/urls.py` — moved; modified.
- `config/wsgi.py` → `backend/config/wsgi.py` — moved; unchanged.
- `docs/AUDIT.md` → `docs/archive/AUDIT.md` — moved; unchanged.
- `docs/IMPLEMENTATION.md` → `docs/archive/IMPLEMENTATION.md` — moved; unchanged.
- `docs/MIGRATION_PLAN.md` → `docs/archive/MIGRATION_PLAN.md` — moved; unchanged.
- `docs/TESTING.md` → `docs/archive/TESTING.md` — moved; unchanged.
- `docs/archive-contents.txt` → `docs/archive/archive-contents.txt` — moved; unchanged.
- `docs/archive-inventory.json` → `docs/archive/archive-inventory.json` — moved; unchanged.
- `docs/browser-results.json` → `docs/archive/browser-results.json` — moved; unchanged.
- `docs/media-audit.jpg` → `docs/archive/media-audit.jpg` — moved; unchanged.
- `docs/media-manifest.json` → `docs/archive/media-manifest.json` — moved; unchanged.
- `docs/media-restore-dry-run.json` → `docs/archive/media-restore-dry-run.json` — moved; unchanged.
- `docs/plugin-audit.json` → `docs/archive/plugin-audit.json` — moved; unchanged.
- `docs/reference-ads.txt` → `docs/archive/reference-ads.txt` — moved; unchanged.
- `docs/test-results.txt` → `docs/archive/test-results.txt` — moved; unchanged.
- `docs/INTEGRATIONS.md` → `docs/archive/INTEGRATIONS.md` — moved; unchanged.
- `docs/PRE_EDIT_AUDIT.md` → `docs/archive/PRE_EDIT_AUDIT.md` — moved; unchanged.
- `docs/ENHANCEMENT_REPORT.md` → `docs/archive/ENHANCEMENT_REPORT.md` — moved; unchanged.
- `docs/FILE_CHANGES.md` → `docs/archive/FILE_CHANGES.md` — moved; unchanged.
- `news/__init__.py` → `backend/apps/news/__init__.py` — moved; unchanged.
- `news/admin.py` → `backend/apps/news/admin.py` — moved; modified.
- `news/context.py` → `backend/apps/news/context.py` — moved; unchanged.
- `news/demo_data.json` → `backend/apps/news/demo_data.json` — moved; unchanged.
- `news/feeds.py` → `backend/apps/news/feeds.py` — moved; modified.
- `news/forms.py` → `backend/apps/news/forms.py` — moved; unchanged.
- `news/models.py` → `backend/apps/news/models.py` — moved; modified.
- `news/tests.py` → `backend/apps/news/tests.py` — moved; modified.
- `news/views.py` → `backend/apps/news/views.py` — moved; modified.
- `news/network.py` → `backend/apps/news/network.py` — moved; modified.
- `news/ingestion.py` → `backend/apps/news/ingestion.py` — moved; modified.
- `news/services.py` → `backend/apps/news/services.py` — moved; unchanged.
- `news/api.py` → `backend/apps/news/api.py` — moved; unchanged.
- `news/tests_enhancements.py` → `backend/apps/news/tests_enhancements.py` — moved; modified.
- `scripts/browser_qa.cjs` → `docs/archive/legacy-tests/browser_qa.cjs` — moved; unchanged.
- `scripts/restore_media.py` → `backend/scripts/restore_media.py` — moved; unchanged.
- `scripts/run_demo.sh` → `backend/scripts/run_demo.sh` — moved; modified.
- `scripts/enhancement_qa.cjs` → `docs/archive/legacy-tests/enhancement_qa.cjs` — moved; unchanged.
- `templates/404.html` → `backend/templates/404.html` — moved; unchanged.
- `templates/base.html` → `backend/templates/base.html` — moved; unchanged.
- `deploy/news-fetch.cron.example` → `docs/archive/deploy/news-fetch.cron.example` — moved; unchanged.
- `recovery/NexusUp_Django_Demo.zip` → `docs/archive/recovery/NexusUp_Django_Demo.zip` — moved; unchanged.
- `recovery/checkpoint.json` → `docs/archive/recovery/checkpoint.json` — moved; unchanged.
- `recovery/baseline-file-hashes.json` → `docs/archive/recovery/baseline-file-hashes.json` — moved; unchanged.
- `templates/news/article.html` → `backend/templates/news/article.html` — moved; unchanged.
- `templates/news/card.html` → `backend/templates/news/card.html` — moved; unchanged.
- `templates/news/contact.html` → `backend/templates/news/contact.html` — moved; unchanged.
- `templates/news/home.html` → `backend/templates/news/home.html` — moved; unchanged.
- `templates/news/info.html` → `backend/templates/news/info.html` — moved; unchanged.
- `templates/news/list.html` → `backend/templates/news/list.html` — moved; unchanged.
- `templates/news/header.html` → `backend/templates/news/header.html` — moved; unchanged.
- `templates/news/widgets.html` → `backend/templates/news/widgets.html` — moved; unchanged.
- `templates/news/animations.html` → `backend/templates/news/animations.html` — moved; modified.
- `templates/news/feature-card.html` → `backend/templates/news/feature-card.html` — moved; unchanged.
- `static/css/site.css` → `backend/static/css/site.css` — moved; unchanged.
- `static/css/magazine.css` → `backend/static/css/magazine.css` — moved; modified.
- `static/img/book.webp` → `backend/static/img/book.webp` — moved; unchanged.
- `static/js/site.js` → `backend/static/js/site.js` — moved; unchanged.
- `static/js/magazine.js` → `backend/static/js/magazine.js` — moved; modified.
- `static/js/widgets.js` → `backend/static/js/widgets.js` — moved; unchanged.
- `news/management/__init__.py` → `backend/apps/news/management/__init__.py` — moved; unchanged.
- `news/migrations/0001_initial.py` → `backend/apps/news/migrations/0001_initial.py` — moved; unchanged.
- `news/migrations/__init__.py` → `backend/apps/news/migrations/__init__.py` — moved; unchanged.
- `news/migrations/0002_article_breaking_until_article_canonical_source_url_and_more.py` → `backend/apps/news/migrations/0002_article_breaking_until_article_canonical_source_url_and_more.py` — moved; unchanged.
- `news/management/commands/__init__.py` → `backend/apps/news/management/commands/__init__.py` — moved; unchanged.
- `news/management/commands/seed_demo.py` → `backend/apps/news/management/commands/seed_demo.py` — moved; modified.
- `news/management/commands/fetch_news.py` → `backend/apps/news/management/commands/fetch_news.py` — moved; modified.
- `news/management/commands/configure_sources.py` → `backend/apps/news/management/commands/configure_sources.py` — moved; modified.
- `media/2026/05/England-Womens-T20I.webp.webp` → `backend/media/2026/05/England-Womens-T20I.webp.webp` — moved; unchanged.
- `media/2026/06/India-T20I-squad-for-Ireland-England-Tour-2026-Full-squad-list-captain-schedule-and-key-selections-e.webp` → `backend/media/2026/06/India-T20I-squad-for-Ireland-England-Tour-2026-Full-squad-list-captain-schedule-and-key-selections-e.webp` — moved; unchanged.
- `media/2026/07/Abhishek-Sharma.jpg` → `backend/media/2026/07/Abhishek-Sharma.jpg` — moved; unchanged.
- `media/2026/07/BCCI-receives-directives-to-include-Rajat-Patidar-in-place-of-Tilak-Varma-in-T20Is.webp.webp` → `backend/media/2026/07/BCCI-receives-directives-to-include-Rajat-Patidar-in-place-of-Tilak-Varma-in-T20Is.webp.webp` — moved; unchanged.
- `media/2026/07/Babar-Azam-and-Mohammad-Amir.webp.webp` → `backend/media/2026/07/Babar-Azam-and-Mohammad-Amir.webp.webp` — moved; unchanged.
- `media/2026/07/FotoJet-1-245.webp.webp` → `backend/media/2026/07/FotoJet-1-245.webp.webp` — moved; unchanged.
- `media/2025/08/Asset-Allocation-Diversification-and-Rebalancing-A-Comprehensive-Guide.png` → `backend/media/2025/08/Asset-Allocation-Diversification-and-Rebalancing-A-Comprehensive-Guide.png` — moved; unchanged.
- `docs/previews/article-desktop.png` → `docs/archive/previews/article-desktop.png` — moved; unchanged.
- `docs/previews/article-mobile.png` → `docs/archive/previews/article-mobile.png` — moved; unchanged.
- `docs/previews/dark.png` → `docs/archive/previews/dark.png` — moved; unchanged.
- `docs/previews/home-desktop.png` → `docs/archive/previews/home-desktop.png` — moved; unchanged.
- `docs/previews/home-mobile.png` → `docs/archive/previews/home-mobile.png` — moved; unchanged.
- `docs/previews/menu-open.png` → `docs/archive/previews/menu-open.png` — moved; unchanged.
- `docs/enhancement/final-system-check.txt` → `docs/archive/enhancement/final-system-check.txt` — moved; unchanged.
- `docs/enhancement/final-migration-check.txt` → `docs/archive/enhancement/final-migration-check.txt` — moved; unchanged.
- `docs/enhancement/final-django-tests.txt` → `docs/archive/enhancement/final-django-tests.txt` — moved; unchanged.
- `docs/enhancement/provider-smoke.json` → `docs/archive/enhancement/provider-smoke.json` — moved; unchanged.
- `docs/enhancement/preservation-check.json` → `docs/archive/enhancement/preservation-check.json` — moved; unchanged.
- `docs/enhancement/live-source-checks.json` → `docs/archive/enhancement/live-source-checks.json` — moved; unchanged.
- `docs/enhancement/browser-results.json` → `docs/archive/enhancement/browser-results.json` — moved; unchanged.
- `docs/enhancement/supplemental-results.json` → `docs/archive/enhancement/supplemental-results.json` — moved; unchanged.
- `docs/enhancement/supplemental.cjs` → `docs/archive/enhancement/supplemental.cjs` — moved; unchanged.
- `docs/enhancement/final-desktop.png` → `docs/archive/enhancement/final-desktop.png` — moved; unchanged.
- `docs/enhancement/final-mobile.png` → `docs/archive/enhancement/final-mobile.png` — moved; unchanged.
- `docs/enhancement/mobile-hero.png` → `docs/archive/enhancement/mobile-hero.png` — moved; unchanged.
- `docs/enhancement/home-360.png` → `docs/archive/enhancement/home-360.png` — moved; unchanged.
- `docs/enhancement/home-390.png` → `docs/archive/enhancement/home-390.png` — moved; unchanged.
- `docs/enhancement/home-768.png` → `docs/archive/enhancement/home-768.png` — moved; unchanged.
- `docs/enhancement/home-1024.png` → `docs/archive/enhancement/home-1024.png` — moved; unchanged.
- `docs/enhancement/article-desktop.png` → `docs/archive/enhancement/article-desktop.png` — moved; unchanged.
- `docs/enhancement/article-mobile.png` → `docs/archive/enhancement/article-mobile.png` — moved; unchanged.
- `docs/enhancement/archive.png` → `docs/archive/enhancement/archive.png` — moved; unchanged.
- `docs/enhancement/search.png` → `docs/archive/enhancement/search.png` — moved; unchanged.
- `docs/enhancement/contact.png` → `docs/archive/enhancement/contact.png` — moved; unchanged.
- `docs/enhancement/reduced-motion.png` → `docs/archive/enhancement/reduced-motion.png` — moved; unchanged.
- `docs/enhancement/widgets-dropdown.png` → `docs/archive/enhancement/widgets-dropdown.png` — moved; unchanged.
- `docs/enhancement/palette-dropdown.png` → `docs/archive/enhancement/palette-dropdown.png` — moved; unchanged.
- `docs/enhancement/language-disabled.png` → `docs/archive/enhancement/language-disabled.png` — moved; unchanged.
- `docs/enhancement/widget-calculator.png` → `docs/archive/enhancement/widget-calculator.png` — moved; unchanged.
- `docs/enhancement/widget-units.png` → `docs/archive/enhancement/widget-units.png` — moved; unchanged.
- `docs/enhancement/widget-calendar.png` → `docs/archive/enhancement/widget-calendar.png` — moved; unchanged.
- `docs/enhancement/widget-clock.png` → `docs/archive/enhancement/widget-clock.png` — moved; unchanged.
- `docs/enhancement/widget-currency-disabled.png` → `docs/archive/enhancement/widget-currency-disabled.png` — moved; unchanged.
- `docs/enhancement/widget-weather-disabled.png` → `docs/archive/enhancement/widget-weather-disabled.png` — moved; unchanged.
- `docs/enhancement/widget-weather-fixture.png` → `docs/archive/enhancement/widget-weather-fixture.png` — moved; unchanged.
- `docs/enhancement/light-ocean.png` → `docs/archive/enhancement/light-ocean.png` — moved; unchanged.
- `docs/enhancement/light-violet.png` → `docs/archive/enhancement/light-violet.png` — moved; unchanged.
- `docs/enhancement/light-emerald.png` → `docs/archive/enhancement/light-emerald.png` — moved; unchanged.
- `docs/enhancement/light-sunset.png` → `docs/archive/enhancement/light-sunset.png` — moved; unchanged.
- `docs/enhancement/dark-ocean.png` → `docs/archive/enhancement/dark-ocean.png` — moved; unchanged.
- `docs/enhancement/dark-violet.png` → `docs/archive/enhancement/dark-violet.png` — moved; unchanged.
- `docs/enhancement/dark-emerald.png` → `docs/archive/enhancement/dark-emerald.png` — moved; unchanged.
- `docs/enhancement/dark-sunset.png` → `docs/archive/enhancement/dark-sunset.png` — moved; unchanged.
- `docs/enhancement/README.md` → `docs/archive/enhancement/README.md` — moved; unchanged.

## Added source/documentation files

- `.dockerignore`
- `.env.production.example`
- `.gitignore`
- `README.md`
- `backend/Dockerfile`
- `backend/apps/__init__.py`
- `backend/apps/news/apps.py`
- `backend/apps/news/migrations/0003_editorial_trust_tags_dedup.py`
- `backend/apps/news/migrations/0004_publisher_and_unique_title.py`
- `backend/apps/news/rest.py`
- `backend/apps/news/tests_rest.py`
- `backend/requirements-storage.txt`
- `backend/resources/reference-ads.txt`
- `backend/tests/verify_production_settings.py`
- `compose.yaml`
- `database/README.md`
- `database/backup-restore.md`
- `docs/AUDIT.md`
- `docs/DEPLOYMENT.md`
- `docs/HANDOVER.md`
- `docs/archive/move-manifest.json`
- `docs/deploy/nginx-container.conf`
- `docs/verification/browser-results.json`
- `docs/verification/collectstatic.txt`
- `docs/verification/desktop.png`
- `docs/verification/django-tests.txt`
- `docs/verification/extra-browser-results.json`
- `docs/verification/fail-closed.txt`
- `docs/verification/frontend-build.txt`
- `docs/verification/frontend-tests.txt`
- `docs/verification/migration-check.txt`
- `docs/verification/mobile.png`
- `docs/verification/netlify-live-status.txt`
- `docs/verification/npm-production-audit.json`
- `docs/verification/preservation.json`
- `docs/verification/production-security-harness.txt`
- `docs/verification/system-check.txt`
- `frontend/.env.example`
- `frontend/Dockerfile`
- `frontend/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/public/_redirects`
- `frontend/public/book.webp`
- `frontend/src/App.jsx`
- `frontend/src/components/Carousel.jsx`
- `frontend/src/components/StoryCard.jsx`
- `frontend/src/components/Widgets.jsx`
- `frontend/src/components/legacyWidgets.js`
- `frontend/src/context/Translation.jsx`
- `frontend/src/main.jsx`
- `frontend/src/pages/NewsPages.jsx`
- `frontend/src/services/api.js`
- `frontend/src/services/preferences.js`
- `frontend/src/styles/site.css`
- `frontend/tests/browser.cjs`
- `frontend/tests/config.test.js`
- `frontend/tests/routing.cjs`
- `frontend/vite.config.js`
- `netlify.toml`
- `docs/file-manifest.json`
- `docs/FILE_CHANGES.md`

## Removed files

No baseline source, database, original media, migrations or recovery payload was discarded. Generated caches/dependencies are excluded; verified duplicate animation behavior was consolidated in-place. The JSON inventory records the exhaustive mapped/modified/added source list.
