from app.schemas.jobs import JobProfile, Requirement
from app.schemas.resume import ResumeProfile
from app.services.evaluation_service import evaluate_candidate
from app.schemas.resume import Experience, Education


def test_evaluate_candidate():

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
                category="framework",
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
    )

    resume = ResumeProfile(
        name="Test Candidate",

        skills=[
            "Python",
            "PyTorch",
            "Docker",
        ],

        experience=[
            Experience(
                company="ABC AI",
                role="ML Engineer",
                duration_years=3,
            )
        ],

        education=[
            Education(
                degree="Bachelor of Technology",
                institution="DTU",
                field="Computer Science",
            )
        ],
    )
    result = evaluate_candidate(job = job, resume = resume)

    print("\n========== EVALUATION ==========")
    print(f"Candidate: {result.candidate_name}")
    print(f"Overall Score: {result.score.overall_score:.2f}")

    print("\nMatched:")
    for match in result.matched_requirements:
        print(f"  ✓ {match.requirement}")

    print("\nMissing:")
    for match in result.missing_requirements:
        print(f"  ✗ {match.requirement}")

    assert result.candidate_name == "Test Candidate"
    assert round(result.score.overall_score, 2) == 73.33
    assert len(result.matched_requirements) == 3
    assert len(result.missing_requirements) == 2