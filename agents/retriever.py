"""
agents/retriever.py
Step 1 of the graph: given a regulation, semantically search the Chroma
collection for the policies most likely to be relevant, using the
regulation's own mandate text as the query.
"""

from typing import List

from vectorstore.chroma_store import search_policies, PolicyMatch

# Rather than an absolute distance threshold (hard to tune across
# embedding backends), we keep the best match plus any other match
# within RELATIVE_MARGIN of it. This correctly narrows down to just
# the truly relevant policy/policies for a regulation, instead of
# passing every policy in the store to the (more expensive) Compliance
# Analyzer step -- while still surfacing genuine near-ties.
RELATIVE_MARGIN = 0.08


def retrieve_relevant_policies(
    collection, regulation_text: str, top_k: int = 3
) -> List[PolicyMatch]:
    matches = search_policies(collection, regulation_text, top_k=top_k)
    if not matches:
        return []
    best_distance = matches[0]["distance"]
    return [m for m in matches if m["distance"] <= best_distance + RELATIVE_MARGIN]
