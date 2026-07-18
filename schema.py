"""
schema.py
Structured output contract. Using Pydantic instead of "ask the LLM to
return JSON" guarantees the final output always matches this shape,
matching the assignment's Expected Output section.
"""

from typing import List
from pydantic import BaseModel, Field


class ConflictingPolicy(BaseModel):
    policy_id: str
    reason: str


class ComplianceReport(BaseModel):
    target_regulation: str
    conflict_detected: bool
    conflicting_policies: List[ConflictingPolicy] = Field(default_factory=list)
    recommended_action: str
    trace_id: str
