"""
scripts/verify_report.py
Asserts output/report.json matches the expected schema and, for the
known sample dataset, the expected conflict findings. Used by both the
offline CI job and the real-LLM CI job so they're checked identically.
"""

import json
import sys

with open("output/report.json") as f:
    reports = json.load(f)

required_keys = {
    "target_regulation",
    "conflict_detected",
    "conflicting_policies",
    "recommended_action",
    "trace_id",
}

for report in reports:
    missing = required_keys - report.keys()
    assert not missing, f"Missing keys in report: {missing}"
    assert isinstance(report["conflicting_policies"], list)

by_regulation = {r["target_regulation"]: r for r in reports}

reg_a = by_regulation.get("REG_2026_PR_COMPLIANCE")
if reg_a:
    flagged = {p["policy_id"] for p in reg_a["conflicting_policies"]}
    assert reg_a["conflict_detected"] is True
    assert flagged == {"policy_001"}, f"Expected only policy_001, got {flagged}"

reg_b = by_regulation.get("REG_2026_SEC_VENDOR")
if reg_b:
    flagged = {p["policy_id"] for p in reg_b["conflicting_policies"]}
    assert reg_b["conflict_detected"] is True
    assert flagged == {"policy_003"}, f"Expected only policy_003, got {flagged}"

print("All schema and regression checks passed.")
sys.exit(0)
