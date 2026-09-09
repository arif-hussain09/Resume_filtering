"""End-to-end pipeline tests with injected LLM profiles (no Groq calls)."""

from app.pipeline import run_batch, run_pipeline

from conftest import SAMPLE_JOB_PDF, SAMPLE_RESUME_PDF, make_job, make_resume


def test_run_pipeline_with_injected_profiles(deterministic_semantics):
    result = run_pipeline(
        job_pdf=SAMPLE_JOB_PDF,
        resume_pdf=SAMPLE_RESUME_PDF,
        job_profile=make_job(),
        resume_profile=make_resume(),
    )

    assert result.error is None, f"pipeline failed: {result.error}"
    assert result.evaluation is not None
    assert result.evaluation.candidate_name == "Test Candidate"
    assert result.highlight is not None
    assert result.highlight.pdf_bytes[:4] == b"%PDF"
    assert result.html_evidence
    assert result.timings


def test_run_batch_reuses_job_profile(deterministic_semantics):
    results = run_batch(
        job_pdf=SAMPLE_JOB_PDF,
        resume_pdfs=[SAMPLE_RESUME_PDF, SAMPLE_RESUME_PDF],
        job_profile=make_job(),
        resume_profiles=[make_resume(), make_resume()],
    )

    assert len(results) == 2
    assert all(r.error is None for r in results)


def test_run_pipeline_isolates_bad_files(deterministic_semantics):
    """One broken file must not kill the batch (original had no error handling)."""
    from app.schemas.resume import ResumeProfile

    missing_profile: ResumeProfile | None = None

    result = run_pipeline(
        job_pdf=SAMPLE_JOB_PDF,
        resume_pdf="data/resumes/does_not_exist.pdf",
        job_profile=make_job(),
        resume_profile=missing_profile,
    )

    assert result.error is not None
    assert "FileNotFoundError" in result.error or "not found" in result.error.lower()
    assert result.evaluation is None


def test_progress_callback_fires(deterministic_semantics):
    stages: list[str] = []

    def progress(stage: str, fraction: float) -> None:
        stages.append(stage)

    run_pipeline(
        job_pdf=SAMPLE_JOB_PDF,
        resume_pdf=SAMPLE_RESUME_PDF,
        job_profile=make_job(),
        resume_profile=make_resume(),
        progress=progress,
    )

    assert stages, "progress callback was never called"
    assert any("Done" in s for s in stages)
