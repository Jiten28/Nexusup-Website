import {read,save} from './preferences.js';
// Six bold palettes. Each has its own light and dark surfaces, and a second "spark" colour
// (--accent-2) used for gradients. Picking a palette never changes the colour mode.
const tokens=(bg,surface,text,muted,line,accent,soft,ink,accent2)=>({'--bg':bg,'--surface':surface,'--text':text,'--muted':muted,'--line':line,'--accent':accent,'--accent-soft':soft,'--on-accent':ink,'--accent-2':accent2});
// Gradients are tonal: --accent-2 is a close neighbour of --accent, so buttons and bars shade
// smoothly instead of clashing two colours.
export const themes=[
 {id:'graphite-silver',name:'Graphite Silver',
  light:tokens('#f2f3f6','#ffffff','#14181f','#505866','#cdd1da','#2f3b52','#e3e7ef','#ffffff','#55658a'),
  dark:tokens('#0d0f13','#171a21','#f1f3f7','#b4bac6','#343a47','#c1cde6','#262c3a','#0d0f13','#8fa0c4')},
 {id:'emerald-imperial',name:'Emerald Imperial',
  light:tokens('#eef7f2','#ffffff','#0a2a1f','#3b6554','#b3d6c4','#0b6b4c','#d6efe3','#ffffff','#12875f'),
  dark:tokens('#04150f','#0b2419','#e8fbf2','#a8d6c0','#245b45','#5be0a8','#123a2a','#04150f','#3fc48c')},
 {id:'ruby-velvet',name:'Ruby Velvet',
  light:tokens('#fcf0f2','#ffffff','#2b0d17','#6e3a48','#e6b9c4','#a3123a','#fadde4','#ffffff','#c4204f'),
  dark:tokens('#1a060d','#2a0e18','#fff0f3','#e9b9c5','#6d2a3f','#ff8fa8','#431927','#1a060d','#ff6f93')},
 {id:'amethyst-noir',name:'Amethyst Noir',
  light:tokens('#f4effc','#ffffff','#1f0e3d','#5d4687','#cdb9ee','#5b21b6','#e8dcfa','#ffffff','#7c3aed'),
  dark:tokens('#0f0720','#1b0f38','#f6efff','#cbb9ee','#432a7a','#c3a1ff','#2d1a58','#0f0720','#a07bff')},
 {id:'arctic-aurora',name:'Arctic Aurora',
  light:tokens('#ebf6f9','#ffffff','#08283a','#3a6577','#aed3df','#0a6e8f','#d3ecf3','#ffffff','#0e8fb3'),
  dark:tokens('#041923','#0a2a39','#e8f9ff','#a7d3e2','#1f5870','#6fe3ff','#0f3d52','#041923','#46c8ea')},
 {id:'copper-sunset',name:'Copper Sunset',
  light:tokens('#fcf3ea','#ffffff','#2e1708','#74502f','#e5c7a6','#a8420b','#fbe3cc','#ffffff','#cf6a22'),
  dark:tokens('#190d05','#2a170a','#fff3e6','#e7cba9','#6a3f1c','#ffb06b','#47270f','#190d05','#ff9a4d')},
 {id:'midnight-rose',name:'Midnight Rose',
  light:tokens('#fdf0f4','#ffffff','#2a0f1a','#6b3b4c','#e8bccb','#b0124f','#fbdce7','#ffffff','#d6336c'),
  dark:tokens('#1a0911','#2a1019','#fff0f5','#eab9ca','#6e2c46','#ff7aa8','#44182a','#1a0911','#ff5c93')},
 {id:'ocean-navy',name:'Ocean Navy',
  light:tokens('#eef3fb','#ffffff','#0c1a38','#44557c','#bccaea','#1e40af','#dbe5fa','#ffffff','#2563eb'),
  dark:tokens('#060e22','#0f1c3d','#eef3ff','#b3c1ea','#2a3d7a','#8fb0ff','#1a2a62','#060e22','#5b8cff')},
];
// Old palette ids (earlier releases) map onto the new set so saved choices keep working.
const aliases={'sapphire-gold':'graphite-silver','royal-indigo':'ocean-navy','crimson-ember':'ruby-velvet','teal-wave':'arctic-aurora','forest-lime':'emerald-imperial','amber-sunrise':'copper-sunset','rose-magenta':'midnight-rose','midnight-coral':'ruby-velvet','ocean-editorial':'arctic-aurora','violet-night':'amethyst-noir','emerald-press':'emerald-imperial','sunset-journal':'copper-sunset','graphite-gold':'graphite-silver',ocean:'arctic-aurora',violet:'amethyst-noir',emerald:'emerald-imperial',sunset:'copper-sunset'};
export const MODES=['light','dark','auto'];
export function resolveTheme(id){return themes.find(t=>t.id===(aliases[id]||id))||themes[0]}
export function resolveMode(mode,prefersDark){return mode==='dark'||(mode==='auto'&&prefersDark)?'dark':'light'}
// One click = next palette, in a fixed order (wraps around).
export function cycleTheme(current){const i=themes.findIndex(t=>t.id===resolveTheme(current).id);return themes[(i+1)%themes.length].id}
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
// mode: 'light' | 'dark' | 'auto' (follow the device). dataset.mode keeps the user's choice.
export function applyTheme(id,mode){
 const root=document.documentElement,theme=resolveTheme(id);
 const prefersDark=typeof matchMedia==='function'&&matchMedia('(prefers-color-scheme: dark)').matches;
 const actual=resolveMode(mode,prefersDark);
 root.dataset.palette=theme.id;root.dataset.theme=actual;root.dataset.mode=mode;
 for(const [key,value] of Object.entries(theme[actual]))root.style.setProperty(key,value);
 root.style.colorScheme=actual;
}
