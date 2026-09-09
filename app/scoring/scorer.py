"""Scoring engine.

Fixes vs. the original implementation:

1. `ScoreBreakdown` fields now hold honest 0-100 percentages. The original
   silently stored weighted contributions (e.g. `required_score = 33.33`
   for a real 66.67%), which made the UI lie.
2. Category weights are dynamic: a job with no preferred requirements no
   longer hands out a free 20% -- that weight is redistributed over the
   categories that actually exist.
3. Status and score are consistent again: matched counts 1.0, partial
   counts its similarity score, missing counts 0.
4. Per-requirement `score_contribution` is computed and written back onto
   each MatchResult so the UI can explain how much each requirement
   contributed to the overall score.
"""

from __future__ import annotations

from app.schemas.evaluation import MatchResult, ScoreBreakdown
from app.schemas.jobs import JobProfile

CATEGORY_WEIGHTS = {
    "required": 0.50,
    "preferred": 0.20,
    "experience": 0.20,
    "education": 0.10,
}


def calculate_requirement_score(
    matches: list[MatchResult],
    importance: str,
) -> float:
    """Percentage score for the requirements of one importance level.

    matched -> 1.0 point, partial -> its similarity score, missing -> 0.
    """
    relevant = [
        match for match in matches if match.requirement_importance == importance
    ]
    if not relevant:
        return 0.0

    total = 0.0
    for match in relevant:
        if match.status == "matched":
            total += 1.0
        elif match.status == "partial":
            total += match.similarity_score

    return (total / len(relevant)) * 100.0


def _active_weights(
    job: JobProfile,
    has_required: bool,
    has_preferred: bool,
) -> dict[str, float]:
    """Weights for categories that actually have requirements.

    Categories without requirements are dropped and their weight is
    redistributed proportionally instead of granting free marks.
    """
    active = {
        category: weight
        for category, weight in CATEGORY_WEIGHTS.items()
        if (
            (category == "required" and has_required)
            or (category == "preferred" and has_preferred)
            or (category == "experience" and bool(job.experience_requirements))
            or (category == "education" and bool(job.education_requirements))
        )
    }
    total = sum(active.values())
    if total == 0:
        return {}
    return {category: weight / total for category, weight in active.items()}


def calculate_score(
    job: JobProfile,
    matches: list[MatchResult],
    experience_score: float = 0.0,
    education_score: float = 0.0,
) -> ScoreBreakdown:
    """Compute the overall score and write contributions back to matches."""

    required_score = calculate_requirement_score(matches, "required")
    preferred_score = calculate_requirement_score(matches, "preferred")

    has_required = any(
        match.requirement_importance == "required" for match in matches
    )
    has_preferred = any(
        match.requirement_importance == "preferred" for match in matches
    )

    weights = _active_weights(job, has_required, has_preferred)

    overall_score = 0.0
    if weights:
        overall_score = (
            required_score * weights.get("required", 0.0)
            + preferred_score * weights.get("preferred", 0.0)
            + experience_score * weights.get("experience", 0.0)
            + education_score * weights.get("education", 0.0)
        )

    _write_contributions(
        matches,
        weights,
        required_score,
        preferred_score,
    )

    return ScoreBreakdown(
        required_score=round(required_score, 2),
        preferred_score=round(preferred_score, 2),
        experience_score=round(experience_score, 2),
        education_score=round(education_score, 2),
        overall_score=round(overall_score, 2),
        weights_used=weights,
    )


def _write_contributions(
    matches: list[MatchResult],
    weights: dict[str, float],
    required_pct: float,
    preferred_pct: float,
) -> None:
    """Attach each requirement's share of the overall score to the MatchResult.

    contribution = (points / category total) * category percentage * weight,
    so the sum of all contributions equals the requirement categories'
    share of the overall score.
    """
    weight_required = weights.get("required", 0.0)
    weight_preferred = weights.get("preferred", 0.0)

    required_points = sum(
        1.0 if m.status == "matched" else (m.similarity_score if m.status == "partial" else 0.0)
        for m in matches
        if m.requirement_importance == "required"
    )
    preferred_points = sum(
        1.0 if m.status == "matched" else (m.similarity_score if m.status == "partial" else 0.0)
        for m in matches
        if m.requirement_importance == "preferred"
    )

    for match in matches:
        points = (
            1.0
            if match.status == "matched"
            else (match.similarity_score if match.status == "partial" else 0.0)
        )
        if match.requirement_importance == "required":
            share = points / required_points if required_points else 0.0
            match.score_contribution = round(
                share * required_pct * weight_required, 2
            )
        else:
            share = points / preferred_points if preferred_points else 0.0
            match.score_contribution = round(
                share * preferred_pct * weight_preferred, 2
            )
