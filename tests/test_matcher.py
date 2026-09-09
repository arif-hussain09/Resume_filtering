# from app.schemas.jobs import JobProfile, Requirement
# from app.schemas.resume import ResumeProfile
# from app.matching.matcher import match_requirements


# def test_match_requirements():

#     job = JobProfile(
#         title="Machine Learning Engineer",
#         requirements=[
#             Requirement(
#                 name="Python",
#                 category="skill",
#                 importance="required",
#             ),
#             Requirement(
#                 name="PyTorch",
#                 category="framework",
#                 importance="required",
#             ),
#             Requirement(
#                 name="SQL",
#                 category="skill",
#                 importance="required",
#             ),
#             Requirement(
#                 name="Docker",
#                 category="tool",
#                 importance="preferred",
#             ),
#         ],
#     )

#     resume = ResumeProfile(
#         name="Test Candidate",
#         skills=[
#             "Python",
#             "PyTorch",
#             "Docker",
#         ],
#     )

#     results = match_requirements(job, resume)

#     assert len(results) == 4

#     assert results[0].status == "matched"
#     assert results[1].status == "matched"
#     assert results[2].status == "missing"
#     assert results[3].status == "matched"

## ----- Update the test to include experience and education requirements -----
from app.schemas.jobs import JobProfile, Requirement
from app.schemas.resume import ResumeProfile
from app.matching.matcher import match_requirements


def test_exact_and_semantic_matching():

    job = JobProfile(
        title="Machine Learning Engineer",
        requirements=[
            Requirement(
                name="Python",
                category="skill",
                importance="required",
            ),
            Requirement(
                name="Deep Learning",
                category="skill",
                importance="required",
            ),
            Requirement(
                name="SQL",
                category="skill",
                importance="required",
            ),
        ],
    )

    resume = ResumeProfile(
        name="Test Candidate",
        skills=[
            "Python",
            "neural network modeling",
        ],
    )

    results = match_requirements(
        job=job,
        resume=resume,
    )

    for result in results:
        print(
            result.requirement,
            result.status,
            result.match_type,
            result.similarity_score,
        )

    assert results[0].status == "matched"
    assert results[0].match_type == "exact"

    assert results[1].status in {"matched", "partial"}

    assert results[2].status == "missing"