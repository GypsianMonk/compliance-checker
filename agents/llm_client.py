"""
agents/llm_client.py

Single choke point for "ask the model to reason about a conflict".
Downstream agent code never checks USE_REAL_LLM itself -- it just calls
`analyze(policy, regulation)` and gets back a dict:
    {"violates": bool, "reason": str}

This keeps agents/compliance_agent.py and agents/auditor.py identical
regardless of whether a real LLM or the offline fallback is answering.
"""

import json

from config import USE_REAL_LLM, OPENAI_API_KEY, OPENAI_MODEL, REQUIRE_REAL_LLM
from prompts.prompts import COMPLIANCE_ANALYSIS_PROMPT, RECOMMENDATION_PROMPT
from agents import local_reasoner


def analyze(policy: dict, regulation: dict) -> dict:
    if USE_REAL_LLM:
        try:
            return _analyze_with_openai(policy, regulation)
        except Exception as exc:
            if REQUIRE_REAL_LLM:
                raise RuntimeError(
                    f"REQUIRE_REAL_LLM is set but the OpenAI analysis call failed: {exc!r}"
                ) from exc
            print(f"[llm_client] OpenAI analysis call failed ({exc!r}); "
                  f"falling back to local rule-based reasoning for this policy.")
    return local_reasoner.analyze_conflict(policy["text"], regulation["text"])


def recommend(policy: dict, regulation: dict, reason: str) -> str:
    if USE_REAL_LLM:
        try:
            return _recommend_with_openai(policy, regulation, reason)
        except Exception as exc:
            if REQUIRE_REAL_LLM:
                raise RuntimeError(
                    f"REQUIRE_REAL_LLM is set but the OpenAI recommendation call failed: {exc!r}"
                ) from exc
            print(f"[llm_client] OpenAI recommendation call failed ({exc!r}); "
                  f"falling back to local rule-based recommendation.")
    return local_reasoner.recommend_action(policy["id"], reason)


def _analyze_with_openai(policy: dict, regulation: dict) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = COMPLIANCE_ANALYSIS_PROMPT.format(
        policy_id=policy["id"],
        policy_section=policy.get("section", ""),
        policy_text=policy["text"],
        regulation_id=regulation["id"],
        regulation_text=regulation["text"],
    )
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(resp.choices[0].message.content)


def _recommend_with_openai(policy: dict, regulation: dict, reason: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = RECOMMENDATION_PROMPT.format(
        policy_id=policy["id"],
        policy_text=policy["text"],
        regulation_id=regulation["id"],
        regulation_text=regulation["text"],
        reason=reason,
    )
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()
