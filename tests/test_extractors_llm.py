"""LLM-dependent tests: skipped automatically when no GROQ_API_KEY is set."""

import os

import pytest

from app.ingestion.pdf_parser import extract_pdf_pages

from conftest import SAMPLE_JOB_PDF, SAMPLE_RESUME_PDF

REQUIRES_KEY = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set; skipping live LLM extraction tests",
)


@REQUIRES_KEY
def test_job_extraction():
    pages = extract_pdf_pages(SAMPLE_JOB_PDF)
    text = "\n".join(page["text"] for page in pages)

    from app.extraction.job_extractor import extract_job_profile

    job = extract_job_profile(text)

    print("\nJOB PROFILE:")
    print(job.model_dump_json(indent=2))

    assert job.title
    assert len(job.requirements) > 0


@REQUIRES_KEY
def test_resume_extraction():
    pages = extract_pdf_pages(SAMPLE_RESUME_PDF)
    text = "\n".join(page["text"] for page in pages)

    from app.extraction.resume_extractor import extract_resume_profile

    resume = extract_resume_profile(text)

    print("\nRESUME PROFILE:")
    print(resume.model_dump_json(indent=2))

    assert resume.name
    assert len(resume.skills) > 0
