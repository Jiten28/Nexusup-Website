(() => {
  'use strict';
  const read = key => {try{return localStorage.getItem(key);}catch{return null;}};
  const store = (key,value) => {try{localStorage.setItem(key,value);}catch{}};
  const root=document.documentElement;
  const palettes=['ocean','violet','emerald','sunset'];
  const applyPalette=value=>{root.dataset.palette=palettes.includes(value)?value:'ocean';document.querySelectorAll('[data-palette]').forEach(b=>{if(b.tagName==='BUTTON')b.setAttribute('aria-pressed',String(b.dataset.palette===root.dataset.palette));});};
  applyPalette(read('nexusup-palette')||'ocean');
  document.querySelectorAll('button[data-palette]').forEach(b=>b.addEventListener('click',()=>{applyPalette(b.dataset.palette);store('nexusup-palette',b.dataset.palette);}));
  const popovers=[...document.querySelectorAll('.header-popover')];
  popovers.forEach(d=>d.addEventListener('toggle',()=>{if(d.open)popovers.forEach(other=>{if(other!==d)other.open=false;});}));
  document.addEventListener('click',e=>{if(!e.target.closest('.header-popover'))popovers.forEach(d=>d.open=false);});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')popovers.forEach(d=>{if(d.open){d.open=false;d.querySelector('summary').focus();}});});
  let tz='UTC';try{tz=Intl.DateTimeFormat().resolvedOptions().timeZone||'UTC';new Intl.DateTimeFormat('en',{timeZone:tz}).format();}catch{tz='UTC';}
  const tick=()=>{const now=new Date();const clock=document.getElementById('visitor-clock'),date=document.getElementById('visitor-date');if(clock){clock.textContent=new Intl.DateTimeFormat('en-IN',{hour:'2-digit',minute:'2-digit',timeZone:tz}).format(now);clock.dateTime=now.toISOString();clock.title=tz;}if(date)date.textContent=new Intl.DateTimeFormat('en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:tz}).format(now);};tick();setInterval(tick,30000);
  // One horizontal image strip; manual by default. The old vertical slider and
  // cloned continuous marquee were consolidated without duplicate focus targets.
  const motion=matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('[data-component="horizontal-headlines"]').forEach(component=>{
    const track=component.querySelector('.horizontal-headlines-track');let playing=false,hover=false,focus=false;
    const move=direction=>{const end=track.scrollWidth-track.clientWidth;track.scrollTo({left:direction>0&&track.scrollLeft>=end-3?0:direction<0&&track.scrollLeft<=3?end:track.scrollLeft+direction*320,behavior:motion.matches?'instant':'smooth'});};
    component.querySelector('[data-horizontal="prev"]').onclick=()=>move(-1);
    component.querySelector('[data-horizontal="next"]').onclick=()=>move(1);
    const pause=component.querySelector('[data-horizontal="pause"]');pause.onclick=()=>{playing=!playing;pause.textContent=playing?'Pause':'Play';pause.setAttribute('aria-pressed',String(playing));};
    component.onmouseenter=()=>hover=true;component.onmouseleave=()=>hover=false;
    component.onfocusin=()=>focus=true;component.onfocusout=()=>setTimeout(()=>focus=component.contains(document.activeElement),0);
    setInterval(()=>{if(playing&&!hover&&!focus&&!motion.matches&&!document.hidden)move(1)},6000);
  });
  // Translation never replaces links, inputs, event handlers or markup; only marked textContent.
  const languageMenu=document.getElementById('language-menu'),select=document.getElementById('language-select'),status=document.getElementById('language-status');
  const originals=new Map([...document.querySelectorAll('[data-i18n]')].map(el=>[el,el.textContent]));let languageLoaded=false;
  const restore=()=>{originals.forEach((text,el)=>el.textContent=text);root.lang='en';root.dir='ltr';select.value='en';document.getElementById('language-label').textContent='EN';store('nexusup-language','en');status.textContent='Original English restored.';};
  async function changeLanguage(code){if(code==='en'){restore();return;}status.textContent='Translating public article text…';select.disabled=true;
    try{const token=document.querySelector('.csrf-holder input').value;const response=await fetch('/api/translate/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':token},body:JSON.stringify({path:location.pathname,language:code})});const data=await response.json();if(!response.ok)throw Error(data.error||'Translation unavailable');originals.forEach((text,el)=>{el.textContent=data.texts[el.dataset.i18n]||text;});root.lang=code;root.dir=['ar','he','fa','ur'].includes(code)?'rtl':'ltr';document.getElementById('language-label').textContent=code.toUpperCase();status.textContent=data.notice+' Some interface labels remain English.';store('nexusup-language',code);}
    catch(e){status.textContent=e.message+' Original content retained.';select.value=read('nexusup-language')||'en';}finally{select.disabled=false;}}
  async function loadLanguages(){if(languageLoaded)return;languageLoaded=true;status.textContent='Checking configured service…';try{const response=await fetch('/api/languages/');const data=await response.json();if(!response.ok)throw Error(data.error);for(const lang of data.languages){if(lang.code==='en')continue;const option=document.createElement('option');option.value=lang.code;option.textContent=lang.name;select.append(option);}status.textContent='Machine translation via '+data.provider+'. Available languages come from the configured provider.';const saved=read('nexusup-language');if(saved&&saved!=='en'&&[...select.options].some(o=>o.value===saved)){select.value=saved;await changeLanguage(saved);}}catch(e){status.textContent=e.message;languageLoaded=false;}}
  languageMenu?.addEventListener('toggle',()=>{if(languageMenu.open)loadLanguages();});select?.addEventListener('change',()=>changeLanguage(select.value));document.getElementById('original-language')?.addEventListener('click',restore);if(read('nexusup-language')&&read('nexusup-language')!=='en')loadLanguages();
})();
