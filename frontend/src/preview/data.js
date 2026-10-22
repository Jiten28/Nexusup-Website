// Opt-in frontend-only fixtures. Never written to Django, never represented as reporting.
export const previewEnabled=import.meta.env?.MODE==='demo';
export const previewCategories=[['india','India'],['technology','Technology'],['science','Science'],['world','World'],['business','Business'],['cricket','Cricket']].map(([slug,name],i)=>({id:`preview-category-${i}`,slug,name}));
const entries=[
 ['india','city','The next chapter of the connected city','A closer look at the ideas shaping more human, more connected urban spaces.'],
 ['technology','chip','Inside the small chips powering big ideas','From the lab bench to everyday life, a visual exploration of the tools behind our digital world.'],
 ['science','observatory','A wider window on the universe','An invitation to look up, ask bigger questions and rediscover the wonder of the night sky.'],
 ['world','mangrove','Where the coastline comes to life','Exploring the quiet beauty of mangrove forests and the communities connected to them.'],
 ['business','solar','A new perspective on everyday energy','The people, places and possibilities behind a changing energy landscape.'],
 ['science','mangrove','The living landscape at the water’s edge','A visual essay on the delicate relationship between land, water and the life between them.'],
 ['technology','chip','Designing technology around people','Why the most thoughtful innovations begin with the everyday experiences they hope to improve.'],
 ['cricket','cricket','Before the first ball, a world of possibility','The rituals, spaces and shared anticipation that make a cricket ground more than a field.'],
 ['india','city','Making room for a slower, better commute','Reimagining the journey through the city, one thoughtful connection at a time.'],
 ['business','solar','The long view: building for tomorrow','A considered look at the infrastructure, investment and ideas that shape our shared future.'],
 ['world','city','What makes a city feel like home?','Public spaces, familiar routes and the small connections that bring a neighbourhood together.'],
 ['science','observatory','Curiosity does not stop at the horizon','The enduring appeal of discovery, from a familiar question to a new way of seeing.'],
 ['technology','chip','Small details. Extraordinary possibilities.','An illustrated journey into the precision and patient craft behind modern computing.'],
 ['cricket','cricket','The ground that brings us together','A moment to appreciate the places where sporting memories begin.'],
 ['world','mangrove','A quieter kind of natural wonder','Taking a closer look at the intricate patterns of a thriving coastal ecosystem.'],
 ['business','solar','From bright ideas to lasting change','Why the transition from a promising concept to everyday infrastructure deserves attention.'],
 ['india','city','A different way to see the city','Looking beyond the skyline to the green spaces and journeys that shape urban life.'],
 ['science','observatory','The art of asking a better question','An editorial reflection on observation, imagination and the patient work of exploration.'],
];
export const previewArticles=entries.map(([category,image,title,excerpt],i)=>({id:`local-preview-${i+1}`,slug:`local-preview-${i+1}`,title,excerpt,category:previewCategories.find(c=>c.slug===category),image:`/preview/${image}.webp`,image_alt:`AI-generated editorial illustration: ${image}`,image_credit:'AI-generated illustration for this local design preview; not documentary photography.',is_preview:true,is_sample:true,reading_minutes:2,date:null,source_name:'NexusUp · Local design preview',body:`${excerpt}\n\nThis is an illustrative local fixture created to demonstrate NexusUp’s layout, typography and navigation. It is not a verified news report and does not describe a specific current event.\n\nThe image is AI-generated editorial artwork, not a photograph of an actual event. The preview is stored only in the frontend; it is never imported into the editorial database.`,comments:[],tags:[]}));
export function uniqueStories(articles=[]){return [...new Map(articles.filter(a=>a?.id!=null&&a.slug).map(a=>[a.id,a])).values()]}
export function needsPreview(data){return uniqueStories(data?.carousel).filter(a=>a.image).length<3}
export function sanitizeHome(data){const carousel=uniqueStories(data?.carousel).slice(0,5),ids=new Set(carousel.map(a=>a.id)),featured=uniqueStories(data?.featured).filter(a=>!ids.has(a.id)).slice(0,5);return {carousel,featured,excluded:[...carousel,...featured].map(a=>a.id)}}
