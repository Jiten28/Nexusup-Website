import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
test('frontend entrypoints contain no privileged Vite environment variables',()=>{
 for(const file of ['src/App.jsx','src/services/api.js']){assert.doesNotMatch(fs.readFileSync(file,'utf8'),/VITE_(SECRET|DB_PASSWORD|NEWS_API_KEY)/)}
});
