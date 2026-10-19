# NexusUp — incremental Django magazine enhancement

This package enhances the working Django demo supplied as **NexusUp_Django_Demo.zip**, not a replacement Django application. The live WordPress site has not been changed. Existing routes, data, manual publishing, media paths and original features remain. The ten supplied stories are still clearly labeled illustrative samples, not current reporting. No production data was supplied/imported.

Start with **docs/ENHANCEMENT_REPORT.md** for implemented features, file changes, executed tests and limitations; **docs/INTEGRATIONS.md** for activation, licensing and scheduler setup. `docs/PRE_EDIT_AUDIT.md` records the audit/plan and original animation source findings before implementation. The original source ZIP and its checksum are included under `recovery/` in the delivery.

## Run locally (Python 3.10+; tested on Python 3.13)

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py configure_sources
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/` on that computer. The bundled SQLite database contains the original ten samples plus additive source/category tables/configuration. **Do not overwrite your own database with it.** If installing without the demo database, `python manage.py seed_demo` creates illustrative samples (optional, never required on a real editorial database). It does not import production content. Windows: `py -m venv .venv`, then `.venv\Scripts\activate` and the same Python commands.

```sh
python manage.py createsuperuser
```

Choose credentials interactively, then open `/admin/`. No usable administrator credentials ship with this package. Draft/future articles stay private. Admin supports manual articles, categories, featured selection, source/review management, scheduled publication timestamps, comments and contact submissions. Contacts are saved locally, not emailed.

## Included

- Blue magazine design, a large center feature/two stories each side, responsive lower grid (4/3/2/1 columns as space allows), refined article/archive/search/forms/footer.
- Independent persistent Light/Dark and four-palette Color Theme controls; system preference when no appearance is stored.
- Separate image-based vertical headline slider and continuously left-scrolling Headlines strip, adapted from audited original WordPress behavior; actual story images, clickable headlines/source metadata, controls, pause/focus/hover and reduced-motion alternatives.
- Header local date/time, language control, location action, Widgets dropdown: calculator, currency, weather, world clock, calendar, unit converter.
- Opt-in, server-side scheduled RSS/Atom ingestion, URL dedup, source/category mapping, draft review, permitted image URLs, status/error tracking, safe fallbacks. API-adapter registry is extensible; no paid news API is configured.
- Opt-in Google Cloud / LibreTranslate adapters, no frontend secrets and no arbitrary markup replacement. Translation is partial localization; see integration limits.
- Existing article/related stories, search/category pagination, reading times, browser-local saves, copy link, form validation/moderation, RSS/sitemap, canonical/Open Graph, CSRF and dated media paths retained.

## Test

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
# Optional browser tests; install Playwright separately and supply local Chromium path if necessary:
npm install --no-save playwright
CHROMIUM_PATH=/path/to/chromium QA_OUT=/tmp/nexusup-qa node scripts/enhancement_qa.cjs
```

Browser suite requires the local sample-only server already running. It uses fixtures for paid-provider success paths and real disabled-provider error states. It does not contact external providers or submit real personal information. Actual logs and preview screenshots are included under `docs/enhancement/`.

## Boundaries and safe rollout

- External feeds, currency/weather and translation are disabled by default. `configure_sources` adds only **disabled** source candidates. Scheduler example is not installed. Review rights, consent, service licensing, credentials, quotas and logs before enabling. `.env.example` lists variables; export them explicitly (no dotenv auto-loader).
- Original WordPress JS/PHP libraries were inspected, not copied into Django. Available Django baseline contained neither news animation; these are source-informed accessible adaptations, not a claim that previously absent Django animation code was preserved byte-for-byte.
- Production MariaDB, WSGI/reverse proxy, SMTP, actual content migration, legal policy/rights clearance, full assistive-technology/RTL testing, load/penetration tests and production monitoring remain unverified. See historical `docs/MIGRATION_PLAN.md` for real-data migration gates. Never apply Django migrations to the WordPress database.
- Production uses a separately provisioned MariaDB database, `requirements-production.txt`, private environment secrets, approved HTTPS `SITE_URL`, `DB_ENGINE=mariadb` and `DJANGO_DEBUG=0`. Settings fail closed without these. Current cache/rate limits are demo-only, per-process; install shared production controls before exposing provider endpoints.
- Demo stays `noindex,nofollow`; ads disabled; no analytics/tracking or outbound email is enabled. Sample policies are not legal sign-off. Supplied reference images/logo need publication-rights review. No live deployment or source-rights approval is implied.

The original source is recoverable; no original project files were removed. `docs/FILE_CHANGES.md` lists the exact delta.
