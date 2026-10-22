import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import Carousel from '../components/Carousel';
import StoryCard,{StoryImage,StoryMeta} from '../components/StoryCard';
import {previewArticles,previewCategories} from './data';
import {read,save} from '../services/preferences';
export function PreviewHome({onAPI,reason}){
 const [category,setCategory]=useState(''),[limit,setLimit]=useState(4);
 const latest=previewArticles.slice(10).filter(a=>!category||a.category.slug===category);
 useEffect(()=>setLimit(4),[category]);
 return <><aside className="preview-notice"><div><strong>LOCAL DESIGN PREVIEW</strong><p>{reason} Illustrative stories and generated artwork — not live reporting. Search and main navigation still browse API content.</p></div><button onClick={onAPI}>View API content ↗</button></aside>
 <Carousel articles={previewArticles.slice(0,5)}/>
 <nav className="category-filters" aria-label="Filter local preview stories"><button aria-pressed={!category} onClick={()=>setCategory('')}>All perspectives</button>{previewCategories.map(c=><button key={c.id} aria-pressed={category===c.slug} onClick={()=>setCategory(c.slug)}>{c.name}</button>)}</nav>
 <section className="featured" aria-label="Editor's picks"><div className="section-head"><div><span className="eyebrow">THE BIGGER PICTURE · LOCAL PREVIEW</span><h2>Editor's picks</h2></div><span className="muted">Ideas worth a closer look.</span></div><div className="featured-grid">{previewArticles.slice(5,10).map((a,i)=><StoryCard key={a.id} article={a} large={i===0} summary/>)}</div></section>
 <section className="latest"><div className="section-head"><div><span className="eyebrow">THE LATEST CHAPTER · LOCAL PREVIEW</span><h2>Latest news</h2></div><span className="muted">Fresh ideas. Wider horizons.</span></div><div className="news-grid">{latest.slice(0,limit).map(a=><StoryCard key={a.id} article={a}/>)}</div>{!latest.length&&<p className="notice">No preview stories in this category. <Link to={`/category/${category}/`}>Browse API stories ↗</Link></p>}{limit<latest.length&&<div className="load-more"><button onClick={()=>setLimit(n=>n+4)}>Load more preview stories ↓</button></div>}</section></>
}
export function PreviewStory({article:a}){
 const [saved,setSaved]=useState(()=>read('nexusup-saved-'+a.slug,'0')==='1'),[note,setNote]=useState('');
 return <article className="article-detail"><p className="notice"><strong>Local design preview — not live reporting.</strong> This fixture and its AI-generated image are separate from the API and editorial database. <Link to="/stories/">Browse API stories ↗</Link></p><span className="category">{a.category.name}</span><h1>{a.title}</h1><p className="lead">{a.excerpt}</p><StoryMeta article={a}/><div className="article-actions"><button aria-pressed={saved} onClick={()=>{if(save('nexusup-saved-'+a.slug,saved?'0':'1'))setSaved(!saved);else setNote('Browser storage is unavailable.')}}>{saved?'Saved ✓':'Save story'}</button><button onClick={async()=>{try{await navigator.clipboard.writeText(location.href);setNote('Link copied')}catch{setNote('Copy the address from your browser to share this preview.')}}}>Copy link</button><span role="status">{note}</span></div><StoryImage article={a} eager/><small className="muted">{a.image_credit}</small><div className="article-body">{a.body.split('\n\n').map((p,i)=><p key={i}>{p}</p>)}</div><Link className="read-story" to="/">Back to the homepage ↗</Link></article>
}
