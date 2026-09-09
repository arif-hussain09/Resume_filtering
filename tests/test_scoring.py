from app.schemas.evaluation import MatchResult
from app.schemas.jobs import JobProfile, Requirement, ExperienceRequirement
from app.scoring.scorer import calculate_score


def test_scoring():

    job = JobProfile(
        title="Machine Learning Engineer",

        requirements=[
            Requirement(
                name="Python",
                category="skill",
                importance="required",
            ),
            Requirement(
                name="PyTorch",
                category="skill",
                importance="required",
            ),
            Requirement(
                name="SQL",
                category="skill",
                importance="required",
            ),
            Requirement(
                name="Docker",
                category="tool",
                importance="preferred",
            ),
            Requirement(
                name="AWS",
                category="cloud",
                importance="preferred",
            ),
        ],

        experience_requirements=[
            ExperienceRequirement(
                description="Machine learning experience",
                minimum_years=2,
            )
        ],
    )

    matches = [
        MatchResult(
            requirement="Python",
            requirement_importance="required",
            status="matched",
            match_type="exact",
            similarity_score=1.0,
        ),
        MatchResult(
            requirement="PyTorch",
            requirement_importance="required",
            status="matched",
            match_type="exact",
            similarity_score=1.0,
        ),
        MatchResult(
            requirement="SQL",
            requirement_importance="required",
            status="missing",
            match_type="none",
        ),
        MatchResult(
            requirement="Docker",
            requirement_importance="preferred",
            status="matched",
            match_type="exact",
            similarity_score=1.0,
        ),
        MatchResult(
            requirement="AWS",
            requirement_importance="preferred",
            status="missing",
            match_type="none",
        ),
    ]

    result = calculate_score(
        job=job,
        matches=matches,
        experience_score=100,
        education_score=100,
    )

    print(result)

    assert round(result.overall_score, 2) == 73.33