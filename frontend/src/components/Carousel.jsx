import React,{useState,useEffect} from 'react';
import {Link} from 'react-router-dom';
import {StoryImage} from './StoryCard';

// Full-width, single-story slider matching the user's sketch. The separate
// large-story/right-sidebar composition now lives in the latest-news grid.
export default function Carousel({articles=[]}){
 const reducedMotion=typeof window!=='undefined'&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 const [index,setIndex]=useState(0),[playing,setPlaying]=useState(!reducedMotion),[visible,setVisible]=useState(typeof document==='undefined'||!document.hidden);
 const stories=Array.from(new Map(articles.filter(Boolean).map(a=>[a.id,a])).values()).slice(0,6);
 const count=stories.length,active=count?index%count:0;
 useEffect(()=>{setIndex(0)},[stories.map(a=>a.id).join(',')]);
 useEffect(()=>{const visibility=()=>setVisible(!document.hidden);document.addEventListener('visibilitychange',visibility);return()=>document.removeEventListener('visibilitychange',visibility)},[]);
 useEffect(()=>{if(!playing||!visible||count<2)return;const timer=setInterval(()=>setIndex(i=>(i+1)%count),7500);return()=>clearInterval(timer)},[playing,visible,count,index]);
 const go=n=>setIndex((n+count)%count);
 if(!count)return <section className="carousel carousel-empty"><span className="eyebrow">LATEST HEADLINES</span><h2>News sliding animation</h2><p>Published headlines will appear here when available.</p></section>;
 const a=stories[active];
 return <section className="carousel sketch-slider" aria-label="Latest headlines" aria-roledescription="carousel">
  <div className="slider-topline"><span className="eyebrow">LATEST HEADLINES</span><span className="carousel-counter">{String(active+1).padStart(2,'0')} <span>/ {String(count).padStart(2,'0')}</span></span></div>
  <div className="sketch-slide" key={a.id}>
   <Link className="sketch-slide-image" to={`/story/${a.slug}/`}><StoryImage article={a} eager /></Link>
   <div className="sketch-slide-copy"><span className="category">{a.category?.name||'News'}</span><h2><Link to={`/story/${a.slug}/`}>{a.title}</Link></h2><p>{a.excerpt}</p><small>{a.source_name||'NexusUp'}{a.date?` · ${new Date(a.date).toLocaleDateString()}`:''}</small><Link className="read-story" to={`/story/${a.slug}/`}>Read story <span aria-hidden="true">↗</span></Link></div>
  </div>
  <div className="carousel-bottom"><div className="slide-indicators" aria-label="Choose headline">{stories.map((story,i)=><button key={story.id} aria-label={`Go to headline ${i+1}`} aria-current={i===active?'true':undefined} onClick={()=>go(i)}><span aria-hidden="true"/></button>)}</div><small className="playback-note">{playing?'Stories switch automatically':'Automatic sliding paused'}</small><div className="controls"><button aria-label="Previous headline" disabled={count<2} onClick={()=>go(active-1)}>←</button><button aria-label={playing?'Pause slider':'Play slider'} aria-pressed={playing} disabled={count<2} onClick={()=>setPlaying(v=>!v)}>{playing?'Pause':'Play'}</button><button aria-label="Next headline" disabled={count<2} onClick={()=>go(active+1)}>→</button></div></div>
 </section>
}
