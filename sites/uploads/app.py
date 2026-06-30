#!/usr/bin/env python3
"""Minimal single-user file uploader for uploads.itproxima.com.

Auth is handled upstream by Cloudflare Access (email OTP) — this app is only
ever reached after Access has verified the owner, so it has no login of its own.

  GET  /            -> upload page (drag-drop / picker) + listing
  GET  /list        -> JSON listing of stored files
  PUT  /up/<name>   -> stream request body to /srv/uploads/<safe-name>
  GET  /files/<name>-> download a stored file
  GET  /healthz     -> "ok"
"""
import json, os, re, html, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = "/srv/uploads"
os.makedirs(ROOT, exist_ok=True)

def safe_name(name):
    name = urllib.parse.unquote(name).replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9._ ()\-]", "_", name).strip().strip(".")
    return name or "unnamed"

def unique_path(name):
    name = safe_name(name)
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
        return path, name
    stem, ext = os.path.splitext(name)
    i = 1
    while True:
        cand = f"{stem} ({i}){ext}"
        p = os.path.join(ROOT, cand)
        if not os.path.exists(p):
            return p, cand
        i += 1

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>Uploads &middot; itproxima</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
 body{font-family:system-ui,sans-serif;background:#0b141a;color:#e9edef;margin:0;padding:28px;max-width:760px;margin:auto}
 h1{font-size:20px} #drop{border:2px dashed #2a3942;border-radius:14px;padding:38px;text-align:center;color:#8696a0;cursor:pointer;transition:.15s}
 #drop.hot{border-color:#25d366;color:#25d366;background:#10231b}
 .row{display:flex;justify-content:space-between;padding:8px 10px;border-bottom:1px solid #1f2c33;font-size:14px}
 a{color:#53bdeb;text-decoration:none} .prog{color:#8696a0;font-size:13px;margin-top:10px;white-space:pre-line}
 input[type=file]{display:none}
</style></head><body>
<h1>Upload to the server</h1>
<div id="drop">Drag files here, or click to choose. Any size, any format.</div>
<input id="f" type="file" multiple>
<div class="prog" id="prog"></div>
<h3>On the server</h3>
<div id="list">loading…</div>
<script>
const drop=document.getElementById('drop'),f=document.getElementById('f'),prog=document.getElementById('prog');
drop.onclick=()=>f.click();
['dragover','dragenter'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.add('hot');}));
['dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.remove('hot');}));
drop.addEventListener('drop',ev=>upload([...ev.dataTransfer.files]));
f.addEventListener('change',()=>upload([...f.files]));
function upload(files){let i=0;(function next(){if(i>=files.length){prog.textContent+='\\nDone.';refresh();return;}
 const file=files[i++];prog.textContent+='\\nUploading '+file.name+' …';
 fetch('/up/'+encodeURIComponent(file.name),{method:'PUT',body:file})
  .then(r=>r.json()).then(j=>{prog.textContent+=' saved as '+j.name;next();})
  .catch(e=>{prog.textContent+=' FAILED '+e;next();});})();}
function refresh(){fetch('/list').then(r=>r.json()).then(j=>{
 document.getElementById('list').innerHTML = j.length? j.map(x=>
  '<div class="row"><a href="/files/'+encodeURIComponent(x.name)+'">'+x.name+'</a><span>'+x.size+'</span></div>').join('')
  : '<div class="prog">empty</div>';});}
refresh();
</script></body></html>"""

def human(n):
    for u in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.0f}{u}" if u=="B" else f"{n:.1f}{u}"
        n/=1024
    return f"{n:.1f}PB"

class H(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", ctype="text/plain", extra=None):
        if isinstance(body, str): body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if path == "/healthz":
            return self._send(200, "ok\n")
        if path == "/list":
            items = []
            for n in sorted(os.listdir(ROOT)):
                p = os.path.join(ROOT, n)
                if os.path.isfile(p): items.append({"name": n, "size": human(os.path.getsize(p))})
            return self._send(200, json.dumps(items), "application/json")
        if path.startswith("/files/"):
            name = safe_name(path[len("/files/"):])
            p = os.path.join(ROOT, name)
            if not os.path.isfile(p): return self._send(404, "not found\n")
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(os.path.getsize(p)))
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.end_headers()
            with open(p, "rb") as fh:
                while True:
                    chunk = fh.read(1 << 20)
                    if not chunk: break
                    self.wfile.write(chunk)
            return
        return self._send(404, "not found\n")

    def do_PUT(self):
        path = urllib.parse.urlparse(self.path).path
        if not path.startswith("/up/"):
            return self._send(404, "not found\n")
        p, name = unique_path(path[len("/up/"):])
        remaining = int(self.headers.get("Content-Length", 0))
        with open(p, "wb") as fh:
            while remaining > 0:
                chunk = self.rfile.read(min(1 << 20, remaining))
                if not chunk: break
                fh.write(chunk); remaining -= len(chunk)
        return self._send(200, json.dumps({"name": name}), "application/json")

    def log_message(self, *a): pass

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
