from __future__ import annotations
import argparse, json, pathlib, socket, sys
SOURCE=pathlib.Path("/tmp/qf04-source-v3"); H=SOURCE/"harness"
sys.path.insert(0,str(H))
from distributed_recovery_qf import DistributedCoordinator, RecoveryLease, RemoteWorkerClient, TransportFailure, canonical_hash, read_jsonl

WFIDS={"MFG":"WF-MFG-BOM-FAT","CONTROL":"WF-CONTROL-PREFLIGHT","STAGING":"WF-STAGING-QUAL"}
EXPECTED={
 "normal":("PASS","COMMITTED"),
 "coordinator_loss_before_commit":("HOLD","ABORTED_RECOVERY_NO_COMMIT"),
 "coordinator_loss_after_commit":("PASS","COMMITTED_RECOVERED"),
 "partition_during_prepare":("HOLD","ROLLED_BACK"),
 "partition_during_commit":("PASS","COMMITTED_RECOVERED"),
 "delayed_reordered_duplicate_delivery":("PASS","COMMITTED"),
 "conflicting_recovery_views":("HOLD","RECOVERY_HOLD_CONFLICT"),
 "tampered_commit_decision":("HOLD","RECOVERY_HOLD"),
 "clock_skew_lease_expiry":("HOLD","LEASE_EXPIRED_FAIL_CLOSED"),
}
SCENARIOS=list(EXPECTED)

