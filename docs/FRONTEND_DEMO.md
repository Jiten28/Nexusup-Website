# NexusUp — frontend demo polish

This is a targeted enhancement of the existing React/Vite frontend. The Django backend, NewsAPI adapter/configuration, database, media, deployment profiles and DNS were not changed. This report supersedes the earlier handover's four-palette/carousel descriptions for the frontend only.

## Diagnosis before editing

The inspected `/api/home/` response contained **four carousel records and five featured records**. Only **one carousel record had an image URL**; the other three used the generic image fallback. The ten published records in the supplied database are existing labeled samples, not a live provider feed.

The backend reserves a primary featured story plus four supporting stories before selecting up to four remaining carousel stories. Its nine excluded IDs leave only one stored story for Latest News. The old frontend rendered a small 84–100px thumbnail beside each headline, divided the track into three/four card-width columns, omitted excerpts and indicators, and navigated by scroll offsets without an active-slide model. Together, sparse image selection and thumbnail rendering explain the reported small-story/empty-space appearance. The current local response was **not literally a one-record response**; no unverifiable claim is made about a different client's API/deployed revision.

## What changed

- One full-width, image-led carousel, with up to five unique stories, category, headline, summary, attribution, working link, active count and indicators.
- Previous/next wrap correctly, and single-story controls disable appropriately. Empty API content has an honest empty state outside demo mode.
- Manual navigation is the default. Explicit Play uses a six-second interval; hover, focus and hidden tabs pause it. Reduced motion disables autoplay and animations while retaining manual navigation. No ticker, second carousel or vertical slider was introduced.
- The existing centered primary story, supporting stories, categories, Latest News, footer and brand remain. Card surfaces, spacing, type hierarchy and responsive imagery were refined. A mobile image-height inheritance bug discovered during visual review was corrected.
- Color Theme applies the next palette in one click. Its current name appears below the button. The six palettes are Midnight Coral, Ocean Editorial, Violet Night, Emerald Press, Sunset Journal and Graphite Gold.
- A Fisher–Yates shuffled bag contains each theme exactly once per six-click cycle. The bag and current theme persist across reloads when storage is available; cycle boundaries avoid an immediate repeat. Old palette keys migrate to corresponding new names. Light/dark remains a separate persisted choice and never changes when cycling palettes.
- Each palette defines light and dark page/surface/text/muted/border/accent/soft-accent/on-accent tokens. Header, navigation, cards, forms, buttons, footer and indicators share those tokens. Automated checks cover normal/muted/accent text against page, card and soft backgrounds, plus text on accent buttons (all >=4.5:1).

## API versus local preview — important

`npm run dev` and `npm run build` remain **API-only**. No fixture replaces API content in these normal modes.

`npm run demo` and `npm run build:demo` explicitly opt into a local client-demo mode. This checks the returned carousel selection. If it has fewer than three distinct records with a nonempty image URL, or the homepage request fails, the homepage displays a **separate, fully labeled local layout preview**. The image-URL check is an availability heuristic, not proof that a remote image will resolve; image errors still use the existing fallback.

The preview has 18 fictional, illustrative editorial fixtures: five carousel stories, five featured stories and eight latest stories (four initially, with a controlled Load More). Sections do not repeat story IDs/titles. The six local WebP illustrations were AI-generated for this demo, not taken from a news provider or presented as documentary photography. Images may be reused for different illustrative articles; stories themselves are distinct.

A visible notice, story metadata and detail-page notices distinguish preview content from reporting. Preview slugs are reserved as `/story/local-preview-N/`. They resolve directly and on refresh in demo mode and never query or write the editorial database. No fixture comments are posted to Django.

**View API content** switches the homepage back to the actual stored selection. Search, main navigation, standard category links, genuine article pages and forms continue to use Django. The preview's category buttons filter only its Latest News grid; the notice explains that search/main navigation browse API content. If the API supplies at least three image-bearing carousel stories, demo mode uses the API homepage instead. Fixtures are never blended into public API rows or imported into Django.

Weather and translation are intentionally off in demo mode. Weather opens a calm explanatory panel without provider/geolocation requests; language selection retains original English with a discreet availability note. Normal mode retains the existing adapters unchanged. Calculator, units, world clock and calendar remain local and functional. Currency retains its existing adapter and honest unavailable state if unconfigured; it is not fetched merely by opening the homepage.

## Exact local commands

From the extracted project, open separate terminals. Python 3.12/3.13 and Node 22+ are recommended.

### Terminal 1 — existing backend

```sh
cd NexusUp/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
DJANGO_DEBUG=1 python manage.py runserver 127.0.0.1:8000 --noreload
```

These commands use the supplied existing development DB. Do not reset/reseed it. If dependencies are already installed, reuse the existing virtual environment. Preserve existing server-side provider settings; no key is required for the local fixture preview. Nothing needs to be added to React for NewsAPI.

### Terminal 2 — client demo

```sh
cd NexusUp/frontend
npm ci
npm run demo -- --port 5174
```

Open **http://127.0.0.1:5174/**. The unchanged Vite development proxy forwards `/api` and `/media` to the local Django server. `DEV_BACKEND_URL` can point to another approved local backend as before. This is a local preview, not a deployment.

### Optional normal API-only preview

```sh
cd NexusUp/frontend
npm run dev -- --port 5173
```

Open **http://127.0.0.1:5173/**. No frontend fixtures are used, even with sparse content.

### Tests and builds

```sh
cd NexusUp/frontend
npm test
npm run build          # normal API-only output: dist/
npm run build:demo     # opt-in preview output: dist-demo/; never overwrites dist/
npm run preview:demo -- --port 4174
```

