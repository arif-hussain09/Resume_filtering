from app.schemas.resume import ResumeProfile
from app.matching.aliases import canonicalize
from app.matching.matcher import match_requirements, fuzzy_similarity

from conftest import make_job, make_resume


def test_exact_and_semantic_matching(deterministic_semantics):
    job = make_job()
    resume = ResumeProfile(
        name="Test Candidate",
        skills=["Python", "MySQL", "neural network modeling"],
    )

    results = match_requirements(job=job, resume=resume)

    by_name = {r.requirement: r for r in results}

    # exact
    assert by_name["Python"].status == "matched"
    assert by_name["Python"].match_type == "exact"
    assert by_name["Python"].similarity_score == 1.0

    # alias exact: SQL requirement vs MySQL skill -> canonical "sql"
    assert by_name["SQL"].status == "matched"
    assert by_name["SQL"].match_type == "exact"

    # missing requirements must NOT carry a matched_text
    for result in results:
        if result.status == "missing":
            assert result.matched_text is None
            assert result.similarity_score == 0.0
            assert result.evidence == []


def test_aliases_resolve_common_equivalents():
    assert canonicalize("MySQL") == canonicalize("SQL")
    assert canonicalize("K8s") == canonicalize("Kubernetes")
    assert canonicalize("ML") == canonicalize("Machine Learning")
    assert canonicalize("JS") == canonicalize("JavaScript")
    assert canonicalize("PyTorch") != canonicalize("SQL")


def test_missing_requirement_is_clean(deterministic_semantics):
    job = make_job()
    resume = ResumeProfile(name="Empty", skills=["COBOL"])

    results = match_requirements(job=job, resume=resume)

    for result in results:
        assert result.status == "missing"
        assert result.matched_text is None
        assert result.similarity_score == 0.0


def test_evidence_attached_to_matches(deterministic_semantics):
    resume = make_resume()
    results = match_requirements(job=make_job(), resume=resume)

    matched = [r for r in results if r.status == "matched"]
    assert matched
    for result in matched:
        assert result.evidence, "matched requirements must carry evidence"
        assert result.evidence[0].text


def test_fuzzy_similarity_basics():
    assert fuzzy_similarity("Python", "python") == 1.0
    assert fuzzy_similarity("PostgreSQL", "Postgres") > 0.7
    assert fuzzy_similarity("Python", "Kubernetes") < 0.4
