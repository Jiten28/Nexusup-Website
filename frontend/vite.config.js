import {defineConfig} from 'vite';
// Development-only proxy. Preserve Host so Django can verify same-origin CSRF.
const target=process.env.DEV_BACKEND_URL || 'http://127.0.0.1:8000';
export default defineConfig({server:{proxy:{'/api':{target,changeOrigin:false},'/media':{target,changeOrigin:false}}},build:{outDir:'dist'}});
