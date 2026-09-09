from app.schemas.evaluation import MatchResult
from app.schemas.jobs import JobProfile, Requirement, ExperienceRequirement
from app.scoring.scorer import calculate_score, calculate_requirement_score

from conftest import make_job


def _matches(
    statuses: list[tuple[str, str, str, float]],
) -> list[MatchResult]:
    return [
        MatchResult(
            requirement=name,
            requirement_importance=importance,
            status=status,
            match_type="exact" if status == "matched" else "none",
            similarity_score=score,
        )
        for name, importance, status, score in statuses
    ]


def test_honest_percentage_fields():
    """ScoreBreakdown fields must be 0-100 percentages, not weighted parts."""
    job = JobProfile(
        title="ML Engineer",
        requirements=[
            Requirement(name="Python", category="skill", importance="required"),
            Requirement(name="PyTorch", category="skill", importance="required"),
            Requirement(name="SQL", category="skill", importance="required"),
            Requirement(name="Docker", category="tool", importance="preferred"),
            Requirement(name="AWS", category="cloud", importance="preferred"),
        ],
        experience_requirements=[
            ExperienceRequirement(description="ML experience", minimum_years=2)
        ],
    )

    matches = _matches(
        [
            ("Python", "required", "matched", 1.0),
            ("PyTorch", "required", "matched", 1.0),
            ("SQL", "required", "missing", 0.0),
            ("Docker", "preferred", "matched", 1.0),
            ("AWS", "preferred", "missing", 0.0),
        ]
    )

    result = calculate_score(
        job=job, matches=matches, experience_score=100, education_score=100
    )

    # honest percentages
    assert result.required_score == 66.67  # 2/3 matched
    assert result.preferred_score == 50.0  # 1/2 matched

    # overall = weighted mean of active categories
    # weights: required .5, preferred .2, experience .2 -> normalized to .9
    expected_overall = (
        66.6666 * 0.5 / 0.9 + 50.0 * 0.2 / 0.9 + 100.0 * 0.2 / 0.9
    )
    assert abs(result.overall_score - expected_overall) < 0.05


def test_empty_preferred_grants_no_free_marks():
    """A job with no preferred requirements must not hand out free 20%."""

    job = JobProfile(
        title="Dev",
        requirements=[
            Requirement(name="Python", category="skill", importance="required"),
        ],
    )
    matches = _matches([("Python", "required", "missing", 0.0)])

    result = calculate_score(
        job=job, matches=matches, experience_score=0, education_score=0
    )

    assert result.overall_score == 0.0
    assert "preferred" not in result.weights_used


def test_degenerate_job_scores_zero():
    result = calculate_score(job=JobProfile(title="x"), matches=[])
    assert result.overall_score == 0.0


def test_partial_counts_by_similarity():
    matches = _matches(
        [
            ("Python", "required", "matched", 1.0),
            ("SQL", "required", "partial", 0.62),
            ("Rust", "required", "missing", 0.0),
        ]
    )
    score = calculate_requirement_score(matches, "required")
    assert abs(score - ((1.0 + 0.62) / 3) * 100) < 0.01


def test_contributions_written_back():
    job = make_job()
    matches = _matches(
        [
            ("Python", "required", "matched", 1.0),
            ("PyTorch", "required", "matched", 1.0),
            ("SQL", "required", "missing", 0.0),
            ("Docker", "preferred", "matched", 1.0),
            ("AWS", "preferred", "missing", 0.0),
        ]
    )
    result = calculate_score(
        job=job, matches=matches, experience_score=100, education_score=100
    )

    contributions = [m.score_contribution for m in matches]
    assert all(c >= 0 for c in contributions)
    total = sum(contributions)
    expected = result.required_score * result.weights_used.get("required", 0) + \
        result.preferred_score * result.weights_used.get("preferred", 0)
    assert abs(total - expected) < 0.5
    # missing requirements contribute nothing
    for m in matches:
        if m.status == "missing":
            assert m.score_contribution == 0.0
