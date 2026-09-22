#!/usr/bin/env bash
set -euo pipefail

BRANCH_ROOT="$PWD"
PART_DIR="$BRANCH_ROOT/gaia-requal/steamers-a01/frozen_parts"
WORK="$RUNNER_TEMP/steamers-a01-requal"
EVID="$WORK/evidence"
mkdir -p "$WORK" "$EVID"

EXPECTED_ARCHIVE_SHA="ea063e896af95f6297c63e2288ba6e4b31b40d998e023c2cc7cfb485e41fae90"
EXPECTED_CONTRACT_ROOT="fd0658ef38123576374aa9ef796413b8f546821cb65d2937dadb1bb053e30c01"
ARTIFACT_DIR="STEAMERS_PROJECT_PASSPORT_ICP_A0.1_v0.1.0"

cat "$PART_DIR"/part-* > "$WORK/frozen_bundle.tar.gz.b64"
base64 -d "$WORK/frozen_bundle.tar.gz.b64" > "$WORK/frozen_bundle.tar.gz"
echo "$EXPECTED_ARCHIVE_SHA  $WORK/frozen_bundle.tar.gz" | sha256sum -c -
tar -xzf "$WORK/frozen_bundle.tar.gz" -C "$WORK"
ROOT="$WORK/$ARTIFACT_DIR"
cd "$ROOT"

python3 -m pip install --disable-pip-version-check --quiet jsonschema
python3 tests/verify_freeze.py | tee "$EVID/freeze_verification.txt"
python3 tests/verify_surface.py | tee "$EVID/surface_verification.txt"
python3 tests/validate_examples.py | tee "$EVID/schema_fixture_validation.txt"

grep -q "$EXPECTED_CONTRACT_ROOT" contract/freeze_manifest.json
grep -q "$EXPECTED_CONTRACT_ROOT" canister/src/lib.rs
python3 - <<'PY' | tee "$EVID/source_hash_verification.txt"
import hashlib, json, pathlib, sys
root = pathlib.Path('.')
manifest = json.loads((root/'evidence/implementation_manifest.json').read_text())
errors=[]
for rel, expected in manifest['source_sha256'].items():
    got=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    print(f"{rel} {got} {'PASS' if got==expected else 'FAIL'}")
    if got!=expected: errors.append((rel, expected, got))
if errors:
    print(errors, file=sys.stderr)
    sys.exit(1)
PY

printf 'rustc=' | tee "$EVID/toolchain_versions.txt"; rustc --version | tee -a "$EVID/toolchain_versions.txt"
printf 'cargo=' | tee -a "$EVID/toolchain_versions.txt"; cargo --version | tee -a "$EVID/toolchain_versions.txt"
printf 'rustup=' | tee -a "$EVID/toolchain_versions.txt"; rustup --version | tee -a "$EVID/toolchain_versions.txt"
rustup target add wasm32-unknown-unknown
npm install -g @icp-sdk/icp-cli @icp-sdk/ic-wasm
cargo install candid-extractor --locked
printf 'icp=' | tee -a "$EVID/toolchain_versions.txt"; icp --version | tee -a "$EVID/toolchain_versions.txt"
printf 'ic-wasm=' | tee -a "$EVID/toolchain_versions.txt"; ic-wasm --version | tee -a "$EVID/toolchain_versions.txt"
printf 'candid-extractor=' | tee -a "$EVID/toolchain_versions.txt"; candid-extractor --version | tee -a "$EVID/toolchain_versions.txt" || true

icp settings telemetry false || true
icp network start -d | tee "$EVID/network_start.txt"
trap 'icp network stop >/dev/null 2>&1 || true' EXIT

PRINCIPAL="$(icp identity principal | tr -d '\r\n')"
AUTH_DIGEST="$(printf '%s' 'STEAMERS_A0.1_TRUST_KERNEL_SYNTHETIC_AUTHORITY' | sha256sum | awk '{print $1}')"
BASELINE_DIGEST="$(printf '%s' 'STEAMERS-WATER-001 baseline v0.1' | sha256sum | awk '{print $1}')"
EVIDENCE_DIGEST="$(printf '%s' 'STEAMERS-WATER-001 synthetic evidence E-001' | sha256sum | awk '{print $1}')"
RATIONALE_DIGEST="$(printf '%s' 'independent synthetic reviewer rationale PASS' | sha256sum | awk '{print $1}')"
ISSUED_NS=1700000000000000000
EXPIRES_NS=4102444800000000000
PROJECT_ID="STEAMERS-WATER-001"
INIT_ARGS="(record { authority_principal = principal \"$PRINCIPAL\"; authority_digest = \"$AUTH_DIGEST\" })"

