import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const py = fs.readFileSync(path.join(root, 'backend/apps/news/ui_strings.py'), 'utf8');
const known = new Set([...py.matchAll(/['"](ui:[a-z_]+)['"]\s*:/g)].map(m => m[1]));
function walk(d) { return fs.readdirSync(d, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(d, e.name)) : /\.jsx?$/.test(e.name) ? [path.join(d, e.name)] : []); }

test('every translatable ui: key used by React exists in the server translation corpus', () => {
  const used = new Set();
  for (const f of walk(path.join(root, 'frontend/src'))) for (const m of fs.readFileSync(f, 'utf8').matchAll(/['"`](ui:[a-z_]+)['"`]/g)) used.add(m[1]);
  assert.ok(used.size > 20, 'found keys');
  assert.deepEqual([...used].filter(k => !known.has(k)), []);
});
