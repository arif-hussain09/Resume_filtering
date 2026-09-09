"""The end-to-end pipeline.

Replaces the LangGraph workflow. The original graph was strictly linear
(parse -> extract -> match -> score, no branching, no loops, no
parallelism, no human-in-the-loop) and -- more importantly -- it crashed
at import time because nodes.py imported a `build_evaluation` function
that never existed. A plain function chain with per-stage error
handling does the same job with far less machinery.

LLM profiles can be injected for testing/caching: pass `job_profile`
and/or `resume_profile` to skip the Groq calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from app.evidence.highlighter import (
    HighlightResult,
    build_html_evidence_view,
    highlight_resume,
)
from app.extraction.job_extractor import extract_job_profile
from app.extraction.resume_extractor import extract_resume_profile
from app.ingestion.pdf_parser import extract_pdf_pages
from app.schemas.evaluation import CandidateEvaluation
from app.schemas.jobs import JobProfile
from app.schemas.resume import ResumeProfile
from app.services.evaluation_service import evaluate_candidate


@dataclass
class CandidateResult:
    """Everything the UI needs for one resume."""

    resume_path: str
    candidate_name: str = ""
    evaluation: CandidateEvaluation | None = None
    highlight: HighlightResult | None = None
    html_evidence: str | None = None
    error: str | None = None
    timings: dict[str, float] = field(default_factory=dict)


def analyze_job(job_pdf: str | Path) -> JobProfile:
    """Parse the JD PDF and extract a JobProfile via the LLM."""
    pages = extract_pdf_pages(job_pdf)
    text = "\n".join(page["text"] for page in pages)
    if not text.strip():
        raise ValueError(
            f"No text layer found in {job_pdf}. Scanned/image PDFs are not "
            "supported yet (OCR is on the roadmap)."
        )
    return extract_job_profile(text)


def analyze_resume(resume_pdf: str | Path) -> ResumeProfile:
    """Parse the resume PDF and extract a ResumeProfile via the LLM."""
    pages = extract_pdf_pages(resume_pdf)
    text = "\n".join(page["text"] for page in pages)
    if not text.strip():
        raise ValueError(
            f"No text layer found in {resume_pdf}. Scanned/image PDFs are not "
            "supported yet (OCR is on the roadmap)."
        )
    return extract_resume_profile(text)


def run_pipeline(
    job_pdf: str | Path,
    resume_pdf: str | Path,
    job_profile: JobProfile | None = None,
    resume_profile: ResumeProfile | None = None,
    progress: Callable[[str, float], None] | None = None,
) -> CandidateResult:
    """Run the full pipeline for ONE candidate.

    `progress(stage_name, fraction)` is an optional callback used by the
    Streamlit UI to render live status.
    """

    import time

    timings: dict[str, float] = {}

    def report(stage: str, fraction: float) -> None:
        if progress:
            progress(stage, fraction)

    try:
        report("Parsing job description", 0.05)
        start = time.perf_counter()
        if job_profile is None:
            job_profile = analyze_job(job_pdf)
        timings["job_extraction"] = time.perf_counter() - start

        report("Parsing resume", 0.30)
        start = time.perf_counter()
        if resume_profile is None:
            resume_profile = analyze_resume(resume_pdf)
        timings["resume_extraction"] = time.perf_counter() - start

        report("Matching requirements", 0.60)
        start = time.perf_counter()
        evaluation = evaluate_candidate(job=job_profile, resume=resume_profile)
        timings["matching_scoring"] = time.perf_counter() - start

        report("Highlighting evidence", 0.85)
        start = time.perf_counter()
        highlight = highlight_resume(resume_pdf, evaluation)
        html_evidence = build_html_evidence_view(highlight)
        timings["highlighting"] = time.perf_counter() - start

        report("Done", 1.0)

        return CandidateResult(
            resume_path=str(resume_pdf),
            candidate_name=resume_profile.name or Path(resume_pdf).stem,
            evaluation=evaluation,
            highlight=highlight,
            html_evidence=html_evidence,
            timings=timings,
        )

    except Exception as exc:  # per-candidate isolation: one bad file
        # must not kill the whole batch
        return CandidateResult(
            resume_path=str(resume_pdf),
            candidate_name=Path(resume_pdf).stem,
            error=f"{type(exc).__name__}: {exc}",
            timings=timings,
        )


def run_batch(
    job_pdf: str | Path,
    resume_pdfs: list[str | Path],
    job_profile: JobProfile | None = None,
    resume_profiles: list[ResumeProfile | None] | None = None,
    progress: Callable[[str, float], None] | None = None,
) -> list[CandidateResult]:
    """Run the pipeline for many candidates against one job.

    The JobProfile is extracted once and reused for every resume.
    `resume_profiles` (optional, aligned with `resume_pdfs`) allows
    injecting pre-extracted profiles -- used by tests and caching.
    """

    results: list[CandidateResult] = []

    if job_profile is None:
        if progress:
            progress("Parsing job description", 0.0)
        job_profile = analyze_job(job_pdf)

    total = max(1, len(resume_pdfs))
    for index, resume_pdf in enumerate(resume_pdfs):
        def per_resume_progress(stage: str, fraction: float) -> None:
            if progress:
                overall = (index + fraction) / total
                progress(f"{Path(resume_pdf).name}: {stage}", overall)

        injected_profile = (
            resume_profiles[index]
            if resume_profiles is not None and index < len(resume_profiles)
            else None
        )

        results.append(
            run_pipeline(
                job_pdf=job_pdf,
                resume_pdf=resume_pdf,
                job_profile=job_profile,
                resume_profile=injected_profile,
                progress=per_resume_progress,
            )
        )

    return results
