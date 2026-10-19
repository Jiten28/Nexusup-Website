> **Historical baseline document.** This describes the previous demo. For this incremental enhancement, use `ENHANCEMENT_REPORT.md`, `INTEGRATIONS.md` and `enhancement/` test evidence.

# Implementation handoff

## Architecture
`config/` handles settings, URL routing and WSGI. `news/` owns the proposed ORM models, views, forms, admin, feed, sitemap, seed data and tests. `templates/` is server-rendered Django HTML. `static/css/site.css` is the responsive editorial design; `static/js/site.js` provides progressive enhancement only. `media/YYYY/MM/` contains seven unmodified reference raster files. The book logo is `static/img/book.webp`.

No WordPress PHP, plugin implementations, cache contents, plugin fonts, API keys or vendor code are included in the application. Complete filenames/sizes are retained in the audit listings, not copied as executable code. The original supplied publisher ID is a public declaration in docs; advertising remains disabled.

## Route map
- `/` — featured sample story, short list, latest cards, category links, disabled ad space.
- `/stories/`, `/search/?q=...` — six articles per page; search is case-insensitive substring matching, not relevance-ranked/full-text search.
- `/category/<slug>/` — filtered category archive.
- `/story/<slug>/` — article detail, escaped plain text, metadata, image/credit, browser save/copy, moderated local comments, related category stories.
- `/about/`, `/privacy/`, `/terms/` — demo context and non-production notices.
- `/contact/` — validated local-only storage; no email.
- `/feed/`, `/sitemap.xml` — published, non-future article data only. `SITE_URL` defines canonical/sitemap/feed links. Sitemap is for the demo's article routes, not an exhaustive production sitemap.
- `/robots.txt` — intentionally blocks all crawling; templates also emit noindex/nofollow.
- `/ads.txt` — disabled response; explicit opt-in serves exact reference only.
- `/admin/` — standard authenticated Django editorial/moderation interface; create an admin locally, no credentials shipped.
- Debug-only `/media/` and `/wp-content/uploads/` — same selected dated files. Production media serving is not implemented by Django views.

## Verified preservation / proposed changes
Preserved reference evidence: book logo; original image bytes and dated paths; original ads declaration as inert reference; article/category/author/date/read-time patterns; broad homepage topic navigation. The new layout and sample taxonomy/editorial flow are proposals. Footer links and legal/demo pages are newly written, not reconstructed from unknown WordPress database records. Comments are proposed flat/moderated storage, not a migrated legacy community. Translation/automation/SMTP/analytics/backups are intentionally not connected.

## Design decisions
Warm near-white canvas, forest-green ink/actions, restrained rust accent, system sans UI with a system serif editorial voice; comfortable reading column; no remote fonts. Native system-aware dark mode is supported with a local override. Mobile collapses navigation through JS; without JS the nav remains visible. Text-only topics use intentionally typographic cards rather than fabricated imagery. All articles visibly carry sample labels, with an explicit explanatory notice on detail pages.

## Security posture and outstanding work
CSRF middleware, template escaping, ORM query parameters, admin auth, password validation, draft/future publication filters, honeypot and local per-session cooldown are implemented. Production settings fail closed for missing MariaDB/secret/HTTPS origin. This is NOT a security certification. Complete abuse protection, shared cache/rate limiting, trusted-proxy settings, database TLS as required, retention controls, dependency review, logging, backup/restore drills, file MIME/malware checks and a production privacy/consent review before launch. Explicit host environment values are required; no credential or remote database is guessed.
