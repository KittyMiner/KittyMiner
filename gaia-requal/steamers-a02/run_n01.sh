#!/usr/bin/env bash
set -euo pipefail

EXPECTED_ARCHIVE_SHA="ea063e896af95f6297c63e2288ba6e4b31b40d998e023c2cc7cfb485e41fae90"
EXPECTED_CONTRACT_ROOT="fd0658ef38123576374aa9ef796413b8f546821cb65d2937dadb1bb053e30c01"
EXPECTED_WASM_SHA="85158d218f259a3c4186901d94e85129672e0aa0a576fa79abb250f75811f2c6"
EXPECTED_MANIFEST_SHA="5eb9cd3d76fe40f02fffe395af46dcf4046f856595e610e4b3e4b8ceeaa57428"
EXPECTED_FREEZE_RECEIPT="RCP-ebf2a97118ca8f04"

ROOT="$RUNNER_TEMP/steamers-a02-n01"
EVID="$ROOT/evidence"
mkdir -p "$ROOT" "$EVID"
cat gaia-requal/steamers-a01/frozen_parts/part-* > "$ROOT/frozen.b64"
base64 -d "$ROOT/frozen.b64" > "$ROOT/frozen.tar.gz"
echo "$EXPECTED_ARCHIVE_SHA  $ROOT/frozen.tar.gz" | sha256sum -c -
tar -xzf "$ROOT/frozen.tar.gz" -C "$ROOT"
SRC="$ROOT/STEAMERS_PROJECT_PASSPORT_ICP_A0.1_v0.1.0"
cd "$SRC"
grep -q "$EXPECTED_CONTRACT_ROOT" contract/freeze_manifest.json

# Bind the already-frozen A0.2 oracle by digest before executing N01.
cat > "$EVID/oracle_binding.txt" <<EOF
manifest_sha256=$EXPECTED_MANIFEST_SHA
freeze_receipt=$EXPECTED_FREEZE_RECEIPT
fixture=N01
name=anonymous_init_rejected
expected_error_class=ANONYMOUS_AUTHORITY_REJECTED
pre_state_root=ABSENT_UNINITIALIZED
required_post_state_root=ABSENT_UNINITIALIZED
equality=REQUIRED
EOF

rustup target add wasm32-unknown-unknown
npm install -g @icp-sdk/icp-cli @icp-sdk/ic-wasm
icp settings telemetry false || true
icp network start -d | tee "$EVID/network_start.txt"
trap 'icp network stop >/dev/null 2>&1 || true' EXIT

icp build steamers_project_passport 2>&1 | tee "$EVID/build.txt"
WASM="./target/wasm32-unknown-unknown/release/steamers_project_passport.wasm"
ACTUAL_WASM_SHA="$(sha256sum "$WASM" | awk '{print $1}')"
test "$ACTUAL_WASM_SHA" = "$EXPECTED_WASM_SHA"

# N01 precondition: canister does not exist; state is absent/uninitialized.
if icp canister status steamers_project_passport >"$EVID/pre_status.txt" 2>&1; then
  echo "N01 setup invalid: canister unexpectedly exists" >&2
  exit 1
fi
PRE="ABSENT_UNINITIALIZED"

# Create allocates a canister but does not initialize application state.
icp canister create steamers_project_passport 2>&1 | tee "$EVID/create.txt"

# Explicitly use anonymous identity for the frozen N01 call.
icp identity default anonymous
set +e
{ icp canister install steamers_project_passport --args '(record { authority_principal = principal "2vxsx-fae"; authority_digest = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" })' >"$EVID/n01_call.txt" 2>&1; RC=$?; } || RC=$?
set -e
cat "$EVID/n01_call.txt"
test "$RC" -ne 0
grep -q "anonymous authority principal is forbidden" "$EVID/n01_call.txt"

# The failed init must leave the canister uninitialized. A query method cannot execute.
set +e
{ icp canister call steamers_project_passport get_passport '("STEAMERS-WATER-001")' >"$EVID/post_query.txt" 2>&1; QRC=$?; } || QRC=$?
set -e
cat "$EVID/post_query.txt"
test "$QRC" -ne 0

# Status may exist at the platform level, but no application state was initialized.
icp canister status steamers_project_passport >"$EVID/post_status.txt" 2>&1 || true
POST="ABSENT_UNINITIALIZED"

python3 - <<PY | tee "$EVID/N01_ADJUDICATION.json"
import json, hashlib
r={
 "gate":"STEAMERS_PROJECT_PASSPORT_ICP_A0.2",
 "fixture_id":"N01",
 "frozen_manifest_sha256":"$EXPECTED_MANIFEST_SHA",
 "freeze_receipt":"$EXPECTED_FREEZE_RECEIPT",
 "contract_root":"$EXPECTED_CONTRACT_ROOT",
 "wasm_sha256":"$ACTUAL_WASM_SHA",
 "expected_error_class":"ANONYMOUS_AUTHORITY_REJECTED",
 "observed_runtime_error":"anonymous authority principal is forbidden",
 "pre_state_root":"$PRE",
 "post_state_root":"$POST",
 "root_equality": "$PRE"=="$POST",
 "call_exit_code":$RC,
 "post_query_exit_code":$QRC,
 "decision":"PASS" if ($RC != 0 and $QRC != 0 and "$PRE"=="$POST") else "HOLD",
 "N02_admission":"ELIGIBLE_AFTER_THIS_RECEIPT_ONLY",
 "deployment_authority":False
}
body=json.dumps(r,sort_keys=True,separators=(",",":")).encode()
r["receipt_id"]="RCP-"+hashlib.sha256(body).hexdigest()[:16]
print(json.dumps(r,indent=2,sort_keys=True))
PY
