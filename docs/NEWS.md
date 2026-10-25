# News: fetching, images and translation

Run from the `backend` folder with the virtual environment active (see README). Same commands on Windows and Mac. Nothing here enables a scheduler.

## Inspect first (read-only)
```
python manage.py backend_status --sources
python manage.py news_report
```
`news_report` shows per-category public/draft counts, newest dates, source flags, image-policy state and recent fetch runs. It never prints keys.

## Manual fetch workflow
```
python manage.py fetch_news --source 1 --dry-run     # network + parse only, no writes
python manage.py fetch_news --source 1               # real import (draft unless source is trusted + auto_publish)
python manage.py news_report
```
Source ids are database ids (BBC India = 1, BBC World = 2 in your DB). `interval_minutes` / `next_fetch_at` throttle repeat fetches.
A scheduler (Windows Task Scheduler running `fetch_news` per source) should be added only after you approve it.

## Adding categories/sources (additive, nothing enabled)
```
python manage.py configure_sources
```
Creates missing categories and *disabled, rights-unconfirmed* candidate sources. You must review each publisher's terms, then in Django admin set
`rights_confirmed`, `enabled` (and optionally `trusted`/`auto_publish`). NewsAPI free plan: 100 requests/day, 24-hour delay, development use only
— not suitable for a public site; use a paid plan or licensed feeds for production. NewsAPI returns no tags, so use one source per category.

## Images (requires your authorisation)
To show BBC thumbnails you must decide that your BBC licence/permission covers it, then in admin set on that source
`allow_images=True` and `image_hosts=["ichef.bbci.co.uk"]`. BBC RSS thumbnails are small (240px). Then recover images for existing articles:
```
python manage.py backfill_images --source 1            # dry run
python manage.py backfill_images --source 1 --apply
```
It only fills empty image fields, never overwrites, never changes permissions. Reasons for rejections are printed per article.

## Translation
`.env`: `TRANSLATION_PROVIDER=disabled|libre|google`, `LIBRETRANSLATE_URL`, `TRANSLATION_API_KEY` (server-side only, never sent to the browser).
Until a provider works the site shows "Original English · translation is not configured". For LibreTranslate, start your local service with the language
models you want and set `libre`. Coverage: fixed UI strings plus the current page's public articles (about 24); items added by Load More stay English
until re-translated. Requests are rate-limited per IP (10 s). Google is billed per character; set a budget alert. Originals always stay available.

## Still needs your machine / permissions
Live DB state and migration status (`python manage.py showmigrations news`), `.env` values, publisher permissions above, LibreTranslate service/models,
Open-Meteo availability, deployment environment.
