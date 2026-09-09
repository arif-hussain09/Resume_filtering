from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it."""
    return SentenceTransformer(MODEL_NAME)


def semantic_similarity(text1: str, text2: str) -> float:
    model = get_embedding_model()

    embeddings = model.encode(
        [text1, text2],
        normalize_embeddings=True,
    )

    score = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]],
    )[0][0]

    return float(score)