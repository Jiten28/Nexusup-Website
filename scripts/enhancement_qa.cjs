/* Run against a local sample-only server. Requires npm package playwright and Chromium.
   QA_BASE_URL defaults to localhost. QA_OUT defaults to /tmp/nexusup-qa. */
const { chromium }=require(process.env.PLAYWRIGHT_MODULE||'playwright');const fs=require('fs'),assert=require('assert');
const base=process.env.QA_BASE_URL||'http://127.0.0.1:8000',out=process.env.QA_OUT||'/tmp/nexusup-qa';fs.mkdirSync(out,{recursive:true});
let browser;const report={checks:[],layouts:[],palettes:[],pageErrors:[],unexpectedRequests:[]};
const check=(name,ok,detail='')=>{report.checks.push({name,pass:!!ok,detail});assert(ok,name+' '+detail);};
async function overflow(page){return page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,broken:[...document.images].filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src),outside:[...document.querySelectorAll('main h1,main h2,main h3,.magazine-header,.popover,dialog[open]')].filter(e=>e.getBoundingClientRect().width&& (e.getBoundingClientRect().right>innerWidth+1||e.getBoundingClientRect().left< -1)).map(e=>e.className||e.tagName)}));}
async function shot(page,name,full=false){await page.screenshot({path:out+'/'+name+'.png',fullPage:full,animations:'disabled'});}
async function openTool(page,name){await page.locator('#widgets-menu>summary').click();await page.locator('#widgets-menu [data-widget="'+name+'"]').click();await page.locator('#utility-dialog').waitFor({state:'visible'});}
async function closeTool(page){await page.locator('#close-utility').click();}
function rgb(s){return(s.match(/[\d.]+/g)||[]).slice(0,3).map(Number);}
function contrast(a,b){const lum=x=>rgb(x).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);const x=lum(a),y=lum(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
(async()=>{try{
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/local/bin/chromium',headless:true,args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1440,height:1000},colorScheme:'light',permissions:['clipboard-read','clipboard-write']});
 const page=await context.newPage();page.on('pageerror',e=>report.pageErrors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('data:'))report.unexpectedRequests.push(r.url());});
 await page.goto(base);await page.waitForLoadState('networkidle');
 check('two separate news animations',await page.locator('[data-component]').count()===2);
 check('actual visible slider image',await page.locator('.headline-slide:not([data-clone]) img').count()>0);
 // Slider autoplay, controls, hover/focus pause, wrap. Do not disable motion here.
 await page.mouse.move(1,999);const before=await page.locator('.slide-count').textContent();await page.waitForTimeout(3750);check('slider autoplay advances',before!==await page.locator('.slide-count').textContent());
 await page.locator('[data-slide="next"]').click();await page.waitForTimeout(600);const after=await page.locator('.slide-count').textContent();
 await page.waitForTimeout(3400);check('slider pauses on focus/hover',after===await page.locator('.slide-count').textContent());
 for(let i=0;i<7;i++){await page.locator('[data-slide="next"]').click();await page.waitForTimeout(550);}check('slider wraps after repeated navigation',/^\d \/ 6$/.test(await page.locator('.slide-count').textContent()));
 await page.locator('[data-slide="prev"]').click();await page.waitForTimeout(550);
 await page.locator('[data-slide="pause"]').click();check('slider pause control',await page.locator('[data-slide="pause"]').getAttribute('aria-pressed')==='true');
 await page.locator('.edition-heading h1').click();await page.mouse.move(1,999);
 const transform=()=>page.locator('.marquee-track').evaluate(e=>getComputedStyle(e).transform);
 const t0=await transform();await page.waitForTimeout(200);check('headlines continuously move left',t0!==await transform());
 await page.locator('[data-marquee-pause]').click();check('marquee pause button',await page.locator('.marquee-track').evaluate(e=>getComputedStyle(e).animationPlayState)==='paused');
 await page.locator('.headline-sequence:not([data-clone]) a').nth(4).focus();check('keyboard headline remains readable',await page.locator('.marquee-window').evaluate(e=>getComputedStyle(e).overflowX)==='auto');
 await page.locator('.edition-heading h1').click();await page.mouse.move(1,999);
 const bounds=await page.locator('.magazine-feature').evaluate(e=>{let b=s=>e.querySelector(s).getBoundingClientRect();return {left:b('.feature-left').x,center:b('.feature-center').x,right:b('.feature-right').x,centerWidth:b('.feature-center').width,sideWidth:b('.feature-left').width};});
 check('large center / two stories each side',bounds.left<bounds.center&&bounds.center<bounds.right&&bounds.centerWidth>bounds.sideWidth*1.5&&await page.locator('.feature-support').count()===4);
 for(const width of [360,390,768,1024,1440]){
   await page.setViewportSize({width,height:width<600?844:1000});await page.waitForTimeout(150);
   const layout=await overflow(page);layout.columns=await page.locator('.latest-grid').evaluate(e=>getComputedStyle(e).gridTemplateColumns.split(' ').length);report.layouts.push(layout);
   check('layout '+width+' no horizontal overflow/broken images',layout.scroll<=width&&layout.broken.length===0&&layout.outside.length===0,JSON.stringify(layout));
   for(const menu of ['palette','language','widgets']){await page.locator('#'+menu+'-menu>summary').click();await page.waitForTimeout(80);const b=await page.locator('#'+menu+'-menu .popover').boundingBox();check(menu+' menu fits '+width,b.x>=0&&b.x+b.width<=width+1);await page.keyboard.press('Escape');}
   await shot(page,'home-'+width);
 }
 await page.setViewportSize({width:1440,height:1000});
 for(const appearance of ['light','dark']){
   let theme=await page.locator('html').getAttribute('data-theme');if((theme||'light')!==appearance)await page.locator('#theme-toggle').click();
   for(const palette of ['ocean','violet','emerald','sunset']){
     await page.locator('#palette-menu>summary').click();await page.locator('button[data-palette="'+palette+'"]').click();await page.keyboard.press('Escape');
     const colors=await page.evaluate(()=>{const root=getComputedStyle(document.documentElement);const color=s=>{const el=document.createElement('span');el.style.color=`var(${s})`;document.body.append(el);let c=getComputedStyle(el).color;el.remove();return c;};return {ink:color('--ink'),surface:color('--surface'),muted:color('--muted'),accent:color('--accent'),buttonInk:color('--button-ink'),bg:color('--bg'),band1:color('--band1'),band2:color('--band2'),button:color('--button'),soft:color('--soft')};});
     const checks={body:contrast(colors.ink,colors.surface),muted:contrast(colors.muted,colors.surface),accent:contrast(colors.accent,colors.surface),badge:contrast(colors.buttonInk,colors.accent),nav1:contrast('rgb(255,255,255)',colors.band1),nav2:contrast('rgb(255,255,255)',colors.band2)};
     check('button token follows '+appearance+' '+palette,colors.button===colors.accent);report.palettes.push({appearance,palette,colors,contrast:checks});check(appearance+' '+palette+' text contrast',Object.values(checks).every(v=>v>=4.5),JSON.stringify(checks));
     check('independent palette and appearance',await page.locator('html').getAttribute('data-palette')===palette&&((await page.locator('html').getAttribute('data-theme'))||'light')===appearance);
     await shot(page,appearance+'-'+palette);
   }
 }
 await page.reload();check('both preferences persist',await page.locator('html').getAttribute('data-theme')==='dark'&&await page.locator('html').getAttribute('data-palette')==='sunset');
 await page.setViewportSize({width:390,height:844});
 // Local calculator, validation, keyboard dialog close/focus.
 await openTool(page,'calculator');await page.fill('#calc-input','(24 + 6) / 3');await page.locator('#calc-form button').click();check('calculator arithmetic',(await page.locator('.utility-result').textContent())==='10');
 await page.fill('#calc-input','1 / 0');await page.locator('#calc-form button').click();check('calculator divide by zero',/zero/.test(await page.locator('.utility-result').textContent()));await shot(page,'widget-calculator');await page.keyboard.press('Escape');check('dialog Escape restores menu focus',await page.locator('#widgets-menu>summary').evaluate(e=>e===document.activeElement));
 await openTool(page,'units');await page.selectOption('#unit-kind','temperature');await page.fill('#unit-value','0');await page.locator('#utility-content form button').click();check('temperature conversion',await page.locator('.utility-result').textContent()==='32 F');await shot(page,'widget-units');await closeTool(page);
 await openTool(page,'calendar');let month=await page.locator('#month-title').textContent();await page.locator('#month-next').click();check('calendar next month',month!==await page.locator('#month-title').textContent());await page.locator('#month-today').click();check('calendar today',month===await page.locator('#month-title').textContent());await shot(page,'widget-calendar');await closeTool(page);
 await openTool(page,'clock');await page.selectOption('#clock-city','Tokyo');check('world clock add city',await page.locator('.clock-list').textContent().then(t=>t.includes('Tokyo')));await page.getByRole('button',{name:'Remove London',exact:true}).focus();await page.waitForTimeout(1100);check('world clock tick retains keyboard focus',await page.getByRole('button',{name:'Remove London',exact:true}).evaluate(e=>e===document.activeElement));await page.getByRole('button',{name:'Remove London',exact:true}).click();await shot(page,'widget-clock');await closeTool(page);
 // Default-off service states are real backend responses, not simulated.
 await openTool(page,'currency');await page.locator('#utility-content form button').click();await page.waitForFunction(()=>document.querySelector('.utility-result').textContent==='Rate unavailable');check('currency disabled state',/disabled/.test(await page.locator('#widget-status').textContent()));await shot(page,'widget-currency-disabled');await closeTool(page);
 await openTool(page,'weather');await page.fill('#city-query','Hyderabad');await page.locator('#city-form button').click();await page.waitForFunction(()=>document.querySelector('#widget-status').textContent.includes('disabled'));check('weather manual fallback after provider failure',await page.locator('#coordinates-form').count()===1);
 await context.grantPermissions([], {origin:base});await page.locator('#detect-location').click();await page.waitForTimeout(300);await shot(page,'widget-weather-disabled');await closeTool(page);
 // Deterministic browser-only fixtures cover successful interactions without contacting providers.
 await page.route('**/api/currency/**',r=>r.fulfill({json:{rate:.012,date:'2026-10-18',source:'QA fixture'}}));await openTool(page,'currency');await page.fill('#fx-amount','100');await page.locator('#utility-content form button').click();await page.waitForFunction(()=>document.querySelector('.utility-result').textContent.includes('1.20'));check('currency successful fixture conversion',/1\.20/.test(await page.locator('.utility-result').textContent()));await closeTool(page);
 await page.route('**/api/cities/**',r=>r.fulfill({json:{results:[{name:'Hyderabad, Telangana, India',latitude:17.38,longitude:78.48}]}}));await page.route('**/api/weather/**',r=>r.fulfill({json:{temperature:27,weather_code:0,wind:8,time:'2026-10-18T05:00:00Z',source:'QA fixture'}}));await openTool(page,'weather');await page.fill('#city-query','Hyderabad');await page.locator('#city-form button').click();await page.locator('.city-results button').click();await page.waitForFunction(()=>document.querySelector('.utility-result').textContent.includes('27'));check('manual city weather fixture',/Updated/.test(await page.locator('#widget-status').textContent()));await shot(page,'widget-weather-fixture');await closeTool(page);
 await page.locator('#language-menu>summary').click();await page.waitForTimeout(100);check('translation disabled state original retained',/not configured/.test(await page.locator('#language-status').textContent()));await page.keyboard.press('Escape');
 await page.route('**/api/languages/',r=>r.fulfill({json:{provider:'QA fixture',languages:[{code:'en',name:'English'},{code:'hi',name:'Hindi'}]}}));await page.route('**/api/translate/',r=>r.fulfill({json:{texts:{'ui:home':'होम'},notice:'QA fixture machine translation.'}}));
 await page.locator('#language-menu>summary').click();await page.waitForTimeout(150);await page.selectOption('#language-select','hi');await page.waitForFunction(()=>document.documentElement.lang==='hi');check('translation preserves anchor target',await page.locator('#primary-nav a').first().getAttribute('href')==='/');await page.locator('#original-language').click();check('original English restored',await page.locator('html').getAttribute('lang')==='en');await page.keyboard.press('Escape');
 await page.locator('#menu-toggle').click();check('mobile menu opens',await page.locator('#primary-nav').isVisible());await page.keyboard.press('Escape');check('mobile menu Escape closes',!await page.locator('#primary-nav').isVisible());
 // Article, archives, search, contact and original browser-local save/copy behavior.
 await page.goto(base+'/stories/');await page.locator('.story-card h3 a').first().click();await page.locator('[data-save]').click();check('save story state',await page.locator('[data-save]').getAttribute('aria-pressed')==='true');await page.reload();check('save persists',await page.locator('[data-save]').getAttribute('aria-pressed')==='true');await page.locator('#share-button').click();await page.waitForFunction(()=>/copied|unavailable/.test(document.querySelector('#action-status').textContent));check('copy link action',/copied|unavailable/.test(await page.locator('#action-status').textContent()));await shot(page,'article-mobile');
 await page.setViewportSize({width:1440,height:1000});await shot(page,'article-desktop');
 for(const [path,name]of [['/stories/','archive'],['/search/?q=portfolio','search'],['/category/business/','category'],['/contact/','contact'],['/about/','about'],['/privacy/','privacy'],['/terms/','terms'],['/story/missing/','404']]){await page.goto(base+path);const o=await overflow(page);check(name+' no overflow',o.scroll<=o.width&&o.broken.length===0);if(['archive','search','contact'].includes(name))await shot(page,name);}
 await page.goto(base+'/');await page.emulateMedia({reducedMotion:'reduce'});check('reduced motion exposes originals only',await page.locator('.headline-slide:not([data-clone]):visible').count()===6&&await page.locator('.headline-slide[data-clone]:visible').count()===0);check('reduced motion marquee stops',await page.locator('.marquee-track').evaluate(e=>getComputedStyle(e).animationName)==='none');await shot(page,'reduced-motion');
 // System preference applies only until explicit appearance selection.
 const system=await browser.newContext({colorScheme:'dark'});const sys=await system.newPage();await sys.goto(base);check('system dark preference',await sys.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--bg').trim())==='#0c1728');await sys.locator('#theme-toggle').click();check('explicit light overrides system',await sys.locator('html').getAttribute('data-theme')==='light');await system.close();
 check('no browser JS errors',report.pageErrors.length===0,JSON.stringify(report.pageErrors));check('no unsolicited external requests',report.unexpectedRequests.length===0,JSON.stringify(report.unexpectedRequests));
 report.pass=true;
}catch(e){report.pass=false;report.error=e.stack;console.error(e.message);}finally{fs.writeFileSync(out+'/browser-results.json',JSON.stringify(report,null,2));if(browser)await browser.close();console.log(JSON.stringify({pass:report.pass,checks:report.checks.length,failed:report.checks.filter(x=>!x.pass),error:report.error},null,2));process.exit(report.pass?0:1);}})();
