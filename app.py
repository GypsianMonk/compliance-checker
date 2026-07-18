"""
app.py
Entry point. Builds the vector store, runs the LangGraph compliance
check against one or more regulations, prints + saves the structured
report(s), and points to the observability trace file.

Usage:
    python app.py                       # runs Rule A (required) + Rule B (edge case)
    python app.py --regulation A        # runs only Rule A
    OPENAI_API_KEY=sk-...  python app.py   # uses the real LLM instead of the offline fallback
"""

import argparse
import json
import os

from config import OUTPUT_PATH, USE_REAL_LLM
from vectorstore.chroma_store import build_collection
from graph.compliance_graph import run_compliance_check

REGULATIONS = {
    "A": {
        "id": "REG_2026_PR_COMPLIANCE",
        "text": (
            "To mitigate insider trading and reputational risk, all external "
            "public communications, social media updates, or technical "
            "publications regarding active company projects must receive "
            "explicit, documented pre-approval from the PR Compliance "
            "Committee prior to publication."
        ),
    },
    "B": {
        "id": "REG_2026_SEC_VENDOR",
        "text": (
            "All external software vendors, micro-services, and digital "
            "tools interacting with company data-regardless of contract "
            "value or tier-must undergo a mandatory automated security "
            "scanning and static analysis review by the central InfoSec "
            "team."
        ),
    },
}


def main():
    parser = argparse.ArgumentParser(description="Automated compliance checker")
    parser.add_argument(
        "--regulation",
        choices=["A", "B", "all"],
        default="all",
        help="Which regulation to check (default: all)",
    )
    args = parser.parse_args()

    print(f"[app] LLM mode: {'OpenAI (' + os.getenv('OPENAI_MODEL', 'gpt-4o-mini') + ')' if USE_REAL_LLM else 'offline rule-based fallback (no OPENAI_API_KEY set)'}")

    collection = build_collection()
    print("[app] Vector store ready: 3 policies embedded into Chroma.\n")

    regulations = (
        [REGULATIONS[args.regulation]]
        if args.regulation != "all"
        else [REGULATIONS["A"], REGULATIONS["B"]]
    )

    reports = []
    for regulation in regulations:
        print(f"--- Checking {regulation['id']} ---")
        report, trace_file = run_compliance_check(collection, regulation)
        reports.append(report.model_dump())
        print(json.dumps(report.model_dump(), indent=2))
        print(f"[app] Trace written to: {trace_file}\n")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(reports if len(reports) > 1 else reports[0], f, indent=2)
    print(f"[app] Final report(s) saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
