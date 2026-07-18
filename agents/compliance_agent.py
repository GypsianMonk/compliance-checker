"""
agents/compliance_agent.py
Runs the retrieved policy against the target regulation and returns a
raw {"violates": bool, "reason": str} per policy, via the LLM client
(real OpenAI or offline fallback -- transparent to this module).
"""

from typing import List, Dict
from agents import llm_client


def compare_policies_to_regulation(
    policies: List[dict], regulation: dict
) -> List[Dict]:
    results = []
    for policy in policies:
        verdict = llm_client.analyze(policy, regulation)
        results.append(
            {
                "policy_id": policy["id"],
                "policy_text": policy["text"],
                "violates": verdict["violates"],
                "reason": verdict["reason"],
            }
        )
    return results
