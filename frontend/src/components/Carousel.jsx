import React,{useState,useEffect,useRef,useContext} from 'react';
import {Link} from 'react-router-dom';
import {StoryImage} from './StoryCard';
import {Translation} from '../context/Translation';

export const SLIDE_INTERVAL_MS=7000;
const SWIPE_PX=48;

// Horizontal headline slider. Every slide is rendered side by side in one track and the
// track is moved with a CSS transform, so the outgoing and incoming slides are both on
// screen during the move and no image is re-created. Exactly one timeout is pending at
// any moment (never an interval), and it is cleared whenever the state that owns it changes.
export default function Carousel({articles=[]}){
 const t=useContext(Translation);
 const reducedMotion=typeof window!=='undefined'&&typeof window.matchMedia==='function'&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 const [index,setIndex]=useState(0),[playing,setPlaying]=useState(!reducedMotion),[visible,setVisible]=useState(typeof document==='undefined'||!document.hidden),[hold,setHold]=useState(false);
 const stories=Array.from(new Map(articles.filter(Boolean).map(a=>[a.id,a])).values()).slice(0,6);
 const count=stories.length,active=count?index%count:0;
 const drag=useRef(null),swiped=useRef(false);
 const ids=stories.map(a=>a.id).join(',');
 useEffect(()=>{setIndex(0)},[ids]);
 useEffect(()=>{const visibility=()=>setVisible(!document.hidden);document.addEventListener('visibilitychange',visibility);return()=>document.removeEventListener('visibilitychange',visibility)},[]);
 useEffect(()=>{
  if(!playing||!visible||hold||count<2)return;
  const timer=setTimeout(()=>setIndex(i=>(i+1)%count),SLIDE_INTERVAL_MS);
  return()=>clearTimeout(timer);
 },[playing,visible,hold,count,active]);
 const go=n=>setIndex((n+count)%count);
 const onPointerDown=e=>{drag.current={x:e.clientX,y:e.clientY};swiped.current=false};
 const onPointerUp=e=>{const d=drag.current;drag.current=null;if(!d||count<2)return;const dx=e.clientX-d.x,dy=e.clientY-d.y;if(Math.abs(dx)>SWIPE_PX&&Math.abs(dx)>Math.abs(dy)*1.5){swiped.current=true;go(active+(dx<0?1:-1))}};
 if(!count)return <section className="carousel carousel-empty"><span className="eyebrow">{t('ui:latest_headlines','LATEST HEADLINES')}</span><h2>News sliding animation</h2><p>Published headlines will appear here when available.</p></section>;
 return <section className="carousel" aria-label="Latest headlines" aria-roledescription="carousel" onMouseEnter={()=>setHold(true)} onMouseLeave={()=>setHold(false)} onFocus={()=>setHold(true)} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget))setHold(false)}}>
  <div className="slider-topline"><span className="eyebrow">{t('ui:latest_headlines','LATEST HEADLINES')}</span><span className="carousel-counter">{String(active+1).padStart(2,'0')} <span>/ {String(count).padStart(2,'0')}</span></span></div>
  <div className="slider-viewport" onPointerDown={onPointerDown} onPointerUp={onPointerUp} onPointerCancel={()=>{drag.current=null}} onDragStart={e=>e.preventDefault()} onClickCapture={e=>{if(swiped.current){e.preventDefault();e.stopPropagation();swiped.current=false}}}>
   <div className="slider-track" data-active={active} style={{transform:`translate3d(${-active*100}%,0,0)`}} aria-live={playing&&!hold?'off':'polite'}>
    {stories.map((a,i)=><div className="slider-slide" key={a.id} role="group" aria-roledescription="slide" aria-label={`${i+1} / ${count}`} aria-hidden={i===active?undefined:'true'} inert={i===active?undefined:true} data-active={i===active?'true':'false'}>
     <Link className="slider-image" to={`/story/${a.slug}/`} tabIndex={i===active?0:-1}><StoryImage article={a} eager/></Link>
     <div className="slider-copy"><span className="category">{a.category?.name||'News'}</span><h2><Link to={`/story/${a.slug}/`} tabIndex={i===active?0:-1}>{t(`article:${a.id}:title`,a.title)}</Link></h2><p>{t(`article:${a.id}:excerpt`,a.excerpt)}</p><small>{a.source_name||'NexusUp'}{a.date?` · ${new Date(a.date).toLocaleDateString()}`:''}</small><Link className="read-story" to={`/story/${a.slug}/`} tabIndex={i===active?0:-1}>{t('ui:read','Read story')} <span aria-hidden="true">↗</span></Link></div>
    </div>)}
   </div>
  </div>
  <div className="carousel-bottom"><div className="slide-indicators" aria-label="Choose headline">{stories.map((story,i)=><button key={story.id} aria-label={`Go to headline ${i+1}`} aria-current={i===active?'true':undefined} onClick={()=>go(i)}><span aria-hidden="true"/></button>)}</div><small className="playback-note">{playing?'Stories switch automatically':'Automatic sliding paused'}</small><div className="controls"><button aria-label="Previous headline" disabled={count<2} onClick={()=>go(active-1)}>←</button><button aria-label={playing?'Pause slider':'Play slider'} aria-pressed={playing} disabled={count<2} onClick={()=>setPlaying(v=>!v)}>{playing?t('ui:pause','Pause'):t('ui:play','Play')}</button><button aria-label="Next headline" disabled={count<2} onClick={()=>go(active+1)}>→</button></div></div>
 </section>
}
