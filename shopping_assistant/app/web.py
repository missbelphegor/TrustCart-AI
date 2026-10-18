"""Tiny offline standard-library web chat; no external UI framework required."""
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
import sys,json,html
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.pipeline import Assistant
bot=Assistant()
PAGE='''<!doctype html><meta charset="utf-8"><title>TrustCart</title><h1>TrustCart product assistant</h1><form method="post"><input name="q" autofocus placeholder="Ask about products or policy" style="width:65%"><button>Send</button></form>{body}'''
class Handler(BaseHTTPRequestHandler):
 def do_GET(self): self.respond('')
 def do_POST(self):
  import urllib.parse
  n=int(self.headers.get('Content-Length','0')); q=urllib.parse.parse_qs(self.rfile.read(n).decode()).get('q',[''])[0]; r=bot.chat('web',q); self.respond(f'<p><b>You:</b> {html.escape(q)}</p><p><b>Assistant:</b> {html.escape(r.text)}</p><details><summary>Debug</summary><pre>{html.escape(json.dumps(r.debug,default=str,indent=2))}</pre></details>')
 def respond(self,body):
  raw=PAGE.format(body=body).encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
if __name__=='__main__': print('Offline UI at http://127.0.0.1:7860'); HTTPServer(('127.0.0.1',7860),Handler).serve_forever()
