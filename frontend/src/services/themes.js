import {read,save} from './preferences.js';
// Six bold palettes. Each has its own light and dark surfaces, and a second "spark" colour
// (--accent-2) used for gradients. Picking a palette never changes the colour mode.
const tokens=(bg,surface,text,muted,line,accent,soft,ink,accent2)=>({'--bg':bg,'--surface':surface,'--text':text,'--muted':muted,'--line':line,'--accent':accent,'--accent-soft':soft,'--on-accent':ink,'--accent-2':accent2});
export const themes=[
 {id:'royal-indigo',name:'Royal Indigo',
  light:tokens('#f1f2fb','#ffffff','#14173a','#464b78','#c3c8ea','#3733c9','#e4e6fb','#ffffff','#ff5a5f'),
  dark:tokens('#0c0f2e','#151943','#f0f1ff','#b6bbf0','#3a4090','#98a3ff','#232a68','#0c0f2e','#ff8a8e')},
 {id:'crimson-ember',name:'Crimson Ember',
  light:tokens('#fbf1f0','#ffffff','#26141a','#68474f','#e0b8be','#b8152c','#fbe1e4','#ffffff','#f59e0b'),
  dark:tokens('#170c0f','#25131a','#fff1f2','#e4bbc2','#6b3440','#ff8494','#3e1c25','#170c0f','#ffc15e')},
 {id:'teal-wave',name:'Teal Wave',
  light:tokens('#ecf7f7','#ffffff','#0a2a2d','#3a6065','#add6d8','#05707a','#d5eff0','#ffffff','#ff7a45'),
  dark:tokens('#061b1e','#0d292d','#e9fbfb','#a6d2d5','#2b5d62','#45e3d3','#12403f','#052123','#ff9d72')},
 {id:'forest-lime',name:'Forest Lime',
  light:tokens('#eff7ea','#ffffff','#13270e','#43603a','#b5d3a8','#2b7516','#dcf0d0','#ffffff','#c99700'),
  dark:tokens('#0d190a','#15250e','#eefce8','#b5d5aa','#3a5c2e','#92e460','#25401a','#0d190a','#e8c43a')},
 {id:'amber-sunrise',name:'Amber Sunrise',
  light:tokens('#fff4e4','#ffffff','#2c1b05','#6f5128','#e4c898','#a94d05','#fde4bd','#ffffff','#7c3aed'),
  dark:tokens('#1b1104','#2a1c08','#fff4e0','#e5cb9c','#6b4c1c','#ffbb52','#4a3210','#1b1104','#c4a1ff')},
 {id:'rose-magenta',name:'Rose Magenta',
  light:tokens('#fdeff6','#ffffff','#29101f','#6c3a57','#e3b5d0','#a8106a','#fadaea','#ffffff','#0e9a9a'),
  dark:tokens('#1a0914','#2a111f','#ffeef7','#eab9d5','#6e2f55','#ff7ac4','#4a1c37','#1a0914','#4fe0e0')},
];
// Old palette ids (earlier releases) map onto the new set so saved choices keep working.
const aliases={'midnight-coral':'crimson-ember','ocean-editorial':'teal-wave','violet-night':'royal-indigo','emerald-press':'forest-lime','sunset-journal':'amber-sunrise','graphite-gold':'amber-sunrise',ocean:'teal-wave',violet:'royal-indigo',emerald:'forest-lime',sunset:'amber-sunrise'};
export const MODES=['light','dark','auto'];
export function resolveTheme(id){return themes.find(t=>t.id===(aliases[id]||id))||themes[0]}
export function resolveMode(mode,prefersDark){return mode==='dark'||(mode==='auto'&&prefersDark)?'dark':'light'}
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
