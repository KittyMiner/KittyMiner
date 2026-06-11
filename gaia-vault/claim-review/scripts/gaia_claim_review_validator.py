#!/usr/bin/env python3
"""Validate Gaia Vault claim-review fields across text registries.

Scans YAML, JSON, Markdown, CSV, and TSV files for Gaia/GUC node-like records and
reports whether required claim-review fields are present.

This validator is intentionally conservative: it does not prove scientific
validity. It checks governance metadata completeness and flags restricted claim
classes that must remain blocked unless evidence is supplied.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = [
    "node_id",
    "title",
    "version",
    "source_assets",
    "claim_type",
    "evidence_layer",
    "evidence_level",
    "validation_status",
    "blocked_claims",
    "permitted_uses",
    "review_required",
    "public_release_status",
    "promotion_requirements",
    "audit_trail",
    "next_actions",
]

RESTRICTED_TERMS = {
    "physical_law": "blocked_pending_validation",
    "energy": "blocked_pending_validation",
    "resonance_causality": "blocked_pending_validation",
    "propulsion_field": "blocked_pending_validation",
    "hidden_constant_encoding": "blocked_pending_validation",
    "medical_safety_compliance": "blocked_pending_qualified_review",
    "investment_performance": "blocked_pending_evidence_and_legal_review",
}

TEXT_EXTENSIONS = {".yaml", ".yml", ".json", ".md", ".csv", ".tsv"}


def normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"__parse_error__": str(exc)}


def flatten_dict(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            norm = normalize_key(str(key))
            full = f"{prefix}_{norm}" if prefix else norm
            out[full] = value
            out.update(flatten_dict(value, full))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            out.update(flatten_dict(value, f"{prefix}_{index}" if prefix else str(index)))
    return out


def scan_text_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^\s*[-*]?\s*([A-Za-z0-9 _/-]{2,80})\s*[:=]", line)
        if match:
            keys.add(normalize_key(match.group(1)))
    return keys


def scan_csv_keys(path: Path) -> set[str]:
    delimiter = "\t" if path.suffix == ".tsv" else ","
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            header = next(reader, [])
    except Exception:
        return set()
    return {normalize_key(col) for col in header}


def field_presence(path: Path) -> tuple[set[str], str]:
    if path.suffix == ".json":
        obj = read_json(path)
        if isinstance(obj, dict):
            keys = set(flatten_dict(obj).keys()) | {normalize_key(k) for k in obj.keys()}
            return keys, json.dumps(obj, ensure_ascii=False)[:10000]
    if path.suffix in {".csv", ".tsv"}:
        text = path.read_text(encoding="utf-8", errors="ignore")[:10000]
        return scan_csv_keys(path) | scan_text_keys(text), text
    text = path.read_text(encoding="utf-8", errors="ignore")
    return scan_text_keys(text), text[:10000]


def file_mentions_node(text: str) -> bool:
    markers = [
        "node_id",
        "claim_type",
        "evidence_layer",
        "validation_status",
        "Gaia Vault",
        "Gaia/GUC",
        "blocked_pending_validation",
        "propulsion",
        "resonance",
        "energy claim",
    ]
    lower = text.lower()
    return any(marker.lower() in lower for marker in markers)


def restricted_flags(text: str) -> list[str]:
    lower = text.lower()
    flags = []
    for term in RESTRICTED_TERMS:
        if term.replace("_", " ") in lower or term in lower:
            flags.append(term)
    return flags


def validate_path(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        keys, sample = field_presence(path)
        if not file_mentions_node(sample):
            continue
        missing = [field for field in REQUIRED_FIELDS if field not in keys]
        flags = restricted_flags(sample)
        status_present = "validation_status" in keys
        findings.append(
            {
                "path": str(path.relative_to(root)),
                "missing_required_fields": missing,
                "restricted_claim_terms_detected": flags,
                "has_validation_status": status_present,
                "status": "pass" if not missing else "fail",
            }
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Gaia Vault claim-review metadata.")
    parser.add_argument("root", nargs="?", default=".", help="Repository or export root to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    findings = validate_path(root)
    failures = [finding for finding in findings if finding["status"] == "fail"]
    result = {
        "root": str(root),
        "files_scanned_with_gaia_markers": len(findings),
        "failures": len(failures),
        "findings": findings,
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Gaia Vault claim-review scan: {root}")
        print(f"Files with Gaia markers: {len(findings)}")
        print(f"Failures: {len(failures)}")
        for finding in findings:
            print(f"- {finding['status'].upper()}: {finding['path']}")
            if finding["missing_required_fields"]:
                print("  missing: " + ", ".join(finding["missing_required_fields"]))
            if finding["restricted_claim_terms_detected"]:
                print("  restricted terms: " + ", ".join(finding["restricted_claim_terms_detected"]))

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
