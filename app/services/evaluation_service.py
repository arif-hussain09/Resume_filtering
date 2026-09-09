from app.matching.matcher import match_requirements
from app.schemas.evaluation import CandidateEvaluation
from app.schemas.jobs import JobProfile
from app.schemas.resume import ResumeProfile
from app.scoring.scorer import calculate_score
from app.scoring.education import calculate_education_score
from app.scoring.experience import calculate_experience_score


def evaluate_candidate(
    job: JobProfile,
    resume: ResumeProfile,
) -> CandidateEvaluation:

    matches = match_requirements(
        job=job,
        resume=resume,
    )

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
            match for match in matches
            if match.status == "matched"
        ],
        partial_requirements=[
            match for match in matches
            if match.status == "partial"
        ],
        missing_requirements=[
            match for match in matches
            if match.status == "missing"
        ],
    )