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
  const motion=matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('[data-component="image-slider"]').forEach(component=>{
    const track=component.querySelector('.vertical-track'),windowEl=component.querySelector('.vertical-window');
    const slides=[...track.children];if(!slides.length)return;
    const clone=slides[0].cloneNode(true);clone.dataset.clone='true';clone.setAttribute('aria-hidden','true');clone.inert=true;clone.querySelectorAll('a').forEach(a=>a.tabIndex=-1);track.append(clone);
    let index=0,busy=false,userPaused=false,hover=false,focus=false,timer=null,settleTimer=null;
    const pause=component.querySelector('[data-slide="pause"]');
    const stopped=()=>userPaused||hover||focus||motion.matches||document.hidden||slides.length<2;
    function schedule(){clearTimeout(timer);if(!stopped())timer=setTimeout(()=>move(1),3000);}
    function state(){slides.forEach((s,n)=>{s.inert=!motion.matches&&n!==index%slides.length;s.setAttribute('aria-hidden',String(!motion.matches&&n!==index%slides.length));});component.querySelector('.slide-count').textContent=`${index%slides.length+1} / ${slides.length}`;pause.textContent=userPaused?'▶':'Ⅱ';pause.setAttribute('aria-pressed',String(userPaused));pause.setAttribute('aria-label',`${userPaused?'Resume':'Pause'} image headline slider`);}
    function position(animate=true){track.style.transition=animate&&!motion.matches?'transform .5s ease':'none';track.style.transform=`translateY(${-index*windowEl.clientHeight}px)`;}
    function move(delta){if(busy||motion.matches||slides.length<2)return;clearTimeout(timer);busy=true;if(delta<0&&index===0){index=slides.length;position(false);track.offsetHeight;}index+=delta;position(true);state();clearTimeout(settleTimer);settleTimer=setTimeout(settle,600);}
    function settle(){clearTimeout(settleTimer);if(index>=slides.length){index=0;position(false);}busy=false;state();schedule();}
    track.addEventListener('transitionend',e=>{if(e.propertyName==='transform')settle();});
    pause.addEventListener('click',()=>{userPaused=!userPaused;state();schedule();});
    component.querySelector('[data-slide="prev"]').addEventListener('click',()=>move(-1));component.querySelector('[data-slide="next"]').addEventListener('click',()=>move(1));
    component.addEventListener('mouseenter',()=>{hover=true;schedule();});component.addEventListener('mouseleave',()=>{hover=false;schedule();});
    component.addEventListener('focusin',()=>{focus=true;schedule();});component.addEventListener('focusout',()=>{setTimeout(()=>{focus=component.contains(document.activeElement);schedule();},0);});
    document.addEventListener('visibilitychange',schedule);motion.addEventListener('change',()=>{index=0;busy=false;position(false);state();schedule();});new ResizeObserver(()=>position(false)).observe(windowEl);
    // Fit the longest actual headline, including long imports and translated text.
    const resize=()=>{if(motion.matches){windowEl.style.height='';[...slides,clone].forEach(s=>{s.style.height='';s.style.flexBasis='';});return;}
      const baseline=matchMedia('(max-width:760px)').matches?260:152;
      const height=Math.ceil(Math.max(baseline,...slides.map(s=>Math.max(s.lastElementChild.scrollHeight,s.querySelector('.slide-photo').getBoundingClientRect().height)+16)));
      if(windowEl.style.height!==height+'px'){windowEl.style.height=height+'px';[...slides,clone].forEach(s=>{s.style.height=height+'px';s.style.flexBasis=height+'px';});position(false);}
    };
    const sizing=new ResizeObserver(resize);slides.forEach(s=>sizing.observe(s.lastElementChild));motion.addEventListener('change',resize);resize();
    state();position(false);schedule();
  });
  document.querySelectorAll('[data-component="headlines-marquee"]').forEach(component=>{
    const track=component.querySelector('.marquee-track'),sequence=component.querySelector('.headline-sequence'),viewport=component.querySelector('.marquee-window'),button=component.querySelector('[data-marquee-pause]');
    const clone=sequence.cloneNode(true);clone.dataset.clone='true';clone.setAttribute('aria-hidden','true');clone.inert=true;clone.querySelectorAll('a').forEach(a=>a.tabIndex=-1);track.append(clone);
    let paused=false;const refresh=()=>{const width=sequence.getBoundingClientRect().width;track.style.setProperty('--marquee-distance',`${width}px`);track.style.setProperty('--marquee-duration',`${width/Math.max(24,viewport.clientWidth/40)}s`);track.classList.toggle('is-animated',width>viewport.clientWidth&&!motion.matches);};
    button.addEventListener('click',()=>{paused=!paused;track.classList.toggle('paused',paused);button.textContent=paused?'▶':'Ⅱ';button.setAttribute('aria-label',`${paused?'Resume':'Pause'} continuous Headlines strip`);button.setAttribute('aria-pressed',String(paused));});
    // Focused links must be readable, not frozen outside an overflow-hidden viewport.
    sequence.addEventListener('focusin',()=>{track.classList.remove('is-animated');viewport.style.overflowX='auto';document.activeElement.scrollIntoView({block:'nearest',inline:'nearest'});});
    component.addEventListener('focusout',()=>setTimeout(()=>{if(!component.contains(document.activeElement)){viewport.scrollLeft=0;viewport.style.overflowX='';refresh();}},0));
    new ResizeObserver(refresh).observe(sequence);new ResizeObserver(refresh).observe(viewport);motion.addEventListener('change',refresh);refresh();
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
