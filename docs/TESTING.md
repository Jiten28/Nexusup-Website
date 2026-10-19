# Testing record — 18 October 2026

## Automated Django suite: PASS
Environment: Python 3.13, Django 5.2.18, isolated local SQLite. `python manage.py test -v 2`: **21 tests passed**. The test runner creates and destroys a separate in-memory database; it does not modify a WordPress or production database.

Coverage: core routes; unknown article/category 404s; search and empty results; query escaping; category isolation; pagination and invalid page values; draft/future publication visibility across list/detail/feed/sitemap; pending/approved comments and cooldown; stored-comment HTML escaping; CSRF rejection; local contact storage with zero mail; validation/honeypot; seed idempotence; sample labels/noindex/canonical; safe existing media paths; disabled vs exact opt-in ads.txt; absence of provider script references; admin authentication; unusable demo-author password; robots; reading-time bounds; authenticated admin article publication and comment approval.

`manage.py check`: no issues. `makemigrations --check --dry-run`: no changes detected. Full test output: `test-results.txt`.

## Real local Chromium checks: PASS
`browser-results.json`: **34 route/viewport combinations** (17 routes at 1440px and 390px), all HTTP 200, no horizontal overflow, all image assets decoded, zero page JavaScript errors and zero non-local network requests. It covers home, both archive pages, all six categories, successful/empty/150-character unbroken search, article, contact and information pages.

Interaction assertions passed: mobile menu open; Escape close/focus behavior; persistent dark theme; persistent per-story browser save; clipboard success/failure feedback; real search-form submission; visible navigation with JavaScript disabled. The test scrolls pages and then forces off-screen lazy assets to eager/decode for deterministic asset validation. The application itself retains lazy loading.

Optional reproduction: with the loopback demo running, install Playwright in a separate Node QA environment (`npm install --no-save playwright`), ensure the `chromium` executable is available, and run `node scripts/browser_qa.cjs`. Playwright is a QA dependency only, not a frontend/application dependency. This browser runner targets loopback exclusively.

## Visual inspection: PASS for reviewed layouts/states
Rendered with local Chromium and the bundled HTML capture helper, then opened and visually inspected individually, not merely generated:
- Desktop and mobile home (1440 and 390px); final preview above the fold.
- Desktop and mobile article, including related imagery, sample notice and moderated-comment form.
- Desktop archive and mobile filtered category archive, including selected navigation/search.
- Mobile search empty state and validation-error form; desktop normal contact form.
- Desktop about page; mobile privacy and terms pages; custom 404.
- Dark homepage and expanded mobile menu.

Verified no visible overlap, no horizontal clipping, readable labels, coherent spacing, image framing, functional responsive reading order and clearly labeled samples. Full-page snapshot rendering uses eager image loading only in the QA copies so off-screen images are captured. Typography/contrast and an awkward search-button wrap were refined during QA; a low-resolution sample image was replaced with a clearer supplied reference. Screenshots are included under `docs/previews/` for selected final views.

## Media helper dry run: PASS, no writes
4,022 dated raster files eligible, 207,037,082 bytes; 4,015 not bundled; 0 conflicts with the seven included assets. 2,304 non-dated/non-raster uploads excluded deliberately. No `--apply` restoration was executed. Exact output: `media-restore-dry-run.json`. Original archive CRC and extraction checks cover all members, separate from this helper.

## Explicitly NOT tested or certified
- MariaDB/mysqlclient execution, SQL source import or production-schema mapping.
- Production services, deployment, HTTPS/proxy/media configuration, SMTP, analytics, translation, ad delivery or consent compliance.
- Full WordPress behavior parity, automated migration accuracy, source plugin authenticity/security/licenses, exhaustive image rights, malware scans, load/concurrency behavior, formal WCAG audit or screen-reader usability.
- The in-memory/session throttle is not a production abuse-control guarantee.

These results establish a local working demo, not production readiness. See the migration plan for remaining acceptance gates.
