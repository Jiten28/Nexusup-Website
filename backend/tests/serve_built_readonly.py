"""Local GET-only React build/reverse-proxy verification. Not Nginx/TLS or production."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit, unquote
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
if not (ROOT / 'index.html').is_file():
    raise SystemExit('Run npm run build in frontend first.')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path.startswith(('/api/','/admin/','/health/','/media/','/wp-content/uploads/','/static/','/feed/')) or path in ('/sitemap.xml','/robots.txt','/ads.txt'):
            headers={k:v for k,v in self.headers.items() if k.lower() in ('host','accept','cookie','origin')}
            try:
                response=urlopen(Request('http://127.0.0.1:8000'+self.path,headers=headers),timeout=15)
            except HTTPError as error:
                response=error
            with response:
                body=response.read()
                self.send_response(response.status)
                for key,value in response.headers.items():
                    if key.lower() not in ('connection','transfer-encoding','content-length'):
                        self.send_header(key,value)
                self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        else:
            candidate=(ROOT / unquote(path).lstrip('/')).resolve()
            if not candidate.is_relative_to(ROOT):
                self.send_error(404);return
            # Only known React routes receive the SPA entry point.
            spa=path in ('/','/stories','/stories/','/search','/search/','/about','/about/','/privacy','/privacy/','/terms','/terms/','/sources','/sources/','/contact','/contact/') or path.startswith(('/story/','/category/'))
            if not candidate.is_file() and spa:
                self.path='/index.html'
            super().do_GET()
    def do_POST(self):
        self.send_error(405,'Verification server is GET-only')

print('Local built verification proxy on http://127.0.0.1:8088',flush=True)
ThreadingHTTPServer(('127.0.0.1',8088),Handler).serve_forever()
