import test from 'node:test';
import assert from 'node:assert/strict';
import {themes,MODES,advanceTheme,cycleTheme,resolveTheme,resolveMode} from '../src/services/themes.js';
const luminance=hex=>{const x=hex.slice(1).match(/../g).map(x=>parseInt(x,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return x[0]*.2126+x[1]*.7152+x[2]*.0722};
const contrast=(a,b)=>{const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
test('eight palettes, each with light and dark tokens that pass AA text contrast',()=>{
 assert.equal(themes.length,8);assert.equal(new Set(themes.map(t=>t.id)).size,8);
 for(const t of themes)for(const mode of ['light','dark']){const p=t[mode];
  for(const bg of ['--bg','--surface','--accent-soft'])for(const fg of ['--text','--muted','--accent'])assert.ok(contrast(p[fg],p[bg])>=4.5,`${t.id}/${mode}: ${fg} on ${bg}`);
  assert.ok(contrast(p['--accent'],p['--on-accent'])>=4.5,`${t.id}/${mode}: button text`);assert.match(p['--accent-2'],/^#[0-9a-f]{6}$/i)}
});
test('three colour modes; auto follows the device',()=>{
 assert.deepEqual(MODES,['light','dark','auto']);
 assert.equal(resolveMode('light',true),'light');assert.equal(resolveMode('dark',false),'dark');
 assert.equal(resolveMode('auto',true),'dark');assert.equal(resolveMode('auto',false),'light');
});
test('old palette ids still resolve; unknown ids fall back to the first palette',()=>{
 assert.equal(resolveTheme('midnight-coral').id,'ruby-velvet');assert.equal(resolveTheme('rose-magenta').id,'midnight-rose');assert.equal(resolveTheme('sapphire-gold').id,'graphite-silver');assert.equal(resolveTheme('nope').id,themes[0].id);
});
test('shuffled cycles visit every palette once with no immediate repeat',()=>{
 let current=themes[0].id,remaining=[],previous=current;
 for(let n=0;n<50;n++){const seen=[];for(let i=0;i<8;i++){const next=advanceTheme(current,remaining);current=next.id;remaining=next.remaining;assert.notEqual(current,previous);previous=current;seen.push(current)}assert.equal(new Set(seen).size,8)}
});
test('one click moves to the next palette and wraps',()=>{let id=themes[0].id;const seen=[id];for(let i=0;i<8;i++){id=cycleTheme(id);seen.push(id)}assert.equal(new Set(seen.slice(0,8)).size,8);assert.equal(seen[8],themes[0].id)});
