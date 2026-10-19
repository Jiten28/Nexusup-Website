# NexusUp enhancement — pre-edit audit and implementation plan

## Status: baseline verified; animation identity needs confirmation before edits

The available Django source is the previous **NexusUp_Django_Demo.zip** delivery. It is not proven to be the latest client-maintained project. That ZIP has no sliding-news implementation. The public nexusup.in homepage still serves WordPress Digital Newspaper theme assets. The two supplied images are a layout sketch and a design reference, not additional application source.

No application source, media, database records, migrations or live services have been modified. No deployment performed. The unchanged original ZIP is the recoverable checkpoint; SHA-256: `aab866652e71ec005d6897fc36fa24381995791a2f9e596566bed39c37f77308`. An extracted baseline and per-file SHA-256 manifest were retained locally. No database reset or reseed was run against the supplied demo database. Tests seeded only their isolated temporary test database.

## 1. Django baseline audit

Reviewed models, views, URLs, forms, admin, feed/sitemap implementations, context processor, settings, dependencies, the initial migration, templates, CSS/JS, seed data and tests.

- Models: Category, Article, Comment, ContactMessage, plus Django auth/session tables. Article supports draft/published status, scheduled timestamps, featured flag, sample flag, image path/alt/credit, empty future WordPress-ID mapping and description. Categories are protected from accidental deletion while referenced.
- Data: ten articles, all marked sample. Categories: Cricket, Business, Stock Market, Investments, Technology and Science. No production schema or real content export is supplied.
- Views/URLs: home; `/stories/`; `/search/`; `/category/<slug>/`; `/story/<slug>/`; contact and information pages; `/feed/`; `/sitemap.xml`; robots; ads.txt; standard Django admin. Search and pagination are server-side; draft/future content is excluded from public queries. Do not change existing routes during enhancement.
- Homepage: `templates/news/home.html`; one large story on the left and a text short list on the right; six latest cards in a three-column grid. It does not yet match the requested center-feature/two-left/two-right layout.
- Branding: archive-derived open-book logo at `static/img/book.webp`; NexusUp text wordmark. Warm off-white/forest-green/rust styling in `static/css/site.css`. This is the baseline to recolor, not unrelated reference branding.
- JS: `static/js/site.js` implements mobile navigation/Escape, system-aware light/dark preference using the `nexusup-theme` storage key, per-story browser-local saves and copy-link feedback. It contains NO slider, marquee or ticker code. The homepage/base templates likewise contain no animated-news strip. CSS has decorative hover transitions and reduced-motion rules, not a news animation.
- Media: seven original raster files at `media/YYYY/MM/...`; local `/media/` and `/wp-content/uploads/` aliases in DEBUG mode. Preserve these files and paths. Production media alias remains a deployment concern.
- Settings: SQLite demo; environment-based MariaDB backend configuration for production, not tested against an actual MariaDB server. CSRF, template escaping, auth and standard middleware present. Contact storage is local; no outbound email. Demo is deliberately noindex; advertising disabled.
- Dependencies: Django 5.2.18; production extras mysqlclient and Gunicorn. No frontend framework or animation library in Django. One initial migration exists and is consistent with models.
- News sources: no NewsSource model, feed ingestion adapter, scheduler, provenance fields, import ledger or fetch-status tracking. The RSS endpoint is OUTPUT, not an ingestion source. Existing manual articles must be retained, not overwritten.
- Missing requested enhancements: utility dropdown, visitor-local header/date/city, independent accent palettes, language service, automatic source ingestion and breaking-status eligibility. These must be additive features, not represented as already existing.

## 2. Original animation findings: WordPress, not Django

Read-only live HTML loads WordPress theme.js, Slick and jquery.marquee. Downloaded live theme.js and jquery.marquee match the supplied WordPress archive after line-ending normalization. Relevant source URLs:

- https://nexusup.in/
- https://nexusup.in/wp-content/themes/digital-newspaper/assets/js/theme.js?ver=1.1.18
- https://nexusup.in/wp-content/themes/digital-newspaper/assets/lib/js-marquee/jquery.marquee.min.js?ver=1.6.0

### Candidate A — continuously sliding “Headlines” strip below the header