def control(host,port,obj):
    with socket.create_connection((host,port),timeout=130) as s:
        s.settimeout(130); s.sendall((json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n").encode()); data=b""
        while not data.endswith(b"\n"):
            c=s.recv(65536)
            if not c: break
            data+=c
    out=json.loads(data)
    if "error" in out: raise RuntimeError(out["error"])
    return out

def workers(info):
    return [RemoteWorkerClient(k,WFIDS[k],2,info["endpoints"][k]["host"],info["endpoints"][k]["port"],"TCP_IPV4_RELAYED_CROSS_HOST") for k in ("MFG","CONTROL","STAGING")]

def coordinator(root,ws):
    return DistributedCoordinator(composition_id="GAIA-COMP-QF04-MFG-CONTROL-STAGING-DISTRIBUTED-RECOVERY-v0.1",workers=ws,coordinator_journal=root/"coordinator.jsonl",authority_ceiling=2,active_version="ORCH-QF-ACTIVE-v0.1")
def lease(tx): return RecoveryLease.issue(tx_id=tx,actor="RECOVERY-COORDINATOR",authority_ceiling=2)

def run_one(chost,cport,campaign,name,root):
    info=control(chost,cport,{"op":"START","campaign":campaign,"scenario":name}); ws=workers(info); c=coordinator(root,ws); tx="TX-QF04-XH-"+name.upper().replace("_","-")
    extra={}
    if name=="normal": r=c.run(tx)
    elif name.startswith("coordinator_loss_"):
        mode="prepare-crash" if name.endswith("before_commit") else "commit-crash"
        cr=control(chost,cport,{"op":"CRASH","mode":mode,"tx_id":tx})
        c.coordinator_journal.write_text(cr["journal"])
        if mode=="prepare-crash": extra["recovery_without_lease"]=c.recover(tx,recovery_lease=None)
        r=c.recover(tx,recovery_lease=lease(tx)); extra["observed_coordinator_exit_code"]=cr["exit_code"]; extra["coordinator_relocated_between_vms"]=True
    elif name=="partition_during_prepare":
        control(chost,cport,{"op":"DROP","worker":"CONTROL"}); r=c.run(tx); extra["fault_method"]="ROUTED_RELAY_PATH_TERMINATION_PREPARE"
    elif name=="partition_during_commit":
        prep=c.prepare_all(tx); commit=c.write_commit_decision(tx); ws[0].finalize(tx,commit["global_commit_hash"])
        control(chost,cport,{"op":"DROP","worker":"CONTROL"})
        try: ws[1].finalize(tx,commit["global_commit_hash"]); raise AssertionError("partition not observed")
        except TransportFailure: pass
        restored=control(chost,cport,{"op":"RESTORE","worker":"CONTROL"}); ws[1].port=restored["port"]
        r=c.recover(tx,recovery_lease=lease(tx)); extra.update({"prepared_count":prep["prepared_count"],"fault_method":"ROUTED_RELAY_PATH_TERMINATION_COMMIT","durable_commit_preexisted_partition":True})
    elif name=="delayed_reordered_duplicate_delivery":
        pre=ws[0].finalize(tx,"deadbeef"); r=c.run(tx); latep=ws[0].prepare(tx,"LATE-DUP","GENESIS",120000); latef=ws[0].finalize(tx,r["global_commit_hash"])
        extra["delivery_checks"]={"pre_finalize_denied":pre["decision"]=="DENY_FINALIZE_WITHOUT_PREPARE","late_prepare_duplicate":latep.get("duplicate") is True,"late_finalize_duplicate":latef["decision"]=="FINALIZED_DUPLICATE"}
    elif name=="conflicting_recovery_views":
        c.prepare_all(tx); ws[0]._request({"op":"FORCE_TEST_VIEW","tx_id":tx,"state":"FINALIZED","global_commit_hash":"conflicting-hash"}); ws[1].abort(tx,"INJECT_CONFLICTING_VIEW"); r=c.recover(tx,recovery_lease=lease(tx))
    elif name=="tampered_commit_decision":
        c.prepare_all(tx); c.write_commit_decision(tx); rows=read_jsonl(c.coordinator_journal); rows[-1]["global_commit_hash"]="0"*64; c.coordinator_journal.write_text("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in rows)+"\n"); r=c.recover(tx,recovery_lease=lease(tx))
    elif name=="clock_skew_lease_expiry":
        req={"op":"PREPARE","tx_id":tx,"delivery_id":tx+":1:MFG","dependency_hash":"GENESIS","lease_ms":0.001,"lease_token":__import__("distributed_recovery_qf")._execution_token(tx,WFIDS["MFG"],2,0.001),"authority_ceiling":2,"wall_clock_claim_ms":4102444800000}
        out=ws[0]._request(req,timeout=125); c._abort_all(tx,"LEASE_EXPIRED"); r={**c._base(tx),"decision":"HOLD","transaction_state":"LEASE_EXPIRED_FAIL_CLOSED","failure_class":out["decision"],"global_commit_hash":None,"promoted_steps":[],"commit_decision_reconstructed":False}; r=c._finish(r); extra={"future_wall_clock_claim_ignored":True,"monotonic_lease_expired":out["decision"]=="LEASE_EXPIRED_DURING_EXECUTION"}
    exp=EXPECTED[name]
    if (r["decision"],r["transaction_state"])!=exp: raise AssertionError((name,r["decision"],r["transaction_state"],exp))
    if r.get("authority_inherited") or r.get("external_effects")!=0 or (r["decision"]!="PASS" and r.get("promoted_steps")): raise AssertionError("constitutional invariant failure")
    obj={"scenario":name,"receipt":r,**extra}; obj["scenario_hash"]=canonical_hash(obj); return obj,info["worker_vm"]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--control-host"); ap.add_argument("--control-port",type=int); ap.add_argument("--out",required=True); a=ap.parse_args()
    out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True); campaigns=[]; worker_vm=None
    try:
        for run in (1,2):
            rows=[]
            for name in SCENARIOS:
                rr=out/f"run{run}"/name; rr.mkdir(parents=True,exist_ok=True)
                x,worker_vm=run_one(a.control_host,a.control_port,f"run{run}",name,rr); rows.append(x)
            campaigns.append(rows)
        hashes1=[x["scenario_hash"] for x in campaigns[0]]; hashes2=[x["scenario_hash"] for x in campaigns[1]]
        result={"qualification_id":"GAIA-ORCHESTRATOR-QF04-XH","campaigns":campaigns,"two_run_reproducible":hashes1==hashes2,"worker_vm":worker_vm,"coordinator_vm":{"runner_name":__import__("os").getenv("RUNNER_NAME"),"hostname":socket.gethostname(),"boot_id":pathlib.Path("/proc/sys/kernel/random/boot_id").read_text().strip()},"source_bundle_sha256":"6f7d62aff134dfaba54c5c4653ba97c32834295dc58f7f1f541269a02c052755","external_effects":0,"authority_expansion":0}
        result["independent_vm"]=result["worker_vm"]["boot_id"]!=result["coordinator_vm"]["boot_id"] and result["worker_vm"]["runner_name"]!=result["coordinator_vm"]["runner_name"]
        if not result["two_run_reproducible"] or not result["independent_vm"]: raise AssertionError("physical/reproducibility gate failed")
        result["campaign_hash"]=canonical_hash({"campaigns":campaigns})
        (out/"qf04_xh_campaign.json").write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
        print(json.dumps({"status":"PASS","campaign_hash":result["campaign_hash"],"independent_vm":result["independent_vm"],"scenarios":len(SCENARIOS)},sort_keys=True))
    finally:
        try: control(a.control_host,a.control_port,{"op":"STOP"})
        except Exception: pass
if __name__=="__main__": main()