The compiled demo is at **http://127.0.0.1:4174/**. Keep the backend running for API navigation/forms; preview pages work without configured external providers. Do not open `dist-demo/index.html` as a file URL.

With the API-only server on 5173 and demo server on 5174:

```sh
# Install a Playwright browser if one is not already available:
# npx playwright install chromium
npm run test:demo
# Or use a preinstalled Chromium explicitly:
CHROMIUM="$(command -v chromium)" npm run test:demo
# Equivalent current regression entrypoint:
CHROMIUM="$(command -v chromium)" npm run test:browser
# With the compiled demo server also running on 4174:
CHROMIUM="$(command -v chromium)" node tests/built-demo.cjs
```

`QA_BASE_URL`, `QA_DEMO_URL`, `QA_BUILT_DEMO_URL`, `QA_OUT` and `CHROMIUM` override test locations. Browser acceptance uses read-only backend GETs; contact submissions and pagination-edge responses are explicitly intercepted and are not stored. `tests/routing.cjs` additionally requires a same-origin staging verification proxy at `QA_BUILT_URL` (default 8088); this is an infrastructure-specific optional test, not needed to run the demo.

## Executed validation

| Check | Result |
|---|---|
| Frontend unit/config tests | **8 passed** |
| Six-theme shuffled cycle | 100 six-click cycles checked; no replacement or boundary repeat |
| Text/accent contrast | Passed for all 12 palette/mode combinations |
| Normal production build | Passed; output remains `dist/` |
| Opt-in demo production build | Passed; separate `dist-demo/` |
| Demo browser acceptance | **50 checks passed; zero console errors** |
| Additional browser/routing suite | **11 checks passed**, including built article refresh, missing-image fallback and reserved API/admin/static/media routes |
| Compiled demo smoke suite | **5 checks passed**, including direct story refresh and graceful API outage |
| Story counts | 0, 1, 3 and 5 tested in API-only and demo modes |
| Carousel interaction | Previous/next, wrap, indicators, Play/Pause, hover/focus pause and reduced motion |
| Responsive | 360, 390, 768, 1024 and 1440 px; no horizontal document overflow |
| Preserved UI | API search/category routes, article refresh, all six utility entries, local calculator/unit outputs, footer routes, mocked contact submission, API Load More deduplication |
| Backend preservation | All **68** packaged backend files match the previous delivery byte-for-byte, including SQLite, settings, NewsAPI code and original media |
| Database | Original SQLite SHA-256 unchanged; no reset, reseed or actual form write |
| Visual QA | Desktop/mobile and all 12 theme/mode renderings inspected; mobile feature-copy clipping fixed |

Builds emit existing non-blocking React Router `"use client"` directive warnings; both exit successfully. The compiled outage test deliberately injects HTTP 503 and records its expected browser resource warning separately; it produces **no page JavaScript errors**. This is not an error from missing weather/translation keys.

Evidence and exact changed-file list: `docs/verification/demo-polish/`. Earlier verification files elsewhere in the package are historical. Screenshots include `client-desktop.png`, `client-mobile.png`, responsive widths, preview article pages and all 12 theme/mode states. Offline QA snapshots are captures only, not alternative application source.

## Changed files

### Existing frontend files modified

- `frontend/package.json` — opt-in demo build/dev/preview and browser-test scripts; no new dependencies.
- `frontend/src/App.jsx` — one-click theme button and quiet disabled translation behavior in demo mode.
- `frontend/src/components/Carousel.jsx` — responsive image-led active-slide model and accessible controls.
- `frontend/src/components/StoryCard.jsx` — eager hero images, explicit preview provenance and optional featured summaries.
- `frontend/src/components/Widgets.jsx`, `legacyWidgets.js` — demo-only weather availability guard; retain normal adapter behavior.
- `frontend/src/pages/NewsPages.jsx` — deduplicated homepage selections, isolated preview fallback and preview detail routing.
- `frontend/src/styles/site.css` — theme-driven surfaces, carousel/card layout and responsive refinements.
- `frontend/tests/browser.cjs`, `config.test.js`, `routing.cjs` — current entrypoint/assertions for the replaced controls.

### Added

- `frontend/src/services/themes.js` — six token sets per mode, migration aliases and persisted shuffled cycle.
- `frontend/src/preview/data.js`, `Preview.jsx` — separate local fixtures, homepage and article views.
- `frontend/public/preview/{city,chip,observatory,mangrove,solar,cricket}.webp` — six generated illustrations.
- `frontend/tests/demo.test.js`, `demo.cjs`, `built-demo.cjs` — unit/browser/compiled-demo regression coverage.
- This report, demo verification logs/screenshots and generated build outputs included for handover.

Root `.gitignore` excludes `frontend/dist-demo/`; root README links to this report and reflects the six-theme UI. No files were deleted. The backend, provider credentials/configuration, migrations, database, deployment configuration, public route fallback rules, Vite proxy and package dependencies are unchanged.

## Remaining limitations

- This is a screenshot-ready local client demo, not production acceptance or a live Netlify fix. No site was deployed, DNS changed, paid service activated or production setting changed.
- The inspected local data is the supplied sample database. No authenticated live NewsAPI fetch or newly configured provider was performed; the existing backend integration remains available unchanged.
- API-only mode can naturally be sparse with the current ten records and backend's featured-first allocation. The opt-in preview exists specifically for that demonstration gap.
- Weather and translation are intentionally unavailable in demo mode. Preview artwork/content is illustrative, never reporting; standard search/navigation browse actual stored API content.
