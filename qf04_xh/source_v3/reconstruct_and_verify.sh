#!/usr/bin/env bash
set -euo pipefail
source_root="${1:-qf04_xh/source_v3}"
output_root="${2:-/tmp/qf04-source-v3}"
mkdir -p "$output_root/harness" "$output_root/sources"
reconstruct() {
  local chunk_dir="$1"
  local output_file="$2"
  awk '{printf "%s", $0}' "$chunk_dir"/part.* | base64 -d > "$output_file"
}
reconstruct "$source_root/harness_distributed" "$output_root/harness/distributed_recovery_qf.py"
reconstruct "$source_root/harness_crash" "$output_root/harness/coordinator_crash_driver.py"
reconstruct "$source_root/src_mfg" "$output_root/sources/GAIA_MFG_M01-A0a_executable_v0.1.zip"
reconstruct "$source_root/src_control" "$output_root/sources/gaia-atom-control-plane-v1.0.zip"
reconstruct "$source_root/src_staging" "$output_root/sources/gaia-atom-staging-qualification-v1.0.zip"
(cd "$output_root" && sha256sum -c "$OLDPWD/$source_root/SHA256SUMS")
python3 - "$output_root" <<'PY'
import hashlib, json, os, pathlib, socket, sys
root = pathlib.Path(sys.argv[1])
files = sorted(p for p in root.rglob('*') if p.is_file())
receipt = {
  'gate': 'QF04-XH_AUTHENTIC_SOURCE_RECONSTRUCTION',
  'status': 'PASS',
  'runner_name': os.getenv('RUNNER_NAME', 'local'),
  'runner_os': os.getenv('RUNNER_OS', sys.platform),
  'hostname': socket.gethostname(),
  'boot_id': pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
  'files': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
}
payload = json.dumps(receipt, sort_keys=True, separators=(',', ':'))
(root / 'reconstruction_receipt.json').write_text(payload + '\n')
print(payload)
PY
