import React,{useState,useEffect,useRef} from 'react';
import {Link} from 'react-router-dom';
import {StoryImage} from './StoryCard';
export default function Carousel({articles=[]}){
 const ref=useRef(null),[playing,setPlaying]=useState(false),[hovered,setHovered]=useState(false),[focused,setFocused]=useState(false);
 const [reduced,setReduced]=useState(()=>matchMedia('(prefers-reduced-motion: reduce)').matches);
 useEffect(()=>{const m=matchMedia('(prefers-reduced-motion: reduce)'),cb=()=>setReduced(m.matches);m.addEventListener('change',cb);return()=>m.removeEventListener('change',cb)},[]);
 function move(direction){const el=ref.current;if(!el)return;const end=el.scrollWidth-el.clientWidth;const next=direction>0&&el.scrollLeft>=end-3?0:direction<0&&el.scrollLeft<=3?end:el.scrollLeft+direction*(el.querySelector('article')?.offsetWidth+16||300);el.scrollTo({left:next,behavior:reduced?'instant':'smooth'});}
 useEffect(()=>{if(!playing||hovered||focused||reduced)return;const timer=setInterval(()=>{if(!document.hidden)move(1)},6000);return()=>clearInterval(timer)},[playing,hovered,focused,reduced,articles.length]);
 if(!articles.length)return null;
 return <section className="carousel" aria-label="Featured headlines" onMouseEnter={()=>setHovered(true)} onMouseLeave={()=>setHovered(false)} onFocus={()=>setFocused(true)} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget))setFocused(false)}}>
  <div className="section-head"><div><span className="eyebrow">IN THE SPOTLIGHT</span><h2>Headlines, in focus</h2></div><div className="controls"><button aria-label="Previous headlines" onClick={()=>move(-1)}>←</button><button aria-label={playing?'Pause carousel':'Play carousel'} disabled={reduced||articles.length<2} onClick={()=>setPlaying(!playing)}>{playing?'Pause':'Play'}</button><button aria-label="Next headlines" onClick={()=>move(1)}>→</button></div></div>
  <div className="carousel-track" ref={ref}>{articles.map(a=><article key={a.id}><Link to={`/story/${a.slug}/`}><StoryImage article={a}/><div className="carousel-copy"><span className="category">{a.category.name}</span><h3>{a.title}</h3><small>{a.is_sample?'Sample story':a.source_name}</small></div></Link></article>)}</div>
 </section>
}
