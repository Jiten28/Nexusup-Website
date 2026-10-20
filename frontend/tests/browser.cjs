// Run from /data to use installed Playwright: node /data/NexusUp/frontend/tests/browser.cjs
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs');
const assert=require('node:assert/strict');
const path=require('path'),os=require('os');
const base=process.env.QA_BASE_URL||'http://127.0.0.1:5173',backend=process.env.QA_BACKEND_URL||'http://127.0.0.1:8000';
const out=process.env.QA_OUT||path.join(os.tmpdir(),'nexusup-react-qa');fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({...(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{}),headless:true,args:['--no-sandbox']});const context=await browser.newContext();const page=await context.newPage();let results=[];const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 for(const width of [360,390,768,1024,1440]){
  await page.setViewportSize({width,height:1000});await page.goto(base+'/');await page.waitForSelector('.latest .story-card');
  assert.equal(await page.locator('.carousel').count(),1);assert.ok((await page.locator('.carousel-track article').count())<=4);
  const size=await page.evaluate(()=>({doc:document.documentElement.scrollWidth,viewport:innerWidth}));assert.ok(size.doc<=width,JSON.stringify(size));
  const urls=await page.locator('main .story-card h3 a, .carousel-copy h3').allTextContents();assert.equal(urls.length,new Set(urls).size);
  const cols=await page.locator('.news-grid').evaluate(e=>getComputedStyle(e).gridTemplateColumns.split(' ').length);assert.equal(cols,width<560?1:width<=800?2:width<=1100?3:4);
  await page.screenshot({path:`${out}/react-${width}.png`,fullPage:true});results.push({test:'responsive-home',width,overflow:false,gridColumns:cols});
 }
 await page.setViewportSize({width:1440,height:1000});
 for(const mode of ['light','dark']){for(const palette of ['ocean','violet','emerald','sunset']){
  await page.evaluate(mode=>{document.documentElement.dataset.theme=mode;localStorage.setItem('nexusup-theme',mode)},mode);await page.reload();await page.waitForSelector('.latest .story-card');
  await page.selectOption('#palette',palette);assert.equal(await page.locator('html').getAttribute('data-theme'),mode);await page.screenshot({path:`${out}/react-${mode}-${palette}.png`,fullPage:true});results.push({test:'theme-palette',mode,palette});
 }}
 // Calculator and all retained widgets open. Offline providers must fail honestly.
 for(const [key,title] of [['calculator','Calculator'],['currency','Currency converter'],['weather','Local weather'],['clock','World clock'],['calendar','Calendar'],['units','Unit converter']]){
  await page.locator('.header-popover summary').click();await page.locator(`[data-widget="${key}"]`).click();await page.waitForSelector('dialog[open]');assert.equal(await page.locator('#utility-title').innerText(),title);
  if(key==='calculator'){await page.fill('#calc-input','(24 + 6) / 3');await page.locator('#calc-form button').click();assert.equal(await page.locator('.utility-result').innerText(),'10')}
  if(key==='currency'){await page.locator('#utility-content form button').click();await page.waitForFunction(()=>document.querySelector('.utility-result').textContent==='Rate unavailable')}
  if(key==='units'){await page.locator('#utility-content form button').click();assert.equal(await page.locator('.utility-result').innerText(),'0.001 km')}
  await page.screenshot({path:`${out}/react-widget-${key}.png`});await page.locator('#close-utility').click();results.push({test:'widget',key});
 }
 await page.locator('#language').focus();await page.waitForFunction(()=>document.querySelector('.language small').textContent.includes('not configured'));results.push({test:'translation-disabled',pass:true});
 await page.locator('.carousel [aria-label="Play carousel"]').click();assert.equal(await page.locator('.carousel [aria-label="Pause carousel"]').count(),1);
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>document.querySelector('.carousel .controls button[disabled]'));assert.equal(await page.locator('.carousel .controls button').nth(1).isDisabled(),true);results.push({test:'carousel-reduced-motion',pass:true});
 const article=await page.locator('.central h3 a').getAttribute('href');await page.goto(base+article);await page.waitForSelector('.article-body');await page.screenshot({path:out+'/react-article.png',fullPage:true});await page.getByRole('button',{name:'Save story',exact:true}).click();await page.reload();await page.getByRole('button',{name:'Saved ✓',exact:true}).waitFor();assert.equal(await page.getByRole('button',{name:'Saved ✓',exact:true}).count(),1);results.push({test:'article-direct-refresh-save',pass:true});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:out+'/react-article-mobile.png',fullPage:true});
 for(const path of ['about','privacy','terms','sources','contact']){await page.goto(`${base}/${path}/`);await page.waitForSelector('.prose');assert.ok((await page.locator('h1').innerText()).length);await page.screenshot({path:`${out}/react-page-${path}.png`,fullPage:true});results.push({test:'footer-route',path});}
 await page.goto(base+'/contact/');await page.locator('[name="name"]').fill('UI QA');await page.locator('[name="email"]').fill('qa@example.com');await page.locator('[name="message"]').fill('Local browser verification message');await page.getByRole('button',{name:'Send message'}).click();await page.waitForFunction(()=>document.querySelector('.message-form [role="status"]').textContent.includes('received'));results.push({test:'contact-csrf-submit',pass:true});
 // Synthetic responses only in browser test interception, never application data.
 const fixture=await (await fetch(backend+'/api/articles/?page_size=3')).json();
 await page.route('**/api/articles/?*',async route=>{const n=new URL(route.request().url()).searchParams.get('page');await route.fulfill({json:{count:4,next:n==='1'?'http://unused.invalid/page2':null,results:n==='1'?fixture.results:fixture.results.slice(0,1)}})});
 await page.goto(base+'/stories/');await page.waitForSelector('.news-grid .story-card');await page.getByRole('button',{name:/Load more stories/}).click();await page.waitForFunction(()=>!document.querySelector('.load-more'));assert.equal(await page.locator('.news-grid .story-card').count(),3);results.push({test:'load-more-dedup-fixture',pass:true});await page.unroute('**/api/articles/?*');
 await page.route('**/api/home/',r=>r.fulfill({json:{carousel:[],featured:[],excluded:[]}}));await page.route('**/api/articles/?*',r=>r.fulfill({json:{count:0,next:null,results:[]}}));await page.goto(base+'/');await page.waitForSelector('.state h2');await page.screenshot({path:out+'/react-empty.png',fullPage:true});results.push({test:'empty-fixture',pass:true});await page.unroute('**/api/home/');await page.unroute('**/api/articles/?*');
 await page.route('**/api/home/',r=>r.fulfill({status:503,json:{error:'QA simulated outage'}}));await page.reload();await page.waitForSelector('.state h2');assert.match(await page.locator('.state').innerText(),/temporarily unavailable/);await page.screenshot({path:out+'/react-error.png',fullPage:true});results.push({test:'error-fixture',pass:true});await page.unroute('**/api/home/');
 await page.goto(base+'/');await page.waitForSelector('.latest .story-card');
 const snapshot=await page.evaluate(()=>{const doc=document.documentElement.cloneNode(true);doc.querySelectorAll('script').forEach(e=>e.remove());doc.querySelectorAll('img').forEach(e=>{e.src=new URL(e.getAttribute('src'),location.href).href});return '<!doctype html>'+doc.outerHTML});fs.writeFileSync(out+'/react-snapshot.html',snapshot);
 assert.deepEqual(errors,[]);fs.writeFileSync(path.resolve(__dirname,'../../docs/verification/browser-results.json'),JSON.stringify({results,errors},null,2));console.log(JSON.stringify({checks:results.length,errors,pass:true}));
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