{
  echo "principal=$PRINCIPAL"
  echo "authority_digest=$AUTH_DIGEST"
  echo "baseline_digest=$BASELINE_DIGEST"
  echo "evidence_digest=$EVIDENCE_DIGEST"
  echo "rationale_digest=$RATIONALE_DIGEST"
  echo "issued_at_ns=$ISSUED_NS"
  echo "expires_at_ns=$EXPIRES_NS"
} > "$EVID/fixture_constants.txt"

icp build steamers_project_passport 2>&1 | tee "$EVID/build_run1.txt"
find . -type f -name '*.wasm' -print0 | sort -z | xargs -0 -r sha256sum | tee "$EVID/wasm_hashes_after_build.txt"
icp canister create steamers_project_passport 2>&1 | tee "$EVID/canister_create.txt"
icp canister install steamers_project_passport --args "$INIT_ARGS" 2>&1 | tee "$EVID/install_run1.txt"
icp canister status steamers_project_passport 2>&1 | tee "$EVID/status_run1.txt"

make_lease() {
  local method="$1" lease_id="$2" actor_ref="$3" actor_role="$4" prev="$5"
  local prev_expr
  if [[ "$prev" == "NONE" ]]; then
    prev_expr="null"
  else
    prev_expr="opt \"$prev\""
  fi
  cat <<LEASE
record {
  schema_version = "0.1.0";
  lease_id = "$lease_id";
  project_id = "$PROJECT_ID";
  caller_ref = "$PRINCIPAL";
  actor_ref = "$actor_ref";
  actor_role = "$actor_role";
  permitted_method = "$method";
  issued_at_ns = $ISSUED_NS : nat64;
  expires_at_ns = $EXPIRES_NS : nat64;
  expected_previous_state_root = $prev_expr;
  authority_digest = "$AUTH_DIGEST";
  signature_ref = "TK-SYNTHETIC-$lease_id";
}
LEASE
}

extract_field() {
  local file="$1" field="$2"
  grep -oE "$field = \"[a-f0-9]{64}\"" "$file" | tail -1 | cut -d'"' -f2
}

assert_ok() {
  local file="$1"
  if ! grep -qE 'variant[[:space:]]*\{[[:space:]]*Ok|Ok[[:space:]]*=' "$file"; then
    echo "Expected Ok result in $file" >&2
    cat "$file" >&2
    return 1
  fi
}

run_sequence() {
  local run="$1"
  local out="$EVID/$run"
  mkdir -p "$out"
  : > "$out/roots.txt"

  local lease root evroot

  lease="$(make_lease create_passport LEASE-001 OWNER-DEMO-001 OWNER NONE)"
  icp canister call steamers_project_passport create_passport "($lease, record { project_id = \"$PROJECT_ID\"; program_id = \"STEAMERS\"; title = \"Synthetic Water Quality Monitor\"; owner_ref = \"OWNER-DEMO-001\"; gate_id = \"STEAMERS-WATER-001-A0\" })" 2>&1 | tee "$out/01_create_passport.txt"
  assert_ok "$out/01_create_passport.txt"
  root="$(extract_field "$out/01_create_passport.txt" resulting_state_root)"
  echo "create_passport $root" >> "$out/roots.txt"

  icp canister call steamers_project_passport get_passport "(\"$PROJECT_ID\")" 2>&1 | tee "$out/02_get_passport_after_create.txt"
  assert_ok "$out/02_get_passport_after_create.txt"

  lease="$(make_lease freeze_baseline LEASE-002 OWNER-DEMO-001 OWNER "$root")"
  icp canister call steamers_project_passport freeze_baseline "($lease, record { version = \"v0.1\"; digest = \"$BASELINE_DIGEST\" })" 2>&1 | tee "$out/03_freeze_baseline.txt"
  assert_ok "$out/03_freeze_baseline.txt"
  root="$(extract_field "$out/03_freeze_baseline.txt" resulting_state_root)"
  echo "freeze_baseline $root" >> "$out/roots.txt"

  lease="$(make_lease admit_evidence LEASE-003 OWNER-DEMO-001 OWNER "$root")"
  icp canister call steamers_project_passport admit_evidence "($lease, record { evidence_id = \"E-001\"; evidence_type = \"SYNTHETIC_SENSOR_SCHEMA\"; digest = \"$EVIDENCE_DIGEST\"; provenance_ref = \"fixture://STEAMERS-WATER-001/E-001\" })" 2>&1 | tee "$out/04_admit_evidence.txt"
  assert_ok "$out/04_admit_evidence.txt"
  root="$(extract_field "$out/04_admit_evidence.txt" resulting_state_root)"
  evroot="$(extract_field "$out/04_admit_evidence.txt" evidence_root)"
  echo "admit_evidence $root" >> "$out/roots.txt"
  echo "$evroot" > "$out/evidence_root.txt"

  lease="$(make_lease set_next_action LEASE-004 OWNER-DEMO-001 OWNER "$root")"
  icp canister call steamers_project_passport set_next_action "($lease, record { action_id = \"NA-001\"; description = \"Validate synthetic sensor input schema against the frozen baseline.\"; bounded = true })" 2>&1 | tee "$out/05_set_next_action.txt"
  assert_ok "$out/05_set_next_action.txt"
  root="$(extract_field "$out/05_set_next_action.txt" resulting_state_root)"
  echo "set_next_action $root" >> "$out/roots.txt"

  lease="$(make_lease transition_gate LEASE-005 SYSTEM-LOCAL-REQUAL SYSTEM "$root")"
  icp canister call steamers_project_passport transition_gate "($lease, \"VERIFY\")" 2>&1 | tee "$out/06_transition_verify.txt"
  assert_ok "$out/06_transition_verify.txt"
  root="$(extract_field "$out/06_transition_verify.txt" resulting_state_root)"
  echo "transition_VERIFY $root" >> "$out/roots.txt"

  lease="$(make_lease record_review LEASE-006 REVIEWER-INDEPENDENT-001 REVIEWER "$root")"
  icp canister call steamers_project_passport record_review "($lease, record { review_id = \"REV-001\"; reviewer_ref = \"REVIEWER-INDEPENDENT-001\"; decision = \"PASS\"; evidence_root = \"$evroot\"; rationale_digest = \"$RATIONALE_DIGEST\" })" 2>&1 | tee "$out/07_record_review.txt"
  assert_ok "$out/07_record_review.txt"
  root="$(extract_field "$out/07_record_review.txt" resulting_state_root)"
  echo "record_review $root" >> "$out/roots.txt"

  lease="$(make_lease transition_gate LEASE-007 SYSTEM-LOCAL-REQUAL SYSTEM "$root")"
  icp canister call steamers_project_passport transition_gate "($lease, \"PASS\")" 2>&1 | tee "$out/08_transition_pass.txt"
  assert_ok "$out/08_transition_pass.txt"
  root="$(extract_field "$out/08_transition_pass.txt" resulting_state_root)"
  echo "transition_PASS $root" >> "$out/roots.txt"

  icp canister call steamers_project_passport get_passport "(\"$PROJECT_ID\")" 2>&1 | tee "$out/09_get_passport_final.txt"
  assert_ok "$out/09_get_passport_final.txt"
  local query_root
  query_root="$(extract_field "$out/09_get_passport_final.txt" current_state_root)"
  if [[ "$query_root" != "$root" ]]; then
    echo "Final query root mismatch: receipt=$root query=$query_root" >&2
    exit 1
  fi
  echo "$root" > "$out/final_semantic_root.txt"
}

