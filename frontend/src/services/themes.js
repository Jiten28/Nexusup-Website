import {read,save} from './preferences.js';
// Every palette has separate light/dark surfaces. Palette changes never change mode.
const palette=(id,name,light,dark)=>({id,name,light,dark});
const tokens=(bg,surface,text,muted,line,accent,soft,ink)=>({'--bg':bg,'--surface':surface,'--text':text,'--muted':muted,'--line':line,'--accent':accent,'--accent-soft':soft,'--on-accent':ink});
export const themes=[
 palette('midnight-coral','Midnight Coral',tokens('#faf4f1','#fffcfa','#29242d','#6d555d','#b59b9f','#ad3434','#f9e4df','#ffffff'),tokens('#171d29','#222b3b','#f8efeb','#c7b8bc','#758296','#ffaaa0','#3c303d','#211b24')),
 palette('ocean-editorial','Ocean Editorial',tokens('#f0f6f7','#fbfefe','#172f3c','#486571','#97b0b9','#126078','#deeff3','#ffffff'),tokens('#101f2b','#192c3a','#edf7fa','#afc7d3','#6f8b9c','#84d8ee','#203e50','#102730')),
 palette('violet-night','Violet Night',tokens('#f5f2fa','#fefcff','#2d2442','#66567e','#b2a0c4','#713ba5','#eee3f8','#ffffff'),tokens('#201a2c','#2c243b','#f6efff','#c8b8de','#8a7b9e','#d0acff','#403054','#271c39')),
 palette('emerald-press','Emerald Press',tokens('#f0f6f1','#fbfefb','#1e342c','#4d695d','#97b0a0','#15664c','#dfefe5','#ffffff'),tokens('#14251f','#1d332a','#eff9f1','#afcdbb','#719780','#88dfb1','#284938','#102d20')),
 palette('sunset-journal','Sunset Journal',tokens('#fcf4eb','#fffdf8','#3c2b22','#765d48','#bfa48c','#a64320','#fae5d2','#ffffff'),tokens('#2b201d','#392b24','#fff3e7','#d6bcaa','#a08673','#ffb080','#51372a','#362013')),
 palette('graphite-gold','Graphite Gold',tokens('#f6f5f0','#fefdf9','#30302c','#666455','#aeaa94','#80600b','#f2e9c9','#ffffff'),tokens('#20211f','#2c2d29','#f6f4e8','#c4c3b1','#8a8c78','#e7c86c','#45412b','#29250f')),
];
const aliases={ocean:'ocean-editorial',violet:'violet-night',emerald:'emerald-press',sunset:'sunset-journal'};
export function resolveTheme(id){return themes.find(t=>t.id===(aliases[id]||id))||themes[0]}
export function shuffleCycle(current,random=Math.random){
 const ids=themes.map(t=>t.id);
 for(let i=ids.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[ids[i],ids[j]]=[ids[j],ids[i]]}
 if(ids[0]===current)[ids[0],ids[1]]=[ids[1],ids[0]];
 return ids;
}
export function advanceTheme(current,remaining=[],random=Math.random){
 let bag=[...remaining];
 if(!bag.length||new Set(bag).size!==bag.length||bag.some(id=>!themes.some(t=>t.id===id)))bag=shuffleCycle(current,random);
 return {id:bag[0],remaining:bag.slice(1)};
}
export function nextTheme(current){
 let stored;try{stored=JSON.parse(read('nexusup-theme-cycle','null'))}catch{}
 const next=advanceTheme(current,stored?.current===current&&Array.isArray(stored.remaining)?stored.remaining:[]);
 save('nexusup-theme-cycle',JSON.stringify({current:next.id,remaining:next.remaining}));return next.id;
}
export function applyTheme(id,mode){const root=document.documentElement;const theme=resolveTheme(id);root.dataset.palette=theme.id;root.dataset.theme=mode;for(const [key,value]of Object.entries(theme[mode==='dark'?'dark':'light']))root.style.setProperty(key,value);root.style.colorScheme=mode==='dark'?'dark':'light'}
