"""High-level candidate evaluation: match + score + recommend."""

from __future__ import annotations

from app.matching.matcher import match_requirements
from app.schemas.evaluation import CandidateEvaluation, Recommendation
from app.schemas.jobs import JobProfile
from app.schemas.resume import ResumeProfile
from app.scoring.education import calculate_education_score
from app.scoring.experience import calculate_experience_score
from app.scoring.scorer import calculate_score

MAX_RECOMMENDATIONS = 5


def build_recommendations(
    job: JobProfile,
    evaluation_matches: list,
    experience_score: float,
    education_score: float,
) -> list[Recommendation]:
    """Simple rule-based, actionable recommendations."""

    recommendations: list[Recommendation] = []

    missing_required = [
        match for match in evaluation_matches
        if match.status == "missing" and match.requirement_importance == "required"
    ]
    if missing_required:
        names = ", ".join(match.requirement for match in missing_required[:4])
        recommendations.append(
            Recommendation(
                area="Required skills",
                suggestion=(
                    f"No evidence found for required: {names}. "
                    "Consider adding these skills to the resume or "
                    "screening them out."
                ),
            )
        )

    partial = [
        match for match in evaluation_matches if match.status == "partial"
    ]
    if partial:
        names = ", ".join(match.requirement for match in partial[:4])
        recommendations.append(
            Recommendation(
                area="Partial matches",
                suggestion=(
                    f"Only weak evidence for: {names}. Ask the candidate "
                    "to clarify depth of experience in these areas."
                ),
            )
        )

    if experience_score < 60:
        recommendations.append(
            Recommendation(
                area="Experience",
                suggestion=(
                    "Reported experience falls short of the stated "
                    "minimum. Check project depth as compensation."
                ),
            )
        )

    if education_score < 60:
        recommendations.append(
            Recommendation(
                area="Education",
                suggestion=(
                    "Education does not clearly meet the stated "
                    "requirement. Verify degree level and field."
                ),
            )
        )

    return recommendations[:MAX_RECOMMENDATIONS]


def evaluate_candidate(
    job: JobProfile,
    resume: ResumeProfile,
) -> CandidateEvaluation:
    """Full evaluation of one candidate against one job."""

    matches = match_requirements(job=job, resume=resume)

    experience_score = calculate_experience_score(
        requirements=job.experience_requirements,
        experiences=resume.experience,
    )

    education_score = calculate_education_score(
        requirements=job.education_requirements,
        education=resume.education,
    )

    score = calculate_score(
        job=job,
        matches=matches,
        experience_score=experience_score,
        education_score=education_score,
    )

    return CandidateEvaluation(
        candidate_name=resume.name,
        score=score,
        matched_requirements=[
            match for match in matches if match.status == "matched"
        ],
        partial_requirements=[
            match for match in matches if match.status == "partial"
        ],
        missing_requirements=[
            match for match in matches if match.status == "missing"
        ],
        recommendations=build_recommendations(
            job,
            matches,
            experience_score,
            education_score,
        ),
    )
