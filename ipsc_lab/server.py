"""Loopback-only research app. No third-party packages, credentials or cloud services."""
import argparse
import copy
import json
import mimetypes
import secrets
import threading
import uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import Campaign,ROOT,SCENARIOS,SOP
from .policies import commands

SESSIONS={}
LOCK=threading.RLock()
TOKEN=secrets.token_urlsafe(24)
RUNTIME=ROOT/".runtime"


def save(key,c):
    RUNTIME.mkdir(exist_ok=True)
    path=RUNTIME/f"{key}.json"
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(c.__dict__,allow_nan=False))
    temp.replace(path)


def get(key):
    if key not in SESSIONS:
        if len(key)!=12 or not key.isalnum():raise ValueError("Unknown campaign")
        path=RUNTIME/f"{key}.json"
        if not path.exists():raise ValueError("Unknown campaign")
        c=Campaign.__new__(Campaign);c.__dict__.update(json.loads(path.read_text()));SESSIONS[key]=c
    return SESSIONS[key]


class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):
        pass

    def send(self,value,status=200,content_type="application/json"):
        body=json.dumps(value,allow_nan=False).encode() if content_type=="application/json" else value
        self.send_response(status)
        self.send_header("Content-Type",content_type)
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.end_headers();self.wfile.write(body)

    def do_GET(self):
        path=urlparse(self.path).path
        try:
            with LOCK:
                if path=="/api/meta":
                    return self.send(dict(token=TOKEN,sop=SOP,scenarios=[dict(id=k,title=v[0],description=v[1]) for k,v in SCENARIOS.items()]))
                if path.startswith("/api/session/"):
                    key=path.split("/")[-1];return self.send(dict(id=key,observation=get(key).observation()))
                if path.startswith("/api/dossier/"):
                    return self.send(get(path.split("/")[-1]).dossier())
                if path=="/api/comparison":
                    p=ROOT/"reports/comparison-v1/summary.json"
                    pilot=ROOT/"reports/model-pilot-v1/summary.json"
                    return self.send(dict(comparison=json.loads(p.read_text()) if p.exists() else None,
                                          pilot=json.loads(pilot.read_text()) if pilot.exists() else None))
                if path=="/api/sources":
                    return self.send(json.loads((ROOT/"docs/sources.json").read_text()))
            file=(ROOT/"web"/("index.html" if path=="/" else path.lstrip("/"))).resolve()
            if not file.is_relative_to((ROOT/"web").resolve()) or not file.is_file():
                return self.send(dict(error="Not found"),404)
            self.send(file.read_bytes(),content_type=mimetypes.guess_type(file)[0] or "application/octet-stream")
        except (ValueError,KeyError) as e:self.send(dict(error=str(e)),400)

    def do_POST(self):
        host=self.headers.get("Host","")
        origin=self.headers.get("Origin")
        if host not in (f"127.0.0.1:{self.server.server_port}",f"localhost:{self.server.server_port}") or (origin and origin not in (f"http://127.0.0.1:{self.server.server_port}",f"http://localhost:{self.server.server_port}")) or self.headers.get("X-Lab-Token")!=TOKEN:
            return self.send(dict(error="Local session token required"),403)
        try:
            size=int(self.headers.get("Content-Length","0"))
            if not 0<size<=65536:raise ValueError("Invalid request size")
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict):raise ValueError("Expected JSON object")
            with LOCK:
                if self.path=="/api/session":
                    scenario=data.get("scenario","blind")
                    if scenario=="blind":scenario=secrets.choice(list(SCENARIOS))
                    c=Campaign(scenario,data.get("seed",17))
                    # A documented warm-start of routine operation, before scientist control.
                    for _ in range(24):
                        c.action(commands(c.observation(),"fixed"),advance_h=2,rationale="Routine warm-start",actor="fixed")
                    key=uuid.uuid4().hex[:12];SESSIONS[key]=c;save(key,c)
                    return self.send(dict(id=key,observation=c.observation()),201)
                key=data.get("id");c=get(key)
                if self.path=="/api/action":
                    obs=c.action(commands=data.get("commands",[]),advance_h=data.get("advance_h",0),rationale=data.get("rationale","Scientist action"),evidence=data.get("evidence",[]),action_id=data.get("action_id"))
                    save(key,c);return self.send(dict(id=key,observation=obs))
                if self.path=="/api/supervisor":
                    if c.clock>=156:raise ValueError("Campaign closeout complete")
                    obs=c.action(commands(c.observation(),"diagnostic"),advance_h=min(2,156-c.clock),rationale="Transparent diagnostic rule policy; no model inference",actor="diagnostic")
                    save(key,c);return self.send(dict(id=key,observation=obs))
                if self.path=="/api/branch":
                    branch=copy.deepcopy(c);branch._event("branch","Campaign branched",f"Counterfactual branch at hour {c.clock:g}")
                    key2=uuid.uuid4().hex[:12];SESSIONS[key2]=branch;save(key2,branch)
                    return self.send(dict(id=key2,parent_id=key,observation=branch.observation()),201)
            return self.send(dict(error="Not found"),404)
        except (ValueError,KeyError,TypeError) as e:self.send(dict(error=str(e)),400)


def main():
    p=argparse.ArgumentParser();p.add_argument("--port",type=int,default=8840);a=p.parse_args()
    server=ThreadingHTTPServer(("127.0.0.1",a.port),Handler)
    print(f"Local: http://127.0.0.1:{server.server_port}",flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=="__main__":main()
