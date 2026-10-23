import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveImageURL} from '../src/services/image-url.js';
test('relative images use the configured backend origin, not the SPA route',()=>{
 assert.equal(resolveImageURL('/media/a.jpg','http://127.0.0.1:8000','http://localhost:5173'),'http://127.0.0.1:8000/media/a.jpg');
 assert.equal(resolveImageURL('media/a.jpg','','http://localhost:5173'),'http://localhost:5173/media/a.jpg');
});
test('HTTPS publisher images are preserved without invented replacements',()=>{
 assert.equal(resolveImageURL('https://publisher.example/a.jpg','','https://site.example'),'https://publisher.example/a.jpg');
 assert.equal(resolveImageURL('//publisher.example/a.jpg','','https://site.example'),'https://publisher.example/a.jpg');
});
test('missing unsafe and mixed-content URLs use the existing fallback',()=>{
 for(const v of ['',null,undefined,'javascript:alert(1)','data:image/png;base64,abc','https://user:password@publisher.example/a.jpg','http://publisher.example/a.jpg'])assert.equal(resolveImageURL(v,'','https://site.example'),'');
});
