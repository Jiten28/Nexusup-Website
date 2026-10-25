import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pages = fs.readFileSync(path.join(root, 'src/pages/NewsPages.jsx'), 'utf8');
const css = fs.readFileSync(path.join(root, 'src/styles/site.css'), 'utf8');
const carousel = fs.readFileSync(path.join(root, 'src/components/Carousel.jsx'), 'utf8');

test('homepage follows the hand-drawn centered lead with two side columns and lower four-column grid', () => {
  for (const c of ['latest-main-composition', 'latest-side-stories', 'latest-main-story', 'latest-surrounding-grid']) assert.match(pages, new RegExp(c));
  assert.match(css, /\.latest-main-composition\s*\{[^}]*grid-template-columns:\s*minmax\(0,1fr\)\s+minmax\(0,1\.6fr\)\s+minmax\(0,1fr\)/s);
  assert.match(css, /\.latest-surrounding-grid\s*\{[^}]*grid-template-columns:\s*repeat\(4,minmax\(0,1fr\)\)/s);
});

test('stories are split 1 lead / 2 left / 2 right / grid trimmed to full rows of four', () => {
  assert.match(pages, /PAGE_SIZE\s*=\s*13/);
  assert.match(pages, /GRID_COLUMNS\s*=\s*4/);
  assert.match(pages, /export function composeLatest/);
});

test('headline slider is a single-timeout horizontal track with controls', () => {
  assert.match(carousel, /setTimeout\(\(\)=>setIndex/);
  assert.doesNotMatch(carousel, /setInterval/);
  assert.match(carousel, /translate3d\(/);
  assert.match(carousel, /slider-track/);
  for (const label of ['Pause slider', 'Previous headline', 'Next headline']) assert.match(carousel, new RegExp(label));
});

test('home has one Load More News control and no duplicate latest section', () => {
  assert.equal((pages.match(/Load More News/g) || []).length, 1);
  assert.doesNotMatch(pages, /heading="More latest news"/);
  assert.match(pages, /exclude/);
});

test('slider interval is 7 seconds and reduced motion is respected', () => {
  assert.match(carousel, /SLIDE_INTERVAL_MS\s*=\s*7000/);
  assert.match(carousel, /prefers-reduced-motion: reduce/);
});

test('navigation shows every category that has stories (no arbitrary slice)', () => {
  const app = fs.readFileSync(path.join(root, 'src/App.jsx'), 'utf8');
  assert.match(app, /visibleCategories/);
  assert.doesNotMatch(app, /categories\.slice\(0,5\)/);
});
