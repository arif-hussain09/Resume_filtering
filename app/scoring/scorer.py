from app.schemas.evaluation import MatchResult, ScoreBreakdown
from app.schemas.jobs import JobProfile


REQUIRED_WEIGHT = 0.50
PREFERRED_WEIGHT = 0.20
EXPERIENCE_WEIGHT = 0.20
EDUCATION_WEIGHT = 0.10


# def calculate_requirement_score(
#     matches: list[MatchResult],
#     importance: str,
# ) -> float:
#     """
#     Calculate the percentage score for required/preferred requirements.

#     matched  = 1.0
#     partial  = 0.5
#     missing  = 0.0
#     """

#     relevant_matches = [
#         match
#         for match in matches
#         if match.requirement_importance == importance
#     ]

#     if not relevant_matches:
#         return 100.0

#     total = 0.0

#     for match in relevant_matches:
#         if match.status == "matched":
#             total += 1.0
#         elif match.status == "partial":
#             total += 0.5

#     return (total / len(relevant_matches)) * 100

## ---- update  requirement scoring ----

def calculate_requirement_score(
    matches: list[MatchResult],
    importance: str,
) -> float:
    relevant_matches = [
        match
        for match in matches
        if match.requirement_importance == importance
    ]

    if not relevant_matches:
        return 100.0

    total = sum(
        match.similarity_score
        for match in relevant_matches
    )

    return (total / len(relevant_matches)) * 100


def calculate_score(
    job: JobProfile,
    matches: list[MatchResult],
    experience_score: float = 0.0,
    education_score: float = 0.0,
) -> ScoreBreakdown:

    required_score = calculate_requirement_score(
        matches,
        "required",
    )

    preferred_score = calculate_requirement_score(
        matches,
        "preferred",
    )

    overall_score = (
        required_score * REQUIRED_WEIGHT
        + preferred_score * PREFERRED_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
        + education_score * EDUCATION_WEIGHT
    )

    return ScoreBreakdown(
        required_score=required_score * REQUIRED_WEIGHT,
        preferred_score=preferred_score * PREFERRED_WEIGHT,
        experience_score=experience_score * EXPERIENCE_WEIGHT,
        education_score=education_score * EDUCATION_WEIGHT,
        overall_score=overall_score,
    )