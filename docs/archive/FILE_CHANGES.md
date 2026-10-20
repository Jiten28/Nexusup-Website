# File changes relative to supplied Django baseline

No original project files removed. demo.sqlite3 received only additive migration/category/source configuration; original article fields and media hashes were verified unchanged. Generated caches and local .git data are excluded from the distributable, not deleted from the working project.

## Modified (19)

- `.env.example`
- `README.md`
- `START_HERE.md`
- `config/settings.py`
- `config/urls.py`
- `demo.sqlite3`
- `docs/AUDIT.md`
- `docs/IMPLEMENTATION.md`
- `docs/TESTING.md`
- `news/admin.py`
- `news/context.py`
- `news/models.py`
- `news/views.py`
- `requirements.txt`
- `templates/base.html`
- `templates/news/article.html`
- `templates/news/card.html`
- `templates/news/home.html`
- `templates/news/list.html`

## Added (65)

- `deploy/news-fetch.cron.example`
- `docs/ENHANCEMENT_REPORT.md`
- `docs/FILE_CHANGES.md`
- `docs/INTEGRATIONS.md`
- `docs/PRE_EDIT_AUDIT.md`
- `docs/enhancement/README.md`
- `docs/enhancement/archive.png`
- `docs/enhancement/article-desktop.png`
- `docs/enhancement/article-mobile.png`
- `docs/enhancement/browser-results.json`
- `docs/enhancement/contact.png`
- `docs/enhancement/dark-emerald.png`
- `docs/enhancement/dark-ocean.png`
- `docs/enhancement/dark-sunset.png`
- `docs/enhancement/dark-violet.png`
- `docs/enhancement/final-desktop.png`
- `docs/enhancement/final-django-tests.txt`
- `docs/enhancement/final-migration-check.txt`
- `docs/enhancement/final-mobile.png`
- `docs/enhancement/final-system-check.txt`
- `docs/enhancement/home-1024.png`
- `docs/enhancement/home-360.png`
- `docs/enhancement/home-390.png`
- `docs/enhancement/home-768.png`
- `docs/enhancement/language-disabled.png`
- `docs/enhancement/light-emerald.png`
- `docs/enhancement/light-ocean.png`
- `docs/enhancement/light-sunset.png`
- `docs/enhancement/light-violet.png`
- `docs/enhancement/live-source-checks.json`
- `docs/enhancement/mobile-hero.png`
- `docs/enhancement/palette-dropdown.png`
- `docs/enhancement/preservation-check.json`
- `docs/enhancement/provider-smoke.json`
- `docs/enhancement/reduced-motion.png`
- `docs/enhancement/search.png`
- `docs/enhancement/supplemental-results.json`
- `docs/enhancement/supplemental.cjs`
- `docs/enhancement/widget-calculator.png`
- `docs/enhancement/widget-calendar.png`
- `docs/enhancement/widget-clock.png`
- `docs/enhancement/widget-currency-disabled.png`
- `docs/enhancement/widget-units.png`
- `docs/enhancement/widget-weather-disabled.png`
- `docs/enhancement/widget-weather-fixture.png`
- `docs/enhancement/widgets-dropdown.png`
- `news/api.py`
- `news/ingestion.py`
- `news/management/commands/configure_sources.py`
- `news/management/commands/fetch_news.py`
- `news/migrations/0002_article_breaking_until_article_canonical_source_url_and_more.py`
- `news/network.py`
- `news/services.py`
- `news/tests_enhancements.py`
- `recovery/NexusUp_Django_Demo.zip`
- `recovery/baseline-file-hashes.json`
- `recovery/checkpoint.json`
- `scripts/enhancement_qa.cjs`
- `static/css/magazine.css`
- `static/js/magazine.js`
- `static/js/widgets.js`
- `templates/news/animations.html`
- `templates/news/feature-card.html`
- `templates/news/header.html`
- `templates/news/widgets.html`

## Removed

None.
