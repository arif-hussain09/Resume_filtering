"""Education scoring.

The original used plain substring matching: a requirement like
"Bachelor's degree in Computer Science" could never match
"Bachelor of Technology Computer Science ...", so strong candidates
scored 0/100. This version scores by degree LEVEL (bachelor / master /
phd) plus a fuzzy check on the field of study.
"""

from __future__ import annotations

from rapidfuzz.fuzz import token_set_ratio

from app.schemas.resume import Education

# Ordered from highest to lowest; the number is the level value.
DEGREE_LEVELS: list[tuple[str, float]] = [
    ("phd", 4.0),
    ("ph.d", 4.0),
    ("doctorate", 4.0),
    ("doctoral", 4.0),
    ("postdoc", 4.5),
    ("master", 3.0),
    ("msc", 3.0),
    ("m.sc", 3.0),
    ("mtech", 3.0),
    ("m.tech", 3.0),
    ("m.s.", 3.0),
    ("mba", 3.0),
    ("postgraduate", 3.0),
    ("bachelor", 2.0),
    ("btech", 2.0),
    ("b.tech", 2.0),
    ("bsc", 2.0),
    ("b.sc", 2.0),
    ("b.s.", 2.0),
    ("ba", 2.0),
    ("undergraduate", 2.0),
    ("diploma", 1.0),
]

FIELD_MATCH_THRESHOLD = 60.0  # token_set_ratio, 0-100


def normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def degree_level(text: str) -> float:
    """Highest degree level mentioned in a text (0 if none recognized)."""
    lowered = normalize(text)
    level = 0.0
    for keyword, value in DEGREE_LEVELS:
        if keyword in lowered:
            level = max(level, value)
    return level


def _candidate_text(education: list[Education]) -> str:
    return " ".join(
        normalize(
            f"{item.degree} {item.field or ''} {item.institution}"
        )
        for item in education
    )


def _score_single_requirement(
    requirement: str,
    education: list[Education],
    candidate_text: str,
) -> float:
    """Score one education requirement, 0-100."""

    required_level = degree_level(requirement)
    candidate_level = degree_level(candidate_text)

    if required_level > 0:
        if candidate_level >= required_level:
            score = 100.0
        elif candidate_level > 0:
            # Partial credit for a lower degree, proportional to level gap.
            score = (candidate_level / required_level) * 100.0
        else:
            score = 0.0
    else:
        # No recognizable degree level -- fall back to fuzzy text match
        # against the candidate's full education text.
        ratio = token_set_ratio(
            normalize(requirement),
            candidate_text,
        )
        score = 100.0 if ratio >= FIELD_MATCH_THRESHOLD else ratio

    # Field-of-study check: if the requirement names a field and the
    # candidate's education does not mention it, cap the credit.
    field_keywords = _field_keywords(requirement)
    if field_keywords and required_level > 0:
        if not any(
            token_set_ratio(field, candidate_text) >= FIELD_MATCH_THRESHOLD
            for field in field_keywords
        ):
            score = min(score, 50.0)

    return score


def _field_keywords(requirement: str) -> list[str]:
    """Extract likely fields of study from an education requirement."""
    known_fields = [
        "computer science",
        "mathematics",
        "statistics",
        "physics",
        "engineering",
        "electronics",
        "information technology",
        "data science",
        "economics",
        "business",
    ]
    lowered = normalize(requirement)
    return [field for field in known_fields if field in lowered]


def calculate_education_score(
    requirements: list[str],
    education: list[Education],
) -> float:

    if not requirements:
        # With dynamic weights an empty category is dropped entirely,
        # so this value never inflates the overall score.
        return 100.0

    if not education:
        return 0.0

    candidate_text = _candidate_text(education)

    total = sum(
        _score_single_requirement(requirement, education, candidate_text)
        for requirement in requirements
    )

    return round(total / len(requirements), 2)
