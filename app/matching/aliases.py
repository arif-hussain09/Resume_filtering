"""Skill / term normalization map.

Job descriptions and resumes name the same technology in many ways
("SQL" vs "MySQL", "K8s" vs "Kubernetes", "ML" vs "Machine Learning").
Canonicalizing both sides before matching turns many weak fuzzy/semantic
matches into exact matches, which is both faster and more explainable.
"""

from __future__ import annotations

CANONICAL_TERMS: dict[str, str] = {
    # databases / query languages
    "sql": "sql",
    "mysql": "sql",
    "postgresql": "sql",
    "postgres": "sql",
    "sqlite": "sql",
    "pl/sql": "sql",
    "t-sql": "sql",
    # languages
    "javascript": "javascript",
    "js": "javascript",
    "ecmascript": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "python": "python",
    "python3": "python",
    "golang": "golang",
    "go": "golang",
    "c++": "c++",
    "cpp": "c++",
    "c#": "c#",
    "csharp": "c#",
    # infra / cloud
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "docker": "docker",
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "azure": "azure",
    "microsoft azure": "azure",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    # ML / AI
    "machine learning": "machine learning",
    "ml": "machine learning",
    "deep learning": "deep learning",
    "dl": "deep learning",
    "neural networks": "deep learning",
    "natural language processing": "nlp",
    "nlp": "nlp",
    "computer vision": "computer vision",
    "cv": "computer vision",
    "llm": "llms",
    "llms": "llms",
    "large language models": "llms",
    "generative ai": "generative ai",
    "genai": "generative ai",
    "gen ai": "generative ai",
    "pytorch": "pytorch",
    "torch": "pytorch",
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "langchain": "langchain",
    "langgraph": "langgraph",
    "rag": "rag",
    "retrieval augmented generation": "rag",
    # web
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "rest": "rest apis",
    "rest api": "rest apis",
    "rest apis": "rest apis",
    "graphql": "graphql",
    # education shorthand
    "computer science": "computer science",
    "cs": "computer science",
    "btech": "btech",
    "b.tech": "btech",
    "bachelor of technology": "btech",
}


def canonicalize(text: str) -> str:
    """Lowercase, collapse whitespace and map aliases to a canonical term."""
    key = " ".join((text or "").lower().strip().split())
    return CANONICAL_TERMS.get(key, key)
