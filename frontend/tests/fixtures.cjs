// Deterministic fixtures and a mock of the NexusUp REST API (MOCKED NETWORK, not the real backend).
// It mirrors the real contract: /api/home/, /api/articles/ (page, page_size, exclude, category, q),
// detail, related, categories with article_count, languages and translate.
const zlib = require('zlib');

// A valid 120x75 PNG so <img> elements really decode (naturalWidth > 0).
function makePng(w = 120, h = 75, rgb = [40, 90, 160]) {
  const crcTable = Array.from({length: 256}, (_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
  const crc = buf => { let c = 0xffffffff; for (const b of buf) c = crcTable[(c ^ b) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
  const chunk = (type, data) => { const len = Buffer.alloc(4); len.writeUInt32BE(data.length); const td = Buffer.concat([Buffer.from(type), data]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([len, td, c]); };
  const row = Buffer.concat([Buffer.from([0]), Buffer.from(Array.from({length: w}, () => rgb).flat())]);
  const raw = Buffer.concat(Array.from({length: h}, () => row));
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

const CATEGORIES = [
  {id: 1, name: 'World', slug: 'world'}, {id: 2, name: 'Technology', slug: 'technology'},
  {id: 3, name: 'Business', slug: 'business'}, {id: 4, name: 'Cricket', slug: 'cricket'},
];
const SUMMARY_NOTICE_SLUG = 'story-3';

function build(total = 30) {
  const base = Date.parse('2026-10-24T06:00:00Z');
  const articles = Array.from({length: total}, (_, i) => {
    const n = i + 1, cat = CATEGORIES[i % 3]; // cricket deliberately has no stories
    // Every 5th story has NO authorised image; every 7th points at an image that 404s.
    const image = n % 5 === 0 ? '' : n % 7 === 0 ? `https://images.example/missing-${n}.png` : `https://images.example/photo-${n}.png`;
    return {
      id: n, slug: `story-${n}`, title: `Story ${n}: a reasonably long headline about ${cat.name.toLowerCase()} developments`,
      excerpt: `Publisher summary for story ${n}.`, category: cat, tags: [], image, image_alt: image ? `Photo ${n}` : '',
      image_credit: image ? 'Fixture publisher' : '', source_name: 'Fixture News', canonical_source_url: `https://publisher.example/story-${n}`,
      date: new Date(base - i * 3600e3).toISOString(), featured: false, is_sample: false, reading_minutes: 1,
      content_kind: n === 4 ? 'feed_content' : 'feed_summary',
      body: n === 4 ? 'First paragraph of publisher-supplied text.\n\nSecond paragraph of publisher-supplied text.' : 'Read the original publisher for the complete report. This entry contains feed metadata only.',
      comments: [],
    };
  });
  return articles;
}

function mockApi(articles = build()) {
  const counts = () => { const c = {}; for (const a of articles) c[a.category.id] = (c[a.category.id] || 0) + 1; return c; };
  const page = (items, url) => {
    const size = Math.min(parseInt(url.searchParams.get('page_size') || '12', 10), 24), p = parseInt(url.searchParams.get('page') || '1', 10);
    const slice = items.slice((p - 1) * size, p * size);
    return {count: items.length, next: p * size < items.length ? `?page=${p + 1}` : null, previous: p > 1 ? `?page=${p - 1}` : null, results: slice};
  };
  const strip = ({body, comments, ...a}) => a;
  return function handle(url, method, bodyText) {
    const path = url.pathname;
    if (path === '/api/categories/') { const c = counts(); return CATEGORIES.map(x => ({...x, article_count: c[x.id] || 0})); }
    if (path === '/api/csrf/') return {csrfToken: 'fixture-token'};
    if (path === '/api/home/') { const car = articles.filter(a => a.image).slice(0, 4).map(strip); return {carousel: car, featured: [], excluded: car.map(a => a.id)}; }
    if (path === '/api/articles/') {
      const ex = (url.searchParams.get('exclude') || '').split(',').filter(Boolean).map(Number), cat = url.searchParams.get('category');
      let items = articles.filter(a => !ex.includes(a.id) && (!cat || a.category.slug === cat));
      return page(items.map(strip), url);
    }
    let m = path.match(/^\/api\/articles\/([^/]+)\/related\/$/);
    if (m) return {results: articles.filter(a => a.slug !== m[1]).slice(0, 2).map(strip)};
    m = path.match(/^\/api\/articles\/([^/]+)\/$/);
    if (m) return articles.find(a => a.slug === m[1]) || null;
    if (path === '/api/languages/') return {languages: [{code: 'en', name: 'English'}, {code: 'hi', name: 'Hindi'}], provider: 'fixture'};
    if (path === '/api/translate/' && method === 'POST') {
      const lang = JSON.parse(bodyText || '{}').language;
      return {source: 'en', language: lang, notice: 'Machine translation. Original English remains available.', texts: {'ui:home': 'होम', 'ui:blogs': 'सभी कहानियाँ', 'ui:latest': 'ताज़ा खबरें', 'ui:load_more': 'और खबरें ↓', 'article:1:title': 'कहानी 1: अनुवादित शीर्षक'}};
    }
    return undefined;
  };
}

module.exports = {makePng, build, mockApi, CATEGORIES, SUMMARY_NOTICE_SLUG};
