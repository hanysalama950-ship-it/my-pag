"""Read-only, loopback-only dashboard server. No source credentials or writes."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]/'site'
ALLOWED={'index.html':'text/html; charset=utf-8','style.css':'text/css; charset=utf-8','app.js':'application/javascript; charset=utf-8','slack-ui.js':'application/javascript; charset=utf-8','local-sync.js':'application/javascript; charset=utf-8','data.js':'application/javascript; charset=utf-8','data.json':'application/json; charset=utf-8'}
ALLOWED['local-entries.js']='application/javascript; charset=utf-8'
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get('Host') not in ('127.0.0.1:8765','localhost:8765'):
            self.send_error(403); return
        # Other websites must not embed data.js to read the private local snapshot.
        origin=self.headers.get('Origin')
        if origin and origin not in ('http://127.0.0.1:8765','http://localhost:8765'):
            self.send_error(403); return
        if self.headers.get('Sec-Fetch-Site')=='cross-site' and self.headers.get('Sec-Fetch-Mode')!='navigate':
            self.send_error(403); return
        name=urlsplit(self.path).path.lstrip('/') or 'index.html'
        if name=='health':
            body=b'{"app":"ceo-followup-local","ok":true}'
            mime='application/json'
        elif name in ALLOWED:
            try: body=(ROOT/name).read_bytes()
            except FileNotFoundError: self.send_error(404); return
            mime=ALLOWED[name]
        else: self.send_error(404); return
        self.send_response(200)
        self.send_header('Content-Type',mime)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cross-Origin-Resource-Policy','same-origin')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass
if __name__=='__main__':
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
