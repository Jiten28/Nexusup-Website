import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
test('Netlify fallback covers frontend routes, not reserved backend paths',()=>{
 const rules=fs.readFileSync('public/_redirects','utf8');
 assert.match(rules,/\/story\/\*/);assert.match(rules,/\/category\/\*/);
 assert.doesNotMatch(rules,/^\/\*\s/m);assert.doesNotMatch(rules,/^\/(api|admin|media|static|feed)\//m);
});
test('frontend entrypoints contain no privileged Vite environment variables',()=>{
 const files=['src/App.jsx','src/services/api.js'];
 for(const file of files){const content=fs.readFileSync(file,'utf8');assert.doesNotMatch(content,/VITE_(SECRET|DB_PASSWORD|NEWS_API_KEY)/);}
});
