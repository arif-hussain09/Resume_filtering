from app.scoring.education import calculate_education_score, degree_level
from app.scoring.experience import calculate_experience_score
from app.schemas.jobs import ExperienceRequirement
from app.schemas.resume import Education, Experience


def make_education() -> list[Education]:
    return [
        Education(
            degree="Bachelor of Technology",
            institution="DTU",
            field="Mathematics and Computer Science",
        )
    ]


def test_btech_matches_bachelors_requirement():
    """The original substring matcher scored this 0; must now be high."""
    score = calculate_education_score(
        requirements=["Bachelor's degree in Computer Science"],
        education=make_education(),
    )
    assert score >= 80.0


def test_lower_degree_gets_partial_credit():
    score = calculate_education_score(
        requirements=["Master's degree in Computer Science"],
        education=make_education(),
    )
    assert 0.0 < score < 100.0  # has bachelor, needs master


def test_phd_beats_bachelor_requirement():
    phd = [
        Education(degree="PhD", institution="MIT", field="Computer Science")
    ]
    score = calculate_education_score(
        requirements=["Bachelor's degree"], education=phd
    )
    assert score == 100.0


def test_no_education_scores_zero():
    score = calculate_education_score(
        requirements=["Bachelor's degree"], education=[]
    )
    assert score == 0.0


def test_degree_level_detection():
    assert degree_level("PhD in Physics") == 4.0
    assert degree_level("M.Tech") == 3.0
    assert degree_level("BSc") == 2.0
    assert degree_level("no degree here") == 0.0


# --------------------------------------------------------------------------
# Experience
# --------------------------------------------------------------------------


def test_experience_met():
    reqs = [ExperienceRequirement(description="ML", minimum_years=2)]
    exps = [Experience(company="A", role="ML Eng", duration_years=3)]
    assert calculate_experience_score(reqs, exps) == 100.0


def test_experience_partial():
    reqs = [ExperienceRequirement(description="ML", minimum_years=4)]
    exps = [Experience(company="A", role="ML Eng", duration_years=1)]
    assert calculate_experience_score(reqs, exps) == 25.0


def test_unparsed_durations_get_partial_credit_not_zero():
    """LLM could not parse dates -> documented 50% credit, not a hard 0."""
    reqs = [ExperienceRequirement(description="ML", minimum_years=3)]
    exps = [
        Experience(company="A", role="ML Eng", duration_years=None),
        Experience(company="B", role="DS", duration_years=None),
    ]
    assert calculate_experience_score(reqs, exps) == 50.0
