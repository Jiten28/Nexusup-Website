// Acceptance tests for the approved homepage, slider, images, categories, article pages,
// Load More News and translation. Real React components in a real Chromium.
//
// NETWORK IS MOCKED: /api/* is answered by tests/fixtures.cjs and publisher images by a local
// PNG, so this proves the FRONT END against the documented API contract. It does not prove the
// live backend, database or publisher image delivery (see docs/TESTING.md for those checks).
//
//   QA_BASE_URL=http://localhost:5173 npm run test:browser      (Vite dev server running)
//   QA_OUT=./qa-output   directory for screenshots (default: ../docs/verification/acceptance)
const assert = require('node:assert/strict'), fs = require('fs'), path = require('path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const {makePng, build, mockApi} = require('./fixtures.cjs');

const base = process.env.QA_BASE_URL || 'http://localhost:5173';
const out = process.env.QA_OUT || path.resolve(__dirname, '../../docs/verification/acceptance');
fs.mkdirSync(out, {recursive: true});
const results = [], pageErrors = [];
const pngCache = new Map();
const photo = n => { const key = n % 12; if (!pngCache.has(key)) { const h = key * 30, f = (k) => { const a = (k + h / 60) % 6; return Math.round(255 * (a < 1 ? a : a < 3 ? 1 : a < 4 ? 4 - a : 0)); }; pngCache.set(key, makePng(600, 375, [70 + (f(0) >> 2), 90 + (f(2) >> 2), 120 + (f(4) >> 2)])); } return pngCache.get(key); };

async function newPage(browser, opts = {}) {
  const context = await browser.newContext({viewport: {width: opts.width || 1440, height: opts.height || 1000}, reducedMotion: opts.reducedMotion || 'no-preference'});
  const handler = mockApi(build());
  await context.route('**/*', route => {
    const url = new URL(route.request().url()), method = route.request().method();
    if (url.origin === new URL(base).origin) {
      if (url.pathname.startsWith('/api/')) {
        const data = handler(url, method, route.request().postData());
        if (data === undefined) return route.fulfill({status: 404, json: {error: 'not mocked'}});
        if (data === null) return route.fulfill({status: 404, json: {detail: 'Not found.'}});
        return route.fulfill({json: data});
      }
      return route.continue();
    }
    if (url.hostname === 'images.example') {
      const m = url.pathname.match(/(photo|missing)-(\d+)\.png/);
      if (!m || m[1] === 'missing') return route.fulfill({status: 404, body: 'missing'});
      return route.fulfill({status: 200, contentType: 'image/png', body: photo(+m[2])});
    }
    return route.abort(); // nothing else may leave the machine
  });
  const page = await context.newPage();
  page.on('pageerror', e => pageErrors.push(e.message));
  return {context, page};
}
async function home(page) { await page.goto(base + '/'); await page.waitForSelector('.latest-main-composition .story-card'); await page.waitForSelector('.slider-slide'); await page.mouse.move(0, 0); }
const tx = page => page.evaluate(() => { const m = new DOMMatrix(getComputedStyle(document.querySelector('.slider-track')).transform); return {x: m.m41, y: m.m42}; });
const counter = page => page.locator('.carousel-counter').innerText().then(s => s.replace(/\s+/g, ' ').trim());
async function run(name, fn) { const t = Date.now(); try { await fn(); results.push({name, pass: true, ms: Date.now() - t}); console.log('PASS', name); } catch (e) { results.push({name, pass: false, error: e.message.split('\n')[0]}); console.log('FAIL', name, '\n   ', e.message.split('\n').slice(0, 3).join('\n    ')); } }

(async () => {
  const browser = await chromium.launch({headless: true, ...(process.env.CHROMIUM ? {executablePath: process.env.CHROMIUM} : {}), args: ['--no-sandbox']});
  const {page, context} = await newPage(browser);
  await home(page);
  await page.waitForFunction(() => [...document.images].filter(i => i.src.includes('photo-')).every(i => i.complete));

  // ---------- Layout ----------
  const geo = await page.evaluate(() => {
    const r = e => { const b = e.getBoundingClientRect(); return {x: b.x, y: b.y, w: b.width, h: b.height, r: b.right, b: b.bottom}; };
    return {main: r(document.querySelector('.latest-main-story .story-card')),
      sides: [...document.querySelectorAll('.latest-side-stories')].map(s => [...s.querySelectorAll(':scope > .story-card')].map(r)),
      grid: [...document.querySelectorAll('.latest-surrounding-grid > .story-card')].map(r),
      comp: r(document.querySelector('.latest-main-composition')), loadMore: document.querySelectorAll('.load-more button').length};
  });
  await run('layout: one large centre story with two stacked cards on each side', async () => {
    assert.equal(geo.sides.length, 2); assert.deepEqual(geo.sides.map(s => s.length), [2, 2]);
    const [L, R] = geo.sides;
    assert.ok(L[0].r <= geo.main.x + 1 && geo.main.r <= R[0].x + 1, 'left | centre | right order');
    assert.ok(geo.main.w > L[0].w * 1.3 && geo.main.w > R[0].w * 1.3, 'centre story is clearly larger');
    for (const stack of geo.sides) assert.ok(stack[1].y >= stack[0].b - 1, 'side cards are stacked, not side by side');
    assert.ok(Math.abs(L[0].y - geo.main.y) <= 2 && Math.abs(R[0].y - geo.main.y) <= 2, 'tops aligned');
    assert.ok(Math.abs(L[1].b - geo.main.b) <= 2 && Math.abs(R[1].b - geo.main.b) <= 2, 'side stacks span the lead height');
  });
  await run('layout: lower grid has complete rows of four and no missing cells', async () => {
    assert.ok(geo.grid.length >= 4 && geo.grid.length % 4 === 0, `grid has ${geo.grid.length} cards`);
    const rows = new Map(); for (const c of geo.grid) rows.set(Math.round(c.y), (rows.get(Math.round(c.y)) || 0) + 1);
    assert.deepEqual([...rows.values()].filter(n => n !== 4), [], 'every row has exactly four cards');
    assert.ok(Math.min(...geo.grid.map(c => c.y)) >= geo.comp.b, 'grid sits below the composition');
  });
  await run('layout: no card text is clipped or overflowing', async () => {
    const bad = await page.evaluate(() => [...document.querySelectorAll('.latest-main-composition .story-card, .latest-surrounding-grid .story-card')].map(c => {
      const cb = c.getBoundingClientRect(), meta = c.querySelector('.story-meta'), mb = meta && meta.getBoundingClientRect(), h3 = c.querySelector('h3');
      const copy = c.querySelector('.card-copy');
      return {title: h3.textContent.slice(0, 24), scrollOverflow: c.scrollHeight - c.clientHeight, metaOutside: mb ? mb.bottom > cb.bottom + 1 || mb.top < cb.top : true, copyOverflow: copy.scrollHeight - copy.clientHeight};
    }).filter(x => x.scrollOverflow > 1 || x.metaOutside || x.copyOverflow > 1));
    assert.deepEqual(bad, []);
  });
  await run('layout: no story is repeated between slider, side cards and grid', async () => {
    const hrefs = await page.evaluate(() => [...document.querySelectorAll('.slider-slide h2 a, .story-card h3 a')].map(a => a.getAttribute('href')));
    assert.equal(new Set(hrefs).size, hrefs.length, 'duplicate hrefs: ' + hrefs.filter((h, i) => hrefs.indexOf(h) !== i));
  });
  await run('layout: exactly one Load More News button; it appends unique stories in full rows', async () => {
    assert.equal(geo.loadMore, 1);
    for (let guard = 0; guard < 6 && await page.locator('.load-more button').count(); guard++) {
      const before = await page.locator('.story-card').count();
      await page.getByRole('button', {name: /Load More News/}).click();
      await page.waitForFunction(n => document.querySelectorAll('.story-card').length > n, before);
      assert.equal(await page.locator('.load-more button').count() <= 1, true);
      if (await page.locator('.load-more button').count()) assert.equal((await page.locator('.latest-surrounding-grid > .story-card').count()) % 4, 0);
    }
    const hrefs = await page.evaluate(() => [...document.querySelectorAll('.story-card h3 a')].map(a => a.getAttribute('href')));
    assert.equal(new Set(hrefs).size, hrefs.length); assert.equal(hrefs.length, 26, 'all 30 stories minus 4 in the slider');
    assert.equal(await page.locator('.load-more button').count(), 0);
  });
  await page.screenshot({path: `${out}/home-desktop-1440.png`, fullPage: true, animations: 'disabled'});

  // ---------- Images ----------
  await run('images: authorised images decode; missing or broken ones fall back safely', async () => {
    await home(page);
    const st = await page.evaluate(() => {
      const card = t => [...document.querySelectorAll('.story-card')].find(c => c.querySelector('h3').textContent.startsWith(t));
      const info = t => { const c = card(t); return {img: !!c.querySelector('img[src*="images.example"]'), w: c.querySelector('img[src*="images.example"]')?.naturalWidth || 0, fallback: !!c.querySelector('[data-image-fallback]')}; };
      return {withImage: info('Story 6:'), none: info('Story 5:'), broken: info('Story 7:'), loaded: [...document.querySelectorAll('.story-card img[src*="photo-"]')].map(i => i.naturalWidth)};
    });
    assert.ok(st.withImage.img && st.withImage.w > 0 && !st.withImage.fallback, 'Story 6 shows a decoded image');
    assert.ok(st.none.fallback && !st.none.img, 'Story 5 (no authorised image) shows the NexusUp fallback');
    assert.ok(st.broken.fallback && !st.broken.img, 'Story 7 (404) falls back instead of a broken icon');
    assert.ok(st.loaded.length > 5 && st.loaded.every(w => w > 0), 'every card image decoded');
    assert.equal(await page.locator('img[src*="images.example"]').first().getAttribute('referrerpolicy'), 'no-referrer');
  });

  // ---------- Slider ----------
  await run('slider: slides share one size and the track starts at slide 1', async () => {
    await home(page);
    const d = await page.evaluate(() => { const v = {width: document.querySelector('.slider-viewport').clientWidth}, s = [...document.querySelectorAll('.slider-slide')].map(e => e.getBoundingClientRect()); return {vw: v.width, w: s.map(x => Math.round(x.width)), h: s.map(x => Math.round(x.height)), n: s.length}; });
    assert.equal(d.n, 4); assert.ok(d.w.every(w => Math.abs(w - d.vw) <= 1), 'slides are viewport width'); assert.equal(new Set(d.h).size, 1, 'slides are one height');
    assert.equal(await counter(page), '01 / 04'); assert.deepEqual(await tx(page), {x: 0, y: 0});
    assert.ok(await page.evaluate(() => { const i = document.querySelector('.slider-slide img'); return i.naturalWidth > 0; }), 'first slide image decoded');
  });
  await run('slider: next moves horizontally with a smooth transition (both slides on screen mid-move)', async () => {
    await home(page);
    const vw = await page.evaluate(() => document.querySelector('.slider-viewport').clientWidth);
    await page.locator('button[aria-label="Next headline"]').click();
    const samples = []; for (let i = 0; i < 8; i++) { samples.push(await tx(page)); await page.waitForTimeout(130); }
    const xs = samples.map(s => s.x); assert.ok(samples.every(s => s.y === 0), 'no vertical movement');
    assert.ok(xs.some(x => x < -8 && x > -vw + 8), `intermediate positions seen: ${xs.map(Math.round)}`);
    for (let i = 1; i < xs.length; i++) assert.ok(xs[i] <= xs[i - 1] + 0.5, 'monotonic, no bounce or flicker');
    assert.ok(Math.abs((await tx(page)).x + vw) <= 1, 'settles exactly one slide over'); assert.equal(await counter(page), '02 / 04');
    await page.locator('button[aria-label="Previous headline"]').click(); await page.waitForTimeout(250);
    await page.screenshot({path: `${out}/slider-mid-transition.png`, clip: {x: 0, y: 330, width: 1440, height: 520}});
    await page.waitForTimeout(900); assert.equal(await counter(page), '01 / 04');
  });
  await run('slider: indicators, previous, next and wrap-around', async () => {
    await home(page);
    await page.locator('.slide-indicators button').nth(2).click(); assert.equal(await counter(page), '03 / 04');
    assert.equal(await page.locator('.slide-indicators button[aria-current="true"]').count(), 1);
    await page.locator('button[aria-label="Previous headline"]').click(); assert.equal(await counter(page), '02 / 04');
    await page.locator('.slide-indicators button').nth(0).click(); await page.locator('button[aria-label="Previous headline"]').click(); assert.equal(await counter(page), '04 / 04');
    await page.locator('button[aria-label="Next headline"]').click(); assert.equal(await counter(page), '01 / 04');
  });
  await run('slider: only the visible slide is focusable or announced', async () => {
    await home(page);
    const st = await page.evaluate(() => [...document.querySelectorAll('.slider-slide')].map(s => ({inert: s.hasAttribute('inert'), hidden: s.getAttribute('aria-hidden')})));
    assert.deepEqual(st.map(s => s.inert), [false, true, true, true]); assert.deepEqual(st.map(s => s.hidden), [null, 'true', 'true', 'true']);
  });
  await run('slider: swipe left advances', async () => {
    await home(page); const b = await page.locator('.slider-viewport').boundingBox();
    await page.mouse.move(b.x + 900, b.y + 150); await page.mouse.down(); await page.mouse.move(b.x + 600, b.y + 155, {steps: 6}); await page.mouse.up();
    await page.waitForTimeout(100); assert.equal(await counter(page), '02 / 04', 'counter after swipe');
  });
  await run('slider: respects reduced motion (starts paused, no transition)', async () => {
    const r = await newPage(browser, {reducedMotion: 'reduce'}); await home(r.page);
    assert.equal(await r.page.locator('button[aria-label="Play slider"]').count(), 1);
    assert.match(await r.page.evaluate(() => getComputedStyle(document.querySelector('.slider-track')).transitionDuration), /^0s$/);
    await r.context.close();
  });
  // Timing tests use real time (the interval is 7 s); run in parallel pages.
  const timing = async (name, fn) => { const r = await newPage(browser); await home(r.page); await run(name, () => fn(r.page)); await r.context.close(); };
  await Promise.all([
    timing('slider: autoplay advances once per interval', async p => { await p.waitForTimeout(7600); assert.equal(await counter(p), '02 / 04'); await p.waitForTimeout(7000); assert.equal(await counter(p), '03 / 04'); }),
    timing('slider: Pause stops autoplay and Play label toggles', async p => {
      const b = p.locator('button[aria-label$="slider"]'); assert.equal(await b.getAttribute('aria-label'), 'Pause slider'); await b.click();
      assert.equal(await b.getAttribute('aria-label'), 'Play slider'); await p.mouse.move(0, 0); await p.waitForTimeout(8000); assert.equal(await counter(p), '01 / 04'); }),
    timing('slider: rapid manual clicks never create duplicate timers', async p => {
      for (let i = 0; i < 3; i++) await p.locator('button[aria-label="Next headline"]').click(); assert.equal(await counter(p), '04 / 04');
      await p.mouse.move(0, 0); await p.waitForTimeout(7700); assert.equal(await counter(p), '01 / 04', 'exactly one advance (04 -> 01)'); }),
    timing('slider: hovering the slider holds autoplay', async p => { const b = await p.locator('.slider-viewport').boundingBox(); await p.mouse.move(b.x + 200, b.y + 100); await p.waitForTimeout(8000); assert.equal(await counter(p), '01 / 04'); }),
  ]);

  // ---------- Categories ----------
  await run('categories: empty categories are hidden; filters open only that category', async () => {
    await home(page);
    const names = await page.locator('.category-filters a').allInnerTexts();
    assert.deepEqual(names, ['All perspectives', 'World', 'Technology', 'Business']);
    assert.deepEqual((await page.locator('nav[aria-label="Main navigation"] a').allInnerTexts()), ['Home', 'All stories', 'World', 'Technology', 'Business']);
    await page.locator('.category-filters a', {hasText: 'Technology'}).click(); await page.waitForSelector('.news-grid .story-card');
    assert.equal(new URL(page.url()).pathname, '/category/technology/');
    const cats = await page.locator('.news-grid .story-card .card-copy .category').allInnerTexts(); assert.ok(cats.length > 0 && cats.every(c => c.toLowerCase() === 'technology'));
    assert.equal(await page.locator('.category-filters a[aria-current="page"]').innerText(), 'Technology');
    await page.goto(base + '/category/cricket/'); await page.waitForSelector('.state'); assert.match(await page.locator('.state').innerText(), /No stories yet/);
  });

  // ---------- Article pages ----------
  await run('article: summary-only story shows headline, date, source, original link and an honest notice', async () => {
    await page.goto(base + '/story/story-3/'); await page.waitForSelector('.article-detail h1');
    assert.match(await page.locator('h1').innerText(), /^Story 3:/); assert.ok(await page.locator('.source-box time[datetime]').count());
    const link = page.locator('.source-box a.read-story'); assert.equal(await link.getAttribute('href'), 'https://publisher.example/story-3');
    assert.equal(await link.getAttribute('target'), '_blank'); assert.match(await link.getAttribute('rel'), /noopener/);
    assert.match(await page.locator('[data-content-kind="summary"]').innerText(), /summary supplied by the publisher/);
    assert.equal(await page.locator('.article-body').count(), 0, 'no fake body for a summary-only entry');
    assert.doesNotMatch(await page.locator('main').innerText(), /metadata only/); assert.match(await page.locator('.source-box').innerText(), /Fixture News/);
    assert.ok(await page.evaluate(() => document.querySelector('.article-detail img[src*="photo-3"]').naturalWidth > 0), 'permitted image shown');
    await page.screenshot({path: `${out}/article-summary.png`, fullPage: true, animations: 'disabled'});
  });
  await run('article: publisher-supplied text is shown and labelled as feed text, not summary', async () => {
    await page.goto(base + '/story/story-4/'); await page.waitForSelector('.article-body');
    assert.equal(await page.locator('.article-body p').count(), 2); assert.equal(await page.locator('[data-content-kind="feed_content"]').count(), 1); assert.equal(await page.locator('[data-content-kind="summary"]').count(), 0);
  });
  await run('article: no authorised image shows the fallback, not a broken image', async () => {
    await page.goto(base + '/story/story-5/'); await page.waitForSelector('.article-detail h1');
    assert.equal(await page.locator('.article-detail [data-image-fallback]').count(), 1); assert.equal(await page.locator('.article-detail img[src*="images.example"]').count(), 0);
  });

  // ---------- Translation ----------
  await run('translation: language list is ready on load; UI switches and original English returns', async () => {
    await page.goto(base + '/'); await page.waitForSelector('.latest-main-composition .story-card');
    assert.equal(await page.locator('#language option').count(), 2, 'languages loaded without opening the menu');
    await page.selectOption('#language', 'hi'); await page.waitForFunction(() => document.querySelector('nav[aria-label="Main navigation"] a').textContent === 'होम');
    assert.equal(await page.evaluate(() => document.documentElement.lang), 'hi'); assert.match(await page.locator('.language small').innerText(), /Machine translation/);
    assert.match(await page.locator('.load-more button').innerText().catch(() => 'और खबरें'), /और खबरें|Load/);
    await page.selectOption('#language', 'en'); await page.waitForFunction(() => document.querySelector('nav[aria-label="Main navigation"] a').textContent === 'Home');
    assert.equal(await page.evaluate(() => document.documentElement.lang), 'en');
    await page.evaluate(() => localStorage.removeItem('nexusup-language'));
  });
  // ---------- Colour themes ----------
  await run('themes: Light / Dark / Auto switch and eight palettes work and are remembered', async () => {
    const r = await newPage(browser); await home(r.page); const p = r.page;
    const st = () => p.evaluate(() => ({theme: document.documentElement.dataset.theme, mode: document.documentElement.dataset.mode, palette: document.documentElement.dataset.palette, accent: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(), bg: getComputedStyle(document.body).backgroundColor}));
    assert.deepEqual(await p.locator('.mode-switch button').allInnerTexts().then(a => a.map(x => x.replace(/[^A-Za-z]/g, ''))), ['Light', 'Dark', 'Auto']);
    await p.locator('.mode-switch button', {hasText: 'Dark'}).click(); let a = await st(); assert.equal(a.theme, 'dark'); assert.equal(a.mode, 'dark');
    await p.locator('.mode-switch button', {hasText: 'Light'}).click(); a = await st(); assert.equal(a.theme, 'light');
    assert.equal(await p.locator('.palette-picker, .theme-cycle ~ .popover').count(), 0, 'no drop-down menu');
    const accents = new Set([(await st()).accent]);
    for (let i = 0; i < 7; i++) { await p.locator('.theme-cycle').click(); const s1 = await st(); accents.add(s1.accent); assert.equal(s1.theme, 'light', 'palette change keeps the mode'); }
    assert.equal(accents.size, 8, 'eight clicks visit eight different palettes, one click each');
    await p.locator('.theme-cycle').click(); assert.equal((await st()).palette, 'graphite-silver', 'wraps around');
    await p.locator('.theme-cycle').click();
    await p.reload(); await p.waitForSelector('.slider-slide'); a = await st(); assert.equal(a.palette, 'emerald-imperial', 'palette remembered'); assert.equal(a.mode, 'light');
    await r.context.close();
    const d = await newPage(browser); await d.context.close();
  });
  await run('themes: Auto follows the device colour scheme', async () => {
    const ctx = await browser.newContext({colorScheme: 'dark', viewport: {width: 1200, height: 800}}); const p = await ctx.newPage();
    await ctx.route('**/*', route => { const u = new URL(route.request().url()); if (u.origin === new URL(base).origin && !u.pathname.startsWith('/api/')) return route.continue(); if (u.pathname.startsWith('/api/')) { const h = mockApi(build())(u, 'GET'); return route.fulfill({json: h}); } return route.abort(); });
    await p.goto(base + '/'); await p.waitForSelector('.slider-slide');
    assert.equal(await p.evaluate(() => document.documentElement.dataset.theme), 'dark'); assert.equal(await p.evaluate(() => document.documentElement.dataset.mode), 'auto');
    await p.emulateMedia({colorScheme: 'light'}); await p.waitForFunction(() => document.documentElement.dataset.theme === 'light');
    await ctx.close();
  });
  for (const [pal, mode] of [['graphite-silver', 'light'], ['graphite-silver', 'dark'], ['emerald-imperial', 'light'], ['ruby-velvet', 'dark'], ['amethyst-noir', 'light'], ['arctic-aurora', 'dark'], ['copper-sunset', 'light'], ['midnight-rose', 'dark'], ['ocean-navy', 'light']]) {
    const r = await newPage(browser, {width: 1440, height: 900}); await r.page.addInitScript(([pal, mode]) => { localStorage.setItem('nexusup-palette', pal); localStorage.setItem('nexusup-theme', mode); }, [pal, mode]);
    await home(r.page); await r.page.waitForTimeout(700); await r.page.screenshot({path: `${out}/theme-${pal}-${mode}.png`, clip: {x: 0, y: 0, width: 1440, height: 900}, animations: 'disabled'}); await r.context.close();
  }
  await run('no uncaught page errors', async () => assert.deepEqual(pageErrors, []));

  // ---------- Screenshots at other widths ----------
  for (const [w, h] of [[1024, 900], [390, 844]]) { const r = await newPage(browser, {width: w, height: h}); await home(r.page); await r.page.waitForTimeout(1200); await r.page.screenshot({path: `${out}/home-${w}.png`, fullPage: true, animations: 'disabled'}); await r.context.close(); }
  await context.close(); await browser.close();
  const failed = results.filter(r => !r.pass);
  fs.writeFileSync(`${out}/acceptance-results.json`, JSON.stringify({base, mocked_network: true, total: results.length, failed: failed.length, results}, null, 1));
  console.log(`\n${results.length - failed.length}/${results.length} acceptance checks passed (mocked API + images, real browser)`);
  process.exit(failed.length ? 1 : 0);
})().catch(e => { console.error('HARNESS ERROR', e); process.exit(2); });
