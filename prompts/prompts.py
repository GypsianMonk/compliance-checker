"""
prompts.py
Prompt templates used by the LLM-backed compliance/auditor step.
Kept separate from agent logic so they can be iterated on without
touching control flow.
"""

COMPLIANCE_ANALYSIS_PROMPT = """You are a corporate compliance analyst.

Compare the RETRIEVED COMPANY POLICY against the NEW REGULATION below, and
decide whether the policy, as written, would violate the regulation.

RETRIEVED COMPANY POLICY (id: {policy_id}, section: {policy_section}):
\"\"\"{policy_text}\"\"\"

NEW REGULATION (id: {regulation_id}):
\"\"\"{regulation_text}\"\"\"

Think step by step about what each document permits or requires, then decide
if there is a direct conflict. Respond ONLY with a JSON object of this exact
shape, no other text:

{{
  "violates": true or false,
  "reason": "one or two sentence explanation citing the specific clauses that conflict (or confirming alignment)"
}}
"""

RECOMMENDATION_PROMPT = """Given this confirmed policy/regulation conflict:

Policy {policy_id}: \"\"\"{policy_text}\"\"\"
Regulation {regulation_id}: \"\"\"{regulation_text}\"\"\"
Reason for conflict: \"\"\"{reason}\"\"\"

In one sentence, recommend the specific policy change needed to resolve the
conflict. Respond with plain text only, no JSON, no preamble.
"""
