// Optional local-only Playwright QA. Not a frontend dependency.
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const browser=await chromium.launch({executablePath:require('child_process').execSync('command -v chromium').toString().trim(),headless:true,args:['--no-sandbox']});const reports=[];const external=new Set();const errors=[];
for(const width of [1440,390]){
 const context=await browser.newContext({viewport:{width,height:900},colorScheme:'light'});const page=await context.newPage();
 page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8000/'))external.add(r.url())});page.on('pageerror',e=>errors.push(e.message));
 for(const path of ['/','/stories/','/stories/?page=2','/category/cricket/','/category/business/','/category/stock-market/','/category/investments/','/category/technology/','/category/science/','/search/?q=portfolio','/search/?q=noresultszz','/search/?q='+'x'.repeat(150),'/story/beyond-the-boundary-a-fresh-lens-on-the-game/','/contact/','/about/','/privacy/','/terms/']){
  const response=await page.goto('http://127.0.0.1:8000'+path);await page.waitForLoadState('networkidle');
  await page.evaluate(async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,30));}window.scrollTo(0,0);});await page.waitForLoadState('networkidle');
  await page.evaluate(()=>Promise.all([...document.images].map(i=>{i.loading='eager';return i.decode().catch(()=>{});})));
  const check=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,brokenImages:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)}));
  reports.push({width,path,status:response.status(),...check});
 }
 await page.goto('http://127.0.0.1:8000/');
 if(width===390){await page.click('#menu-toggle');if(await page.getAttribute('#menu-toggle','aria-expanded')!=='true')throw Error('Menu did not open');await page.keyboard.press('Escape');if(await page.getAttribute('#menu-toggle','aria-expanded')!=='false')throw Error('Escape did not close menu');}
 await page.click('#theme-toggle');await page.reload();if(await page.getAttribute('html','data-theme')!=='dark')throw Error('Dark mode did not persist');await page.click('#theme-toggle');
 await page.goto('http://127.0.0.1:8000/story/beyond-the-boundary-a-fresh-lens-on-the-game/');await page.click('[data-save]');await page.reload();if(await page.getAttribute('[data-save]','aria-pressed')!=='true')throw Error('Save did not persist');
 await page.click('#share-button');await page.waitForTimeout(100);if(!await page.locator('#action-status').textContent())throw Error('Missing clipboard feedback');
 await page.goto('http://127.0.0.1:8000/search/');await page.fill('#q','portfolio');await page.locator('.search-form button').click();await page.waitForLoadState('networkidle');if(!await page.locator('h1').textContent().then(t=>t.includes('portfolio')))throw Error('Search form failed');
 await context.close();
}
const nojs=await browser.newContext({viewport:{width:390,height:844},javaScriptEnabled:false});const page=await nojs.newPage();await page.goto('http://127.0.0.1:8000/');if(!await page.locator('#primary-nav').isVisible())throw Error('No-JS navigation hidden');await nojs.close();
const failed=reports.filter(x=>x.status!==200||x.overflow||x.brokenImages.length);fs.writeFileSync(require('path').join(__dirname,'../docs/browser-results.json'),JSON.stringify({reports,interactionChecks:['mobile menu opens','Escape closes menu','theme persists','story save persists','copy-link feedback','search submits','no-JS navigation visible'],externalRequests:[...external],javascriptErrors:errors,failures:failed},null,2));console.log(JSON.stringify({routesChecked:reports.length,externalRequests:external.size,javascriptErrors:errors.length,failures:failed}));await browser.close();process.exit(failed.length||errors.length||external.size?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
