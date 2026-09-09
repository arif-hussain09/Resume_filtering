from app.services.evaluation_service import evaluate_candidate

from conftest import make_job, make_resume


def test_evaluate_candidate(deterministic_semantics):
    result = evaluate_candidate(job=make_job(), resume=make_resume())

    print("\n========== EVALUATION ==========")
    print(f"Candidate: {result.candidate_name}")
    print(f"Overall Score: {result.score.overall_score:.2f}")
    print(f"Weights: {result.score.weights_used}")
    print("\nMatched:")
    for match in result.matched_requirements:
        print(f"  + {match.requirement} ({match.score_contribution})")
    print("\nMissing:")
    for match in result.missing_requirements:
        print(f"  - {match.requirement}")

    assert result.candidate_name == "Test Candidate"

    # 3/5 requirements matched with deterministic stub semantics
    assert len(result.matched_requirements) == 3
    assert len(result.missing_requirements) == 2

    # required: Python + PyTorch matched, SQL missing -> 2/3 = 66.67
    assert result.score.required_score == 66.67

    # missing requirements carry no evidence and no matched_text
    for match in result.missing_requirements:
        assert match.matched_text is None
        assert match.evidence == []

    # recommendations are produced
    assert result.recommendations, "recommendations should be generated"

    # matched requirements carry evidence
    for match in result.matched_requirements:
        assert match.evidence
        assert match.matched_text


def test_evaluate_candidate_ranking_order(deterministic_semantics):
    from app.schemas.resume import ResumeProfile

    strong = ResumeProfile(
        name="Strong",
        skills=["Python", "PyTorch", "SQL", "Docker", "AWS"],
    )
    weak = ResumeProfile(name="Weak", skills=["COBOL"])

    strong_eval = evaluate_candidate(job=make_job(), resume=strong)
    weak_eval = evaluate_candidate(job=make_job(), resume=weak)

    assert strong_eval.score.overall_score > weak_eval.score.overall_score
    assert weak_eval.score.overall_score == 0.0
