from app.evidence.highlighter import (
    build_html_evidence_view,
    highlight_resume,
)
from app.schemas.evaluation import CandidateEvaluation, MatchResult
from app.schemas.resume import ResumeProfile
from app.services.evaluation_service import evaluate_candidate

from conftest import SAMPLE_RESUME_PDF, make_job


def _evaluation_with_real_matches(deterministic_semantics) -> CandidateEvaluation:
    """Use the real sample resume profile so needles exist in the PDF."""
    resume = ResumeProfile(
        name="Arif Hussain",
        skills=[
            "Python",
            "C",
            "OpenCV",
            "MediaPipe",
            "LangChain",
            "LangGraph",
        ],
        experience=[],
        education=[],
        projects=[],
    )
    job = make_job()
    # requirement names that actually appear in the sample resume
    job.requirements = [
        type(job.requirements[0])(name="Python", category="skill", importance="required"),
        type(job.requirements[0])(name="Docker", category="tool", importance="preferred"),
    ]
    return evaluate_candidate(job=job, resume=resume)


def test_highlight_resume_produces_annotations(deterministic_semantics):
    evaluation = _evaluation_with_real_matches(deterministic_semantics)

    result = highlight_resume(SAMPLE_RESUME_PDF, evaluation)

    assert result.pdf_bytes[:4] == b"%PDF"
    assert result.total_highlights > 0
    assert any(page.highlight_count for page in result.pages)

    # evidence got page numbers and coordinates
    matched = evaluation.matched_requirements
    assert matched
    for match in matched:
        for evidence in match.evidence:
            if match.status == "matched" and match.matched_text == "Python":
                assert evidence.page_number is not None
                assert evidence.locations
                location = evidence.locations[0]
                assert 0 <= location.x0 <= 1000
                assert 0 <= location.y0 <= 1000


def test_highlighted_pdf_has_more_pages_than_original():
    """A summary page is appended."""
    import fitz

    from app.schemas.evaluation import ScoreBreakdown

    evaluation = CandidateEvaluation(
        candidate_name="Nobody",
        score=ScoreBreakdown(overall_score=0),
        missing_requirements=[
            MatchResult(
                requirement="Python",
                requirement_importance="required",
                status="missing",
                match_type="none",
            )
        ],
    )

    result = highlight_resume(SAMPLE_RESUME_PDF, evaluation)

    original = fitz.open(SAMPLE_RESUME_PDF)
    annotated = fitz.open(stream=result.pdf_bytes, filetype="pdf")
    assert len(annotated) == len(original) + 1
    original.close()
    annotated.close()


def test_html_evidence_view_contains_marks(deterministic_semantics):
    evaluation = _evaluation_with_real_matches(deterministic_semantics)
    result = highlight_resume(SAMPLE_RESUME_PDF, evaluation)
    html = build_html_evidence_view(result)

    assert "<mark" in html
    assert "Page 1" in html
    assert "Python" in html
    # HTML-escaped content must not contain raw tag injection
    assert "<script" not in html
