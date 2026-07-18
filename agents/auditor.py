"""
agents/auditor.py
Step 2 of the graph. The Auditor never retrieves anything itself -- it
only takes the Compliance Analyzer's per-policy verdicts and turns them
into the final validated ComplianceReport (Pydantic-enforced schema).
"""

from typing import List, Dict

from agents import llm_client
from schema import ComplianceReport, ConflictingPolicy


def audit(
    regulation: dict, comparisons: List[Dict], trace_id: str
) -> ComplianceReport:
    conflicts = [c for c in comparisons if c["violates"]]

    if conflicts:
        conflicting_policies = [
            ConflictingPolicy(policy_id=c["policy_id"], reason=c["reason"])
            for c in conflicts
        ]
        # Base the recommendation on the strongest (first) conflict found.
        primary = conflicts[0]
        recommended_action = llm_client.recommend(
            {"id": primary["policy_id"], "text": primary["policy_text"]},
            regulation,
            primary["reason"],
        )
        conflict_detected = True
    else:
        conflicting_policies = []
        recommended_action = (
            "No action required. Existing policies already satisfy this "
            "regulation's requirements."
        )
        conflict_detected = False

    return ComplianceReport(
        target_regulation=regulation["id"],
        conflict_detected=conflict_detected,
        conflicting_policies=conflicting_policies,
        recommended_action=recommended_action,
        trace_id=trace_id,
    )
