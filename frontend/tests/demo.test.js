import test from 'node:test';
import assert from 'node:assert/strict';
import {themes,advanceTheme,resolveTheme} from '../src/services/themes.js';
import {previewArticles,needsPreview,sanitizeHome} from '../src/preview/data.js';
const luminance=hex=>{const x=hex.slice(1).match(/../g).map(x=>parseInt(x,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return x[0]*.2126+x[1]*.7152+x[2]*.0722};
const contrast=(a,b)=>{const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
test('six themes, migration aliases, light/dark tokens and AA text contrast',()=>{
 assert.equal(themes.length,6);assert.equal(resolveTheme('ocean').id,'ocean-editorial');assert.equal(resolveTheme('unknown').id,'midnight-coral');
 for(const t of themes)for(const mode of ['light','dark']){const p=t[mode];for(const bg of ['--bg','--surface','--accent-soft'])for(const fg of ['--text','--muted','--accent'])assert.ok(contrast(p[fg],p[bg])>=4.5,`${t.id}/${mode}: ${fg}/${bg} ${contrast(p[fg],p[bg])}`);assert.ok(contrast(p['--accent'],p['--on-accent'])>=4.5)}
});
test('100 shuffled cycles have no replacement or boundary repeat',()=>{
 let current=themes[0].id,remaining=[],previous=current;
 for(let n=0;n<100;n++){const cycle=[];for(let i=0;i<6;i++){const next=advanceTheme(current,remaining);current=next.id;remaining=next.remaining;assert.notEqual(current,previous);previous=current;cycle.push(current)}assert.equal(new Set(cycle).size,6);assert.equal(remaining.length,0)}
});
test('corrupt theme-cycle data is recovered safely',()=>{for(const remaining of [['fake'],['midnight-coral','midnight-coral']]){const next=advanceTheme('midnight-coral',remaining);assert.ok(themes.some(t=>t.id===next.id));assert.notEqual(next.id,'midnight-coral')}});
test('0/1 headlines use preview eligibility; 3/5 image-led headlines do not',()=>{for(const n of [0,1,3,5])assert.equal(needsPreview({carousel:previewArticles.slice(0,n)}),n<3);assert.equal(needsPreview({carousel:previewArticles.slice(0,5).map(a=>({...a,image:''}))}),true)});
test('preview stories, sections and links have unique IDs and transparent provenance',()=>{assert.equal(previewArticles.length,18);assert.equal(new Set(previewArticles.map(a=>a.slug)).size,18);for(const a of previewArticles){assert.ok(a.is_preview);assert.equal(a.date,null);assert.match(a.slug,/^local-preview-/);assert.match(a.body,/not a verified news report/);assert.ok(a.image.startsWith('/preview/'))}});
test('API selection removes duplicates and keeps exclusions to rendered stories only',()=>{const d=sanitizeHome({carousel:[...previewArticles.slice(0,3),previewArticles[0]],featured:[...previewArticles.slice(2,8)],excluded:['old']});assert.equal(d.carousel.length,3);assert.equal(d.featured.length,5);assert.equal(new Set([...d.carousel,...d.featured].map(a=>a.id)).size,8);assert.equal(d.excluded.length,8);assert.equal(needsPreview(null),true)});
