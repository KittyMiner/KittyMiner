from __future__ import annotations
import hashlib,json,pathlib,sys
EXPECTED={"normal":("PASS","COMMITTED"),"coordinator_loss_before_commit":("HOLD","ABORTED_RECOVERY_NO_COMMIT"),"coordinator_loss_after_commit":("PASS","COMMITTED_RECOVERED"),"partition_during_prepare":("HOLD","ROLLED_BACK"),"partition_during_commit":("PASS","COMMITTED_RECOVERED"),"delayed_reordered_duplicate_delivery":("PASS","COMMITTED"),"conflicting_recovery_views":("HOLD","RECOVERY_HOLD_CONFLICT"),"tampered_commit_decision":("HOLD","RECOVERY_HOLD"),"clock_skew_lease_expiry":("HOLD","LEASE_EXPIRED_FAIL_CLOSED")}
def cb(x): return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
p=pathlib.Path(sys.argv[1]); d=json.loads(p.read_text()); checks={}
checks["source_root"]=d["source_bundle_sha256"]=="6f7d62aff134dfaba54c5c4653ba97c32834295dc58f7f1f541269a02c052755"
checks["independent_vm"]=d["independent_vm"] and d["worker_vm"]["boot_id"]!=d["coordinator_vm"]["boot_id"]
checks["two_runs"]=len(d["campaigns"])==2 and d["two_run_reproducible"]
checks["scenario_set"]=all({x["scenario"] for x in run}==set(EXPECTED) for run in d["campaigns"])
checks["decisions"]=all((x["receipt"]["decision"],x["receipt"]["transaction_state"])==EXPECTED[x["scenario"]] for run in d["campaigns"] for x in run)
checks["zero_effects"]=d["external_effects"]==0 and all(x["receipt"]["external_effects"]==0 for run in d["campaigns"] for x in run)
checks["zero_authority_inheritance"]=d["authority_expansion"]==0 and all(x["receipt"]["authority_inherited"] is False for run in d["campaigns"] for x in run)
checks["zero_partial_promotion"]=all(not x["receipt"].get("promoted_steps") for run in d["campaigns"] for x in run if x["receipt"]["decision"]!="PASS")
checks["scenario_hashes"]=all(hashlib.sha256(cb({k:v for k,v in x.items() if k!="scenario_hash"})).hexdigest()==x["scenario_hash"] for run in d["campaigns"] for x in run)
checks["campaign_hash"]=hashlib.sha256(cb({"campaigns":d["campaigns"]})).hexdigest()==d["campaign_hash"]
out={"gate":"QF04-XH_COLD_RECONSTRUCTION","checks":checks,"status":"PASS" if all(checks.values()) else "HOLD"}
out["receipt_hash"]=hashlib.sha256(cb(out)).hexdigest(); print(json.dumps(out,sort_keys=True,separators=(",",":"))); sys.exit(0 if out["status"]=="PASS" else 1)
