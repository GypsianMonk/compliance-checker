"""
chroma_store.py

Builds an in-memory ChromaDB collection from policies.json and exposes
a similarity-search helper the Retriever agent uses.
"""

import json
from typing import List, TypedDict

import chromadb

from config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, POLICIES_PATH
from vectorstore.embeddings import get_embedding_function


class PolicyMatch(TypedDict):
    id: str
    section: str
    text: str
    distance: float


def load_policies(path: str = POLICIES_PATH) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_collection():
    """Creates (or resets) an in-memory Chroma collection with all policies."""
    client = (
        chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        if CHROMA_PERSIST_DIR
        else chromadb.EphemeralClient()
    )

    # Start clean each run so re-running the script is idempotent.
    try:
        client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )

    policies = load_policies()
    collection.add(
        ids=[p["id"] for p in policies],
        documents=[p["text"] for p in policies],
        metadatas=[{"section": p["section"]} for p in policies],
    )
    return collection


def search_policies(collection, query: str, top_k: int = 3) -> List[PolicyMatch]:
    """Returns the top_k most semantically similar policies to `query`."""
    results = collection.query(query_texts=[query], n_results=top_k)

    matches: List[PolicyMatch] = []
    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    for i in range(len(ids)):
        matches.append(
            PolicyMatch(
                id=ids[i],
                section=metas[i].get("section", ""),
                text=docs[i],
                distance=dists[i],
            )
        )
    return matches
