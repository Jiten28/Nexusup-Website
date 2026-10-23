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
  assert.match(pages, /latest-main-composition/);
  assert.match(pages, /latest-side-stories/);
  assert.match(pages, /latest-main-story/);
  assert.match(pages, /latest-surrounding-grid/);
  assert.match(css, /\.latest-main-composition\s*\{[^}]*grid-template-columns:\s*minmax\(0,1fr\)\s+minmax\(0,1\.55fr\)\s+minmax\(0,1fr\)/s);
  assert.match(css, /\.latest-surrounding-grid\s*\{[^}]*grid-template-columns:\s*repeat\(4,minmax\(0,1fr\)\)/s);
});

test('headline slider keeps automatic advance and manual play/pause controls', () => {
  assert.match(carousel, /setInterval\(\(\)=>setIndex/);
  assert.match(carousel, /Pause/);
  assert.match(carousel, /Previous headline/);
  assert.match(carousel, /Next headline/);
});

test('home uses one centered composition and a single Load More News control, not a duplicate latest section', () => {
  assert.match(pages, /Load More News/);
  assert.doesNotMatch(pages, /heading="More latest news"/);
  assert.match(pages, /const main=stories\[0\],left=stories\.slice\(1,3\),right=stories\.slice\(3,5\),grid=stories\.slice\(5\)/);
  assert.match(pages, /setHasMore\(Boolean\(d\.next\)\)/);
});

test('headline slider has a gentler 7.5-second interval and respects reduced motion', () => {
  assert.match(carousel, /7500/);
  assert.match(carousel, /prefers-reduced-motion: reduce/);
});

test('navigation does not silently hide categories after the first five', () => {
  const app = fs.readFileSync(path.join(root, 'src/App.jsx'), 'utf8');
  assert.match(app, /categories\.map\(c=>/);
  assert.doesNotMatch(app, /categories\.slice\(0,5\)/);
});
