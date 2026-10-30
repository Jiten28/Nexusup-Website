import React,{useState,useEffect,useContext,useRef} from 'react';
import {api,submit} from '../services/api';
import {Translation} from '../context/Translation';
import {read,save} from '../services/preferences';

const initials=name=>(name||'?').trim().split(/\s+/).slice(0,2).map(w=>w[0]).join('').toUpperCase();
function ago(iso){
 const s=Math.round((new Date(iso)-Date.now())/1000),rtf=new Intl.RelativeTimeFormat(undefined,{numeric:'auto'});
 for(const [unit,secs] of [['year',31536000],['month',2592000],['day',86400],['hour',3600],['minute',60]])if(Math.abs(s)>=secs)return rtf.format(Math.round(s/secs),unit);
 return rtf.format(0,'second');
}
// Compose box: used for new comments and for replies. Nothing is shown publicly until an editor approves it.
function Composer({slug,parent,onDone,onCancel,autoFocus}){
 const t=useContext(Translation),[name,setName]=useState(()=>read('nexusup-commenter','')),[body,setBody]=useState(''),[busy,setBusy]=useState(false),[note,setNote]=useState(''),[bad,setBad]=useState(false),ref=useRef(null);
 useEffect(()=>{if(autoFocus&&ref.current)ref.current.focus()},[autoFocus]);
 const send=async e=>{
  e.preventDefault();setBusy(true);setNote('');setBad(false);
  try{
   const d=await submit(`/api/articles/${slug}/comments/`,{name:name.trim(),body:body.trim(),...(parent?{parent}:{})});
   save('nexusup-commenter',name.trim());setBody('');setNote(t('ui:awaiting_approval',d.message));onDone&&onDone(d.message);
  }catch(err){setBad(true);setNote(err.message)}finally{setBusy(false)}
 };
 return <form className={`composer${parent?' composer-reply':''}`} onSubmit={send}>
  <span className="avatar" aria-hidden="true">{initials(name)}</span>
  <div className="composer-fields">
   <input required maxLength="80" value={name} onChange={e=>setName(e.target.value)} placeholder={t('ui:your_name','Your name')} aria-label={t('ui:your_name','Your name')}/>
   <textarea ref={ref} required maxLength="2000" rows={parent?2:3} value={body} onChange={e=>setBody(e.target.value)} placeholder={parent?t('ui:write_reply','Write a reply…'):t('ui:write_comment','Add a comment…')} aria-label={parent?t('ui:write_reply','Write a reply…'):t('ui:write_comment','Add a comment…')}/>
   <div className="composer-actions">
    <small className="muted">{body.length}/2000</small>
    {onCancel&&<button type="button" className="ghost" onClick={onCancel}>{t('ui:cancel','Cancel')}</button>}
    <button disabled={busy||!body.trim()||!name.trim()}>{busy?t('ui:sending','Sending…'):parent?t('ui:reply','Reply'):t('ui:comment','Comment')}</button>
   </div>
   {note&&<p role="status" className={bad?'composer-note bad':'composer-note'}>{note}</p>}
  </div>
 </form>
}
function Item({c,slug,isReply,topId}){
 const t=useContext(Translation),[replying,setReplying]=useState(false),[open,setOpen]=useState(false),replies=c.replies||[];
 return <li className={`comment${isReply?' comment-reply':''}`}>
  <span className={`avatar${c.is_editor?' avatar-editor':''}`} aria-hidden="true">{initials(c.name)}</span>
  <div className="comment-main">
   <p className="comment-head"><b>{c.name}</b>{c.is_editor&&<span className="badge">{t('ui:editorial_team','Editorial team')}</span>}<time dateTime={c.created_at} title={new Date(c.created_at).toLocaleString()}>{ago(c.created_at)}</time></p>
   <p className="comment-body">{c.body}</p>
   <div className="comment-actions"><button type="button" className="link" onClick={()=>setReplying(v=>!v)} aria-expanded={replying}>{t('ui:reply','Reply')}</button></div>
   {replying&&<Composer slug={slug} parent={c.id} autoFocus onCancel={()=>setReplying(false)} onDone={()=>{}}/>}
   {!isReply&&replies.length>0&&<>
    <button type="button" className="link replies-toggle" aria-expanded={open} onClick={()=>setOpen(v=>!v)}>{open?'▾ ':'▸ '}{open?t('ui:hide_replies','Hide replies'):`${replies.length} ${replies.length===1?t('ui:one_reply','reply'):t('ui:replies','replies')}`}</button>
    {open&&<ul className="comment-list replies">{replies.map(r=><Item key={r.id} c={r} slug={slug} isReply topId={c.id}/>)}</ul>}
   </>}
  </div>
 </li>
}
export default function Conversation({slug,initial=[],count=0}){
 const t=useContext(Translation),[items,setItems]=useState(initial),[total,setTotal]=useState(count),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{setItems(initial);setTotal(count)},[slug,initial,count]);
 const refresh=async()=>{setBusy(true);setError('');try{const d=await api(`/api/articles/${slug}/comments/`);setItems(d.results);setTotal(d.count)}catch(e){setError(e.message)}finally{setBusy(false)}};
 return <section className="conversation" id="conversation" aria-labelledby="conversation-title">
  <div className="conversation-head"><h2 id="conversation-title">{t('ui:conversation','Conversation')} <span className="count">{total}</span></h2><button type="button" className="ghost" onClick={refresh} disabled={busy}>{busy?'…':t('ui:refresh','Refresh')}</button></div>
  <p className="muted">{t('ui:comments_reviewed','Comments and replies appear after an editor approves them.')}</p>
  <Composer slug={slug}/>
  {error&&<p className="composer-note bad" role="alert">{error}</p>}
  {items.length===0?<p className="conversation-empty">{t('ui:no_comments','No conversation yet. Be the first to share a thought.')}</p>
   :<ul className="comment-list">{items.map(c=><Item key={c.id} c={c} slug={slug}/>)}</ul>}
 </section>
}
