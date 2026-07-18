"""
config.py
Central configuration. Reads from environment variables so no secrets
are ever hard-coded. Every value has a safe default so the prototype
runs end-to-end with zero paid services configured.
"""

import os

# --- LLM configuration -------------------------------------------------
# If OPENAI_API_KEY is set, the Compliance/Auditor agents call the real
# OpenAI API. If it is NOT set, they fall back to a deterministic,
# rule-based reasoning engine (see agents/local_reasoner.py) so the
# whole graph still runs offline for demo/grading purposes.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
USE_REAL_LLM = bool(OPENAI_API_KEY)

# --- Observability -------------------------------------------------------
# Native LangSmith support: set these env vars and every LangGraph node
# is traced automatically, no code changes needed. Both the newer
# LANGSMITH_* names and the older LANGCHAIN_* names are accepted, since
# different LangSmith docs/versions use different names for the same
# variables:
#   LANGSMITH_TRACING=true          (or LANGCHAIN_TRACING_V2=true)
#   LANGSMITH_API_KEY=lsv2_...       (or LANGCHAIN_API_KEY=ls__...)
#   LANGSMITH_PROJECT=my-project     (or LANGCHAIN_PROJECT=...)
#   LANGSMITH_ENDPOINT=https://...   (or LANGCHAIN_ENDPOINT=...)
_TRACING_RAW = os.getenv("LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "false"))
LANGSMITH_ENABLED = _TRACING_RAW.lower() == "true"

if LANGSMITH_ENABLED:
    # The LangChain/LangGraph tracer instrumentation reads the LANGCHAIN_*
    # names specifically, so mirror LANGSMITH_* into LANGCHAIN_* for
    # anyone who only set the newer names (e.g. via GitHub Actions secrets).
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    for _new, _old in [
        ("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"),
        ("LANGSMITH_PROJECT", "LANGCHAIN_PROJECT"),
        ("LANGSMITH_ENDPOINT", "LANGCHAIN_ENDPOINT"),
    ]:
        if os.getenv(_new) and not os.getenv(_old):
            os.environ[_old] = os.environ[_new]

# Fallback local tracer (always on) writes a LangSmith-shaped JSONL
# trace file so a reviewer can inspect the run even with no LangSmith
# account configured.
LOCAL_TRACE_DIR = os.getenv("LOCAL_TRACE_DIR", "output/traces")

# --- Vector store ----------------------------------------------------------
CHROMA_COLLECTION_NAME = "company_policies"
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", None)  # None = in-memory only

# --- Data paths -----------------------------------------------------------
POLICIES_PATH = os.path.join(os.path.dirname(__file__), "policies", "policies.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "report.json")