- Renderer: `wp-content/themes/digital-newspaper/inc/hooks/header-hooks.php`, function `digital_newspaper_ticker_news_part()` (around lines 273–339).
- Item template: `template-parts/ticker-news/template-three.php`. Each item contains a featured-image link, date metadata and headline link.
- JS: `assets/js/theme.js`, around lines 30–46; selector `.ticker-news-wrap .ticker-item-wrap`; jQuery marquee implementation in `assets/lib/js-marquee/jquery.marquee.min.js`.
- Direction: left for LTR; right when body has `rtl`.
- Configuration: `duration: 40000`, `gap: 0`, `delayBeforeStart: 0`, `duplicated: true`, `startVisible: true`, `pauseOnHover: true`.
- Transition: linear scrolling, CSS3 transforms where supported with a jQuery animation fallback. The plugin derives traversal duration from content/container dimensions, so 40,000 ms is the configuration input, not a browser-measured fixed full-content cycle across every width.
- Looping: plugin internally clones the item sequence for continuity. If adapted, duplicate accessibility/focus targets must be handled without visible duplicate fragments or seam jumps.
- Controls: `.digital-newspaper-ticker-pause` toggles pause/resume and icon; hover pauses. No focus-within pause or prefers-reduced-motion handling was found in this initialization.
- Responsive code: theme `assets/css/responsive.css` hides the pause controls under the `max-width: 610px` media block. The supplied behavior should be improved accessibly, not reproduced with that control limitation.
- Live HTML contains this exact strip with label “Headlines”, direction left and six item elements. No claim of frame-by-frame live animation timing or flicker validation has been made; this turn audited source, not a live browser recording.

### Candidate B — separate upper-header rotating headlines

- Renderer: `inc/hooks/top-header-hooks.php`, `digital_newspaper_top_header_ticker_news_part()`.
- JS: `assets/js/theme.js`, around lines 176–189; `.top-ticker-news .ticker-item-wrap` initialized with Slick.
- Vertical one-at-a-time transitions, infinite loop, autoplay and previous/next arrow buttons, no dots. Theme initialization does not override Slick's 3,000 ms autoplay interval or 500 ms transition defaults. Default Slick pause-on-hover/focus applies. These are code settings, not browser-measured timing.
- Live HTML contains this component as well. It is distinct from Candidate A; neither is an existing Django component in the available ZIP.

**Blocking ambiguity:** confirm whether Candidate A is the recognizable original animation to carry into the previous Django project, whether Candidate B is also required, or whether a newer Django project contains a different animation. Do not silently introduce a new implementation and describe it as preserved existing Django code.

## 3. Checks actually executed this turn

- `python manage.py check` — PASS, no issues.
- `python manage.py makemigrations --check --dry-run` — PASS, no changes detected.
- `python manage.py test -v 1` — PASS, 21 tests, using a separate temporary test database.
- Live HTML and two original animation assets retrieved read-only; source match confirmed.
- Existing database inspected in SQLite read-only mode: ten samples, six categories.
- Browser tests, redesign renders, API integration tests, MariaDB execution and production access NOT performed this turn. Prior packaged test reports are historical evidence only, not newly executed browser tests.

## 4. Concise staged implementation plan — pending baseline/animation confirmation

1. Lock the confirmed project baseline, back up database/media, record source hashes and retain all existing migrations/tests/routes. If a newer ZIP is provided, audit it before changing it.
2. Preserve/adapt the confirmed original animation as a separately named component. Record direction, timing and controls; add focus/hover pause, accessible controls and reduced-motion static layout. Keep breaking news separately eligibility-driven; no fake LIVE status or sample breaking claims.
3. Introduce shared design tokens for Ocean Blue, Vibrant Violet, Emerald and Sunset in BOTH appearances. Keep independent persistence for accent palette and light/dark, preserving the existing appearance key. Apply tokens across cards, forms, nav, ticker, widgets and focus states; retain logo/media.
4. Adapt the existing header/home templates: device-timezone time/date; reliable known/manual location only; compact header utilities/language/search controls; category filters below news strips; 2-left/large-center/2-right feature; readable 4/3/2/1-column lower grid at suitable widths. No below-grid widget section and no whole-project replacement.
5. Add compatible source/provenance/fetch-status models and migrations, feed/API adapter interface, scheduled management command, normalization/deduplication, category mapping, draft-first visibility, fetch logs and last-valid-content fallback. Validate publisher feed availability AND reuse permissions before enabling a source. Scheduling is off-request; no full-article scraping or hardcoded secrets. Preserve manual articles and existing admin; enhance source/feature controls there.
6. Implement calculator, world clock, calendar and unit conversion locally. Choose documented currency/weather providers; configurable, cached server-side adapters, timestamped results and explicit unavailable states. Geolocation only after user action; manual city fallback. Evaluate current Google/widget/paid-API/alternative translation terms, availability, coverage and cost before choosing; backend secrets only, original text retained, honest unsupported/error states. Do not promise universal translation or activate production accounts without approval.
7. Run existing regression tests plus ingestion/malformed-feed/rate-limit/deduplication tests; all six utility and language states; animation pause/resume/reduced-motion; every four-palette/two-appearance combination; viewport checks at 360, 390, 768, 1024 and 1440px. Compare visual snapshots and source behavior, fix regressions, then deliver updated ZIP, migration/scheduling/provider setup, exact changed/removed file list and actual test results.

## 5. File-change report at this checkpoint

Modified/removed existing application files: **none**.
New audit-only artifacts outside the application: this report, backup/checkpoint metadata, baseline file hashes, test log, read-only live HTML/source match evidence and extracted WordPress theme reference excerpts. The application database, original archive and previous Django ZIP remain intact. No feature implementation is marked complete.
