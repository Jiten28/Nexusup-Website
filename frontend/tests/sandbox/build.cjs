// SANDBOX-ONLY: bundle the real src/ with esbuild (+ router shim) into dist-sandbox/ and serve it with SPA fallback.
// Usage: ESBUILD_DIR=/opt/npm-tools/node_modules node tests/sandbox/build.cjs [--serve 4173]
const path = require('path'), fs = require('fs'), http = require('http');
const root = path.resolve(__dirname, '../..'), out = path.join(root, 'dist-sandbox');
const modules = process.env.ESBUILD_DIR || path.join(root, 'node_modules');
const esbuild = require(path.join(modules, 'esbuild'));
async function build() {
  fs.rmSync(out, {recursive: true, force: true}); fs.mkdirSync(out, {recursive: true});
  await esbuild.build({entryPoints: [path.join(root, 'src/main.jsx')], bundle: true, outfile: path.join(out, 'app.js'), format: 'esm', jsx: 'transform', loader: {'.js': 'jsx', '.css': 'css'},
    nodePaths: [modules], alias: {'react-router-dom': path.join(__dirname, 'router-shim.jsx')}, minify: false, logLevel: 'error',
    define: {'import.meta.env': JSON.stringify({MODE: 'production', PROD: true, DEV: false, VITE_API_BASE_URL: ''}), 'process.env.NODE_ENV': '"production"'}});
  fs.cpSync(path.join(root, 'public'), out, {recursive: true});
  fs.writeFileSync(path.join(out, 'index.html'), '<!doctype html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><link rel="stylesheet" href="/app.css"/><title>NexusUp sandbox</title></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>');
}
function serve(port) {
  const types = {'.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.webp': 'image/webp', '.png': 'image/png'};
  http.createServer((req, res) => { const p = decodeURIComponent(req.url.split('?')[0]), f = path.join(out, p); const file = fs.existsSync(f) && fs.statSync(f).isFile() ? f : path.join(out, 'index.html');
    res.writeHead(200, {'Content-Type': types[path.extname(file)] || 'application/octet-stream'}); fs.createReadStream(file).pipe(res); }).listen(port, '127.0.0.1', () => console.log('sandbox server http://127.0.0.1:' + port));
}
build().then(() => { const i = process.argv.indexOf('--serve'); if (i > 0) serve(+process.argv[i + 1] || 4173); else console.log('built', out); }).catch(e => { console.error(e.message); process.exit(1); });
