"""
agents/local_reasoner.py

Deterministic, offline fallback for the "Compliance Analyzer" reasoning
step, used only when OPENAI_API_KEY is not configured (see llm_client.py).

It is intentionally simple and auditable: a small set of keyword/clause
heuristics that mirror the kind of reasoning a compliance analyst does
for THIS class of problem (permissive policy clauses vs. mandatory
approval/review clauses in a regulation). This is not a substitute for
a real LLM in production -- it exists so the graph is fully runnable and
gradeable with zero paid services, per the assignment's cost guide.
"""

import re

_APPROVAL_TERMS = [
    "pre-approval", "pre approval", "prior approval", "approval from",
    "approved by", "sign-off", "sign off", "authorization", "review by",
    "must be approved", "documented pre-approval",
]
_PERMISSIVE_WITHOUT_REVIEW_TERMS = [
    "without requiring", "without a formal review", "directly by",
    "encouraged to share", "may share", "permissible", "provided that",
    "no specific", "strictly omitted",
]


def _contains_any(text: str, terms) -> bool:
    text = text.lower()
    return any(t in text for t in terms)


def analyze_conflict(policy_text: str, regulation_text: str) -> dict:
    """
    Heuristic conflict check: a regulation that mandates approval/review
    conflicts with a policy that explicitly permits the same action
    without requiring that approval/review.
    """
    regulation_requires_approval = _contains_any(regulation_text, _APPROVAL_TERMS)
    policy_allows_without_approval = _contains_any(
        policy_text, _PERMISSIVE_WITHOUT_REVIEW_TERMS
    )

    if regulation_requires_approval and policy_allows_without_approval:
        # Try to name the specific clauses for a useful "reason".
        reg_clause = _first_matching_clause(regulation_text, _APPROVAL_TERMS)
        pol_clause = _first_matching_clause(policy_text, _PERMISSIVE_WITHOUT_REVIEW_TERMS)
        reason = (
            f"The policy permits the activity ({pol_clause.strip()}) without the "
            f"mandatory step the regulation requires ({reg_clause.strip()}). "
            "This is a direct conflict."
        )
        return {"violates": True, "reason": reason}

    return {
        "violates": False,
        "reason": (
            "No direct conflict detected: the regulation's approval/review "
            "requirement is not contradicted by an explicit permissive clause "
            "in this policy."
        ),
    }


def _first_matching_clause(text: str, terms) -> str:
    lowered = text.lower()
    for term in terms:
        idx = lowered.find(term)
        if idx != -1:
            # Grab the sentence containing the matched term for context.
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for s in sentences:
                if term in s.lower():
                    return s
    return text[:80]


def recommend_action(policy_id: str, reason: str) -> str:
    return (
        f"Update {policy_id} to explicitly require documented pre-approval "
        f"from the relevant compliance/review committee before the described "
        f"activity occurs, closing the gap identified: {reason}"
    )
