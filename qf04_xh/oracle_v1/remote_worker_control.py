from __future__ import annotations
import argparse, json, os, pathlib, select, shutil, socket, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = pathlib.Path("/tmp/qf04-source-v3")
HARNESS = SOURCE / "harness"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

WORKFLOWS = {
    "MFG": (pathlib.Path("/tmp/qf04-workflows/mfg/gaia-mfg-control-plane"), [sys.executable, "run_a0a_fat.py"], "WF-MFG-BOM-FAT"),
    "CONTROL": (pathlib.Path("/tmp/qf04-workflows/control"), [sys.executable, "scripts/preflight.py"], "WF-CONTROL-PREFLIGHT"),
    "STAGING": (pathlib.Path("/tmp/qf04-workflows/staging"), [sys.executable, "scripts_validate.py"], "WF-STAGING-QUAL"),
}

class Control:
    def __init__(self, root: pathlib.Path, bore: str):
        self.root=root; self.bore=bore; self.workers={}; self.tunnels={}; self.ports={}

    def stop_current(self):
        for p in self.tunnels.values():
            if p.poll() is None: p.terminate()
        for item in self.workers.values():
            p=item["process"]
            if p.poll() is None: p.terminate()
        for p in [x["process"] for x in self.workers.values()]:
            try: p.wait(timeout=2)
            except subprocess.TimeoutExpired: p.kill()
        self.tunnels={}; self.workers={}; self.ports={}

    def _tunnel(self, key: str, local_port: int) -> int:
        attempts=[]
        for attempt in range(1,5):
            p=subprocess.Popen([self.bore,"local",str(local_port),"--to","bore.pub"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env={**os.environ,"NO_COLOR":"1","RUNNER_TRACKING_ID":""})
            assert p.stdout
            deadline=time.time()+35; remote=None; lines=[]
            while time.time()<deadline:
                ready,_,_=select.select([p.stdout],[],[],1)
                if not ready:
                    if p.poll() is not None: break
                    continue
                line=p.stdout.readline()
                if not line: break
                lines.append(line.strip())
                import re
                m=re.search(r"bore\.pub:(\d+)",line)
                if m: remote=int(m.group(1)); break
            attempts.append({"attempt":attempt,"returncode":p.poll(),"lines":lines[-8:]})
            with (self.root/"tunnel_debug.jsonl").open("a") as f:
                f.write(json.dumps({"key":key,**attempts[-1]},sort_keys=True)+"\n")
            if remote is not None:
                self.tunnels[key]=p
                return remote
            if p.poll() is None: p.terminate()
            try: p.wait(timeout=3)
            except subprocess.TimeoutExpired: p.kill()
            time.sleep(2)
        raise RuntimeError(f"bore tunnel failed for {key}: {attempts}")

    def start(self, campaign: str, scenario: str):
        self.stop_current()
        scenario_root=self.root/campaign/scenario
        if scenario_root.exists(): shutil.rmtree(scenario_root)
        scenario_root.mkdir(parents=True)
        for idx,key in enumerate(("MFG","CONTROL","STAGING"),1):
            src,cmd,wfid=WORKFLOWS[key]
            wr=scenario_root/key.lower(); cwd=wr/"cwd"
            shutil.copytree(src,cwd)
            p=subprocess.Popen([sys.executable,str(HARNESS/"distributed_recovery_qf.py"),"--serve","--adapter-id",key,"--workflow-id",wfid,"--authority-ceiling","2","--bind-host","127.0.0.1","--root",str(wr),"--command-json",json.dumps(cmd)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={**os.environ,"RUNNER_TRACKING_ID":""})
            assert p.stdout
            line=p.stdout.readline()
            if not line: raise RuntimeError(p.stderr.read())
            port=int(json.loads(line)["port"])
            self.workers[key]={"process":p,"port":port,"workflow_id":wfid,"root":wr}
            self.ports[key]=self._tunnel(key,port)
        return self.info()

    def info(self):
        return {"endpoints":{k:{"host":"bore.pub","port":self.ports[k],"workflow_id":v["workflow_id"]} for k,v in self.workers.items()},"worker_vm":{"runner_name":os.getenv("RUNNER_NAME"),"hostname":socket.gethostname(),"boot_id":pathlib.Path("/proc/sys/kernel/random/boot_id").read_text().strip()}}

    def drop(self,key):
        p=self.tunnels.pop(key)
        p.terminate(); p.wait(timeout=3)
        return {"dropped":key}

    def restore(self,key):
        self.ports[key]=self._tunnel(key,self.workers[key]["port"])
        return {"restored":key,"host":"bore.pub","port":self.ports[key]}

    def crash(self, mode, tx):
        cfg=self.root/"driver.json"
        cfg.write_text(json.dumps({"composition_id":"GAIA-COMP-QF04-MFG-CONTROL-STAGING-DISTRIBUTED-RECOVERY-v0.1","coordinator_journal":str(self.root/"relocated_coordinator.jsonl"),"authority_ceiling":2,"active_version":"ORCH-QF-ACTIVE-v0.1","workers":[{"adapter_id":k,"workflow_id":v["workflow_id"],"authority_ceiling":2,"bind_host":"127.0.0.1","port":v["port"]} for k,v in self.workers.items()]},sort_keys=True))
        j=self.root/"relocated_coordinator.jsonl"
        if j.exists(): j.unlink()
        p=subprocess.run([sys.executable,str(HARNESS/"coordinator_crash_driver.py"),mode,tx,str(cfg)])
        return {"exit_code":p.returncode,"journal":j.read_text()}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--port",type=int,default=31247); ap.add_argument("--root",default="/tmp/qf04-remote"); ap.add_argument("--bore",required=True); a=ap.parse_args()
    ctl=Control(pathlib.Path(a.root),a.bore)
    s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind(("127.0.0.1",a.port)); s.listen(8)
    print(json.dumps({"ready":True,"port":a.port}),flush=True)
    running=True
    while running:
        conn,_=s.accept()
        with conn:
            data=b""
            while not data.endswith(b"\n"):
                chunk=conn.recv(65536)
                if not chunk: break
                data+=chunk
            try:
                q=json.loads(data)
                op=q["op"]
                if op=="START": out=ctl.start(q["campaign"],q["scenario"])
                elif op=="DROP": out=ctl.drop(q["worker"])
                elif op=="RESTORE": out=ctl.restore(q["worker"])
                elif op=="CRASH": out=ctl.crash(q["mode"],q["tx_id"])
                elif op=="STOP":
                    ctl.stop_current(); pathlib.Path("/tmp/qf04-worker-done").write_text("done\n"); out={"stopped":True}; running=False
                else: out={"error":"unknown op"}
            except Exception as e:
                out={"error":type(e).__name__+":"+str(e)}
            conn.sendall((json.dumps(out,sort_keys=True,separators=(",",":"))+"\n").encode())
    s.close()
if __name__=="__main__": main()
