"""Batched sentence-embedding similarity.

The original implementation encoded TWO texts per call, once per
(requirement, skill) pair -- up to 1000+ individual `model.encode()`
round-trips per resume. Here the embedding model is loaded once and
whole lists of texts are encoded in a single batch, then compared with
one matrix multiplication.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app import config


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it."""
    return SentenceTransformer(config.get_embedding_model_name())


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts and L2-normalize the vectors."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = get_embedding_model()
    return model.encode(
        list(texts),
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype(np.float32)


def similarity_matrix(requirements: list[str], evidence: list[str]) -> np.ndarray:
    """Pairwise cosine similarity, shape (len(requirements), len(evidence))."""
    if not requirements or not evidence:
        return np.zeros((len(requirements), len(evidence)), dtype=np.float32)
    req_emb = embed_texts(requirements)
    ev_emb = embed_texts(evidence)
    return req_emb @ ev_emb.T


def semantic_similarity(text1: str, text2: str) -> float:
    """Backward-compatible single-pair similarity (avoid in hot loops)."""
    emb = embed_texts([text1, text2])
    return float(emb[0] @ emb[1])
