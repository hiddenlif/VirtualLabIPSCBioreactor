import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer
from ipsc_lab import server
from ipsc_lab.engine import digest


class LocalApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.old_runtime=server.RUNTIME
        server.RUNTIME=Path(cls.temp.name)
        cls.http=ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f"http://127.0.0.1:{cls.http.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.thread.join()
        server.RUNTIME=cls.old_runtime;cls.temp.cleanup()

    def req(self,path,data=None,token=True,origin=None):
        headers={}
        if data is not None:
            headers["Content-Type"]="application/json"
            if token:headers["X-Lab-Token"]=server.TOKEN
        if origin:headers["Origin"]=origin
        r=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
        with urllib.request.urlopen(r,timeout=10) as response:return json.load(response)

    def create(self):return self.req("/api/session",dict(scenario="nominal",seed=17))

    def test_public_api_and_export_agree(self):
        r=self.create();key=r["id"]
        self.assertEqual(r["observation"]["time_h"],48)
        text=json.dumps(r)
        self.assertNotIn("latent_quality_decision",text)
        self.assertNotIn('"scenario"',text)
        d=self.req("/api/dossier/"+key)
        self.assertEqual(d["observation_sha256"],digest(r["observation"]))
        self.assertEqual(d["conclusion"],r["observation"]["assessment"])
        r=self.req("/api/action",dict(id=key,commands=[dict(type="sample",panel="metabolic")]))
        self.assertNotIn("values",r["observation"]["samples"][-1])
        r=self.req("/api/action",dict(id=key,advance_h=2))
        self.assertEqual(r["observation"]["samples"][-1]["status"],"complete")
        self.assertIn("values",r["observation"]["samples"][-1])

    def test_branch_and_failed_action_preserve_parent(self):
        parent=self.create();key=parent["id"]
        branch=self.req("/api/branch",dict(id=key));child=branch["id"]
        self.req("/api/action",dict(id=child,commands=[dict(type="set_perfusion",value=8)]))
        self.assertEqual(self.req("/api/session/"+key)["observation"]["settings"]["perfusion_ml_h"],3)
        self.assertEqual(self.req("/api/session/"+child)["observation"]["settings"]["perfusion_ml_h"],8)
        before=self.req("/api/session/"+child)
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.req("/api/action",dict(id=child,commands=[dict(type="repair_pump")]))
        self.assertEqual(caught.exception.code,400)
        self.assertEqual(before,self.req("/api/session/"+child))

    def test_cross_origin_and_uncredentialed_mutation_fail(self):
        for kw in (dict(token=False),dict(origin="https://unrelated.example")):
            with self.assertRaises(urllib.error.HTTPError) as caught:self.req("/api/session",dict(scenario="nominal",seed=17),**kw)
            self.assertEqual(caught.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as caught:self.req("/../config/sop.json")
        self.assertEqual(caught.exception.code,404)

    def test_malformed_commands_fail_without_state_change(self):
        r=self.create();key=r["id"]
        for commands in ({},[dict(type="set_perfusion",value=True)],[dict(type="set_perfusion",value=100)]):
            with self.assertRaises(urllib.error.HTTPError) as caught:self.req("/api/action",dict(id=key,commands=commands))
            self.assertEqual(caught.exception.code,400)
        self.assertEqual(r,self.req("/api/session/"+key))


if __name__=="__main__":unittest.main()
