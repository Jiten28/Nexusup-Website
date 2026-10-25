import React,{useContext,useEffect,useState} from 'react';
import {Link,Routes,Route,useLocation,useNavigate} from 'react-router-dom';
import {api,submit,backendLink} from './services/api';
import Widgets from './components/Widgets';
import {Home,Listing,Story,Info,visibleCategories} from './pages/NewsPages';
import {Translation} from './context/Translation';
import {read,save} from './services/preferences';
import {resolveTheme,nextTheme,applyTheme} from './services/themes';
import {previewEnabled} from './preview/data';
function Header({categories}){
 const t=useContext(Translation);const [mode,setMode]=useState(()=>read('nexusup-theme',matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
 const [palette,setPalette]=useState(()=>resolveTheme(read('nexusup-palette','midnight-coral')).id),[time,setTime]=useState(new Date()),[menu,setMenu]=useState(false),[search,setSearch]=useState('');const nav=useNavigate(),loc=useLocation();
 useEffect(()=>{applyTheme(palette,mode);save('nexusup-theme',mode);save('nexusup-palette',palette)},[mode,palette]);
 useEffect(()=>{const timer=setInterval(()=>setTime(new Date()),1000);return()=>clearInterval(timer)},[]);
 useEffect(()=>{setMenu(false)},[loc.pathname]);
 return <header><div className="topline wrap"><span>{t('ui:tagline','More perspective. Less noise.')}</span><span><span id="location-name">{t('ui:local_time','Your local time')}</span> · <time>{time.toLocaleString(undefined,{weekday:'short',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}</time></span></div>
 <div className="brand-row wrap"><Link to="/" className="brand"><img src="/book.webp" alt=""/>NexusUp<span>.</span></Link><div className="header-tools"><button aria-label="Toggle light and dark mode" onClick={()=>setMode(mode==='dark'?'light':'dark')}>{mode==='dark'?t('ui:light_mode','Light mode'):t('ui:dark_mode','Dark mode')}</button><div className="theme-switch"><button aria-describedby="theme-name" onClick={()=>setPalette(current=>nextTheme(current))}><span className="theme-dot" aria-hidden="true"/>{t('ui:color_theme','Color Theme')}</button><small id="theme-name" aria-live="polite">{resolveTheme(palette).name}</small></div><Widgets/></div></div>
 <div className="nav-border"><div className="wrap nav-row"><button className="mobile-toggle" aria-expanded={menu} onClick={()=>setMenu(!menu)} onKeyDown={e=>{if(e.key==='Escape')setMenu(false)}}>{t('ui:menu','Menu')}</button><nav className={menu?'open':''} aria-label="Main navigation"><Link to="/">{t('ui:home','Home')}</Link><Link to="/stories/">{t('ui:blogs','All stories')}</Link>{visibleCategories(categories).map(c=><Link key={c.id} to={`/category/${c.slug}/`}>{t(`category:${c.id}`,c.name)}</Link>)}</nav><form className="search" role="search" onSubmit={e=>{e.preventDefault();nav(`/search/?q=${encodeURIComponent(search)}`)}}><label className="sr-only" htmlFor="search">Search stories</label><input id="search" placeholder={t('ui:search_placeholder','Find a fresh perspective…')} value={search} maxLength="120" onChange={e=>setSearch(e.target.value)}/><button aria-label="Search">↗</button></form></div></div></header>
}
const RTL=['ar','he','fa','ur'];
function Language({setTexts}){
 const t=useContext(Translation),loc=useLocation();
 const [languages,setLanguages]=useState([]),[selected,setSelected]=useState(()=>read('nexusup-language','en')),[note,setNote]=useState(''),[busy,setBusy]=useState(false);
 const reset=()=>{setTexts({});document.documentElement.lang='en';document.documentElement.dir='ltr'};
 // The language list is loaded once on page load, so the dropdown is ready before it is opened.
 useEffect(()=>{let live=true;(async()=>{if(previewEnabled){setNote('Original English · translation is off for this demo.');return}try{const d=await api('/api/languages/');if(live)setLanguages(d.languages)}catch(e){if(live){setNote('Original English · translation is not configured on this server.');setSelected('en')}}})();return()=>{live=false}},[]);
 async function apply(language){
  if(language==='en'){reset();return}
  setBusy(true);
  try{const d=await submit('/api/translate/',{path:loc.pathname,language});setTexts(d.texts);setNote(d.notice+' Some labels and stories may remain English.');document.documentElement.lang=language;document.documentElement.dir=RTL.includes(language)?'rtl':'ltr'}
  catch(e){setNote(e.message+' Original English retained.');setSelected('en');save('nexusup-language','en');reset()}
  finally{setBusy(false)}
 }
 // Re-translate each page the reader opens; English simply clears the overrides.
 useEffect(()=>{apply(selected)},[loc.pathname]);
 const change=language=>{setSelected(language);save('nexusup-language',language);if(language==='en')setNote('Original English');apply(language)};
 return <div className="language-bar wrap"><div><span className="eyebrow">{t('ui:eyebrow','A FRESH PERSPECTIVE')}</span><p>{t('ui:curiosity','Curiosity connects us.')}</p></div><div className="language"><label htmlFor="language">{t('ui:read_in','Read in')}</label><select id="language" value={selected} disabled={busy} onChange={e=>change(e.target.value)}><option value="en">Original · English</option>{languages.filter(x=>x.code!=='en').map(x=><option key={x.code} value={x.code}>{x.name}</option>)}</select><small role="status">{busy?'Translating…':note}</small></div></div>
}
function Footer(){const t=useContext(Translation);return <footer><div className="wrap footer-grid"><div><Link className="brand" to="/">NexusUp<span>.</span></Link><p>More perspective.<br/>Less noise.</p></div><div><h2>{t('ui:footer_discover','Discover')}</h2><Link to="/stories/">{t('ui:blogs','All stories')}</Link><a href={backendLink('/feed/')}>RSS feed ↗</a><a href={backendLink('/sitemap.xml')}>Sitemap</a></div><div><h2>NexusUp</h2><Link to="/about/">{t('ui:footer_about','About NexusUp')}</Link><Link to="/contact/">{t('ui:footer_contact','Contact')}</Link><Link to="/terms/">{t('ui:footer_editorial','Editorial policy')}</Link></div><div><h2>{t('ui:footer_good','Good to know')}</h2><Link to="/privacy/">{t('ui:footer_privacy','Privacy policy')}</Link><Link to="/sources/">{t('ui:footer_sources','Sources & attribution')}</Link><p className="muted">Sample content is labeled.</p></div></div><div className="wrap footer-bottom">© {new Date().getFullYear()} NexusUp <a href="#main">Back to top ↑</a></div></footer>}
export default function App(){const [categories,setCategories]=useState([]),[texts,setTexts]=useState({}),loc=useLocation();useEffect(()=>{api('/api/categories/').then(setCategories).catch(()=>{})},[]);useEffect(()=>{window.scrollTo(0,0);document.title='NexusUp — A fresh perspective'},[loc.pathname]);return <Translation.Provider value={(k,f)=>texts[k]||f||k}><a className="skip" href="#main">Skip to content</a><Header categories={categories}/><Language setTexts={setTexts}/><main className="wrap" id="main"><Routes><Route path="/" element={<Home categories={categories}/>}/><Route path="/stories/" element={<Listing categories={categories}/>}/><Route path="/search/" element={<Listing categories={categories}/>}/><Route path="/category/:slug/" element={<Listing categories={categories}/>}/><Route path="/story/:slug/" element={<Story/>}/>{['about','privacy','terms','sources','contact'].map(type=><Route key={type} path={`/${type}/`} element={<Info type={type}/>}/>)}<Route path="*" element={<section className="prose"><h1>Page not found</h1><Link to="/">Return to NexusUp</Link></section>}/></Routes></main><Footer/></Translation.Provider>}