run_sequence run1

icp deploy steamers_project_passport --mode reinstall --argument "$INIT_ARGS" 2>&1 | tee "$EVID/reinstall_run2.txt"
icp canister status steamers_project_passport 2>&1 | tee "$EVID/status_run2.txt"
run_sequence run2

cmp -s "$EVID/run1/roots.txt" "$EVID/run2/roots.txt"
cmp -s "$EVID/run1/final_semantic_root.txt" "$EVID/run2/final_semantic_root.txt"

FINAL_ROOT="$(cat "$EVID/run1/final_semantic_root.txt")"
WASM_HASH="$(find . -type f -name '*.wasm' -print0 | sort -z | xargs -0 -r sha256sum | head -1 | awk '{print $1}')"
cat > "$EVID/semantic_root_comparison.txt" <<REPORT
contract_root=$EXPECTED_CONTRACT_ROOT
run1_final_semantic_root=$FINAL_ROOT
run2_final_semantic_root=$FINAL_ROOT
root_sequences_equal=PASS
final_roots_equal=PASS
wasm_hash_observed=$WASM_HASH
REPORT

python3 - <<PY > "$EVID/A0.1_RUNTIME_REQUALIFICATION.json"
import json
print(json.dumps({
  "artifact_id": "STEAMERS_PROJECT_PASSPORT_ICP_A0.1",
  "version": "v0.1.0",
  "requalification_event": "A0.1_RUNTIME_REQUALIFICATION_2026-09-22",
  "contract_canonical_root": "$EXPECTED_CONTRACT_ROOT",
  "frozen_source_archive_sha256": "$EXPECTED_ARCHIVE_SHA",
  "wasm_hash_observed": "$WASM_HASH",
  "local_replica_install": "PASS",
  "seven_method_surface_exercised": "PASS",
  "clean_state_execution_1": "PASS",
  "clean_state_execution_2": "PASS",
  "semantic_root_sequence_equality": "PASS",
  "final_semantic_root": "$FINAL_ROOT",
  "decision": "PASS",
  "deployment_authority": False,
  "public_icp_deployment": "CLOSED"
}, indent=2, sort_keys=True))
PY

cat "$EVID/A0.1_RUNTIME_REQUALIFICATION.json"
