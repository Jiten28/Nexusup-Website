# Changelog

All changes are source-only. No database, `.env`, source approval, migration or scheduler was touched.
Checkpoint of the css before cleanup: kept out of the archive; the original upload is unchanged.

## 1. Images
Root cause: images are **default-deny**. A feed image is stored only when the source has `allow_images=True`
AND the exact host is in `image_hosts` (https only). Both BBC sources currently have neither, so every image was
(correctly) discarded. That is a permission, not a bug, and this pass does not change it.
Real defects fixed: widest declared candidate was not chosen; no way to recover images for articles imported earlier;
no `referrerPolicy`; no diagnostics.
- `backend/apps/news/images.py` (new) · `ingestion.py` · `management/commands/backfill_images.py` (new, dry-run by default) · `news_report.py` (new)
- `frontend/src/components/StoryCard.jsx` (`decoding=async`, `referrerPolicy=no-referrer`, fallback marker)

## 2. Homepage layout (hand-drawn sketch)
1 large centre lead, 2 stacked cards left, 2 right, lower 4-column grid, one "Load More News" button, slider stories excluded.
`frontend/src/pages/NewsPages.jsx` (`composeLatest`, page size 13) · `frontend/src/styles/site.css` (100 dead/conflicting rules removed, one consolidated section).

## 3. Slider
`frontend/src/components/Carousel.jsx` rewritten: one horizontal CSS-transform track, equal slide size, one `setTimeout`
(never an interval), pause on hover/focus/hidden tab, swipe, prev/next/indicators/play-pause, reduced motion.
Found by the browser test: native image drag cancelled swipes → `onDragStart` prevented.

## 4–5. Categories and freshness
- `rest.py`: category `article_count`; UI hides categories with zero stories (nothing is deleted).
- `configure_sources.py`: additive candidate sources (BBC section feeds, NewsAPI queries) created **disabled and unapproved**.
- Ordering/dedupe/pagination unchanged (already source-date ordered; covered by existing tests).

## 6. Article pages
`NewsPages.jsx` `ApiStory`: headline, permitted image, date, source box, original link (`noopener noreferrer`), honest notice; feed summaries are never shown as full text.

## 7. Translation
`ui_strings.py` (new, 41 UI strings), `api.py` (corpus = UI strings + public articles), `App.jsx` (`Language` component loads languages on mount, remembers choice, re-translates on navigation, RTL).
Provider stays `disabled` until you configure it; see `docs/NEWS_COVERAGE_AND_FETCHING.md`.

## 8. Tests
- `frontend/tests/acceptance.cjs` (new, 22 checks), `fixtures.cjs`, `ui-strings.test.js` (new), `layout-sketch.test.js` (updated)
- Stale suites moved to `frontend/tests/archive/` (they targeted removed selectors).
- `backend/apps/news/tests_images.py`, `tests_coverage.py` (new)


## Second pass: restructure, themes, MariaDB

**Structure.** Project is now `backend/`, `frontend/`, `database/` (+ `docs/`). Removed: 27 MB of historical audit archives, stale
per-version docs, demo-preview mode (`frontend/src/preview`, `public/preview`), Netlify/Docker deployment files, old browser suites,
`EXPORT/`, one-off backend helper scripts, split requirements files. Layout/version names (hand-drawn, V6-V8, sketch) removed from files, CSS classes and tests.

**Themes.** Six new bold palettes (Royal Indigo, Crimson Ember, Teal Wave, Forest Lime, Amber Sunrise, Rose Magenta), each with light and dark
tokens and an `--accent-2` gradient colour; Light / Dark / Auto mode switch; theme menu with swatches; old saved palette ids map to the new ones.
New "Design layer" at the end of `site.css` restyles buttons, header/nav, slider, filters, cards, article page and footer without touching grid/layout rules.

**MariaDB.** `database/compose.yaml` (MariaDB 11.4, utf8mb4, localhost-only port, persistent volume); `database/scripts/db.ps1` and `db.sh`:
up, create, status, export, import, from-sqlite, down, reset. PyMySQL fallback in `backend/config/__init__.py` (no compiler needed on Windows/Mac);
`DB_HOST` defaults to 127.0.0.1. SQLite remains supported for quick local use.
