"""
observability/tracer.py

Two layers of observability, both active at once:

1. Native LangSmith tracing (production path): if LANGCHAIN_TRACING_V2=true
   and LANGCHAIN_API_KEY are set as environment variables, LangGraph/LangChain
   trace every node run automatically to your LangSmith project. No code
   change needed beyond the env vars -- see README.md.

2. A local, dependency-free JSONL tracer (works with zero configuration).
   It records the same information LangSmith would show for each node:
   inputs, outputs, latency, and a run/trace id -- so the run is always
   auditable, and the trace_id can be embedded in the final structured
   output as the assignment requires.

Swap point: `RunTracer` is intentionally the only thing agents/graph code
talk to. If you later want Langfuse instead of the local tracer, you only
change this file.
"""

import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from config import LOCAL_TRACE_DIR, LANGSMITH_ENABLED


class RunTracer:
    def __init__(self, run_name: str = "compliance-check"):
        self.trace_id = str(uuid.uuid4())
        self.run_name = run_name
        self.spans = []
        os.makedirs(LOCAL_TRACE_DIR, exist_ok=True)
        self._path = os.path.join(LOCAL_TRACE_DIR, f"{self.trace_id}.jsonl")
        self._write_event(
            {
                "event": "trace_start",
                "trace_id": self.trace_id,
                "run_name": self.run_name,
                "langsmith_enabled": LANGSMITH_ENABLED,
                "timestamp": self._now(),
            }
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _write_event(self, event: dict) -> None:
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")

    @contextmanager
    def span(self, node_name: str, inputs: dict):
        """Wrap one LangGraph node execution and record it as a trace span."""
        start = time.time()
        span_id = str(uuid.uuid4())
        self._write_event(
            {
                "event": "node_start",
                "trace_id": self.trace_id,
                "span_id": span_id,
                "node": node_name,
                "inputs": inputs,
                "timestamp": self._now(),
            }
        )
        record = {"output": None, "error": None}
        try:
            yield record
        except Exception as exc:  # re-raise after logging
            record["error"] = str(exc)
            raise
        finally:
            self._write_event(
                {
                    "event": "node_end",
                    "trace_id": self.trace_id,
                    "span_id": span_id,
                    "node": node_name,
                    "output": record["output"],
                    "error": record["error"],
                    "latency_ms": round((time.time() - start) * 1000, 2),
                    "timestamp": self._now(),
                }
            )

    def finish(self, final_output: dict) -> None:
        self._write_event(
            {
                "event": "trace_end",
                "trace_id": self.trace_id,
                "final_output": final_output,
                "timestamp": self._now(),
            }
        )

    @property
    def trace_file(self) -> str:
        return self._path
