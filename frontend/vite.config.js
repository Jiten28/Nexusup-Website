import {defineConfig} from 'vite';
// Development proxy: forwards /api, /media, /feed and /sitemap.xml to Django.
// It presents every request to Django as coming from Django's own address, so the site also works when you
// open it from a phone or another PC (http://192.168.x.x:5173) with no extra .env settings.
// (Production does not use this file: the web server routes these paths to Django.)
const target=process.env.DEV_BACKEND_URL || 'http://127.0.0.1:8000';
const rule={target,changeOrigin:true,configure:proxy=>proxy.on('proxyReq',req=>{
  req.setHeader('origin',target);
  if(req.getHeader('referer'))req.setHeader('referer',target+'/');
})};
export default defineConfig({
  server:{host:true,proxy:{'/api':rule,'/media':rule,'/feed':rule,'/sitemap.xml':rule}},
  build:{outDir:'dist'},
});
