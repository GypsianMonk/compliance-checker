"""
graph/compliance_graph.py

The 2-step agentic graph the assignment asks for, built with LangGraph:

    START -> retriever_node -> compliance_node -> auditor_node -> END

(The assignment's "Step 1" and "Step 2" map onto three LangGraph nodes
here because Retrieval and Comparison are logically distinct, but the
Compliance Analyzer and Auditor stay strictly separated, per the spec:
"An Auditor step that evaluates ... and outputs a structured JSON
response" -- the Auditor only verifies/formats, it never re-retrieves.)

Every node execution is wrapped in a tracer span, so the full run
(inputs, outputs, latency per node) is captured for observability
regardless of whether LangSmith is configured.
"""

from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, END

from agents.retriever import retrieve_relevant_policies
from agents.compliance_agent import compare_policies_to_regulation
from agents.auditor import audit
from schema import ComplianceReport
from observability.tracer import RunTracer


class GraphState(TypedDict, total=False):
    collection: object
    regulation: dict
    retrieved_policies: List[dict]
    comparisons: List[dict]
    report: ComplianceReport
    tracer: RunTracer


def retriever_node(state: GraphState) -> GraphState:
    tracer: RunTracer = state["tracer"]
    regulation = state["regulation"]
    with tracer.span("retriever_node", {"regulation_id": regulation["id"]}) as rec:
        matches = retrieve_relevant_policies(state["collection"], regulation["text"])
        rec["output"] = {"matched_policy_ids": [m["id"] for m in matches]}
    return {"retrieved_policies": matches}


def compliance_node(state: GraphState) -> GraphState:
    tracer: RunTracer = state["tracer"]
    regulation = state["regulation"]
    policies = [
        {"id": m["id"], "section": m["section"], "text": m["text"]}
        for m in state["retrieved_policies"]
    ]
    with tracer.span("compliance_node", {"policy_ids": [p["id"] for p in policies]}) as rec:
        comparisons = compare_policies_to_regulation(policies, regulation)
        rec["output"] = comparisons
    return {"comparisons": comparisons}


def auditor_node(state: GraphState) -> GraphState:
    tracer: RunTracer = state["tracer"]
    regulation = state["regulation"]
    with tracer.span("auditor_node", {"comparisons": state["comparisons"]}) as rec:
        report = audit(regulation, state["comparisons"], tracer.trace_id)
        rec["output"] = report.model_dump()
    return {"report": report}


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("retriever_node", retriever_node)
    graph.add_node("compliance_node", compliance_node)
    graph.add_node("auditor_node", auditor_node)

    graph.set_entry_point("retriever_node")
    graph.add_edge("retriever_node", "compliance_node")
    graph.add_edge("compliance_node", "auditor_node")
    graph.add_edge("auditor_node", END)

    return graph.compile()


def run_compliance_check(collection, regulation: dict) -> ComplianceReport:
    tracer = RunTracer(run_name=f"compliance-check-{regulation['id']}")
    app = build_graph()
    final_state = app.invoke(
        {"collection": collection, "regulation": regulation, "tracer": tracer}
    )
    report: ComplianceReport = final_state["report"]
    tracer.finish(report.model_dump())
    return report, tracer.trace_file
