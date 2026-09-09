"""Shared test fixtures: portable paths and deterministic embedding stubs."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.schemas.jobs import JobProfile, Requirement  # noqa: E402
from app.schemas.resume import Education, Experience, ResumeProfile  # noqa: E402

SAMPLE_JOB_PDF = ROOT / "data" / "jobs" / "sample_job.pdf"
SAMPLE_RESUME_PDF = ROOT / "data" / "resumes" / "sample_resume.pdf"


def make_job() -> JobProfile:
    """The classic fixture: 3 required + 2 preferred requirements."""
    return JobProfile(
        title="Machine Learning Engineer",
        requirements=[
            Requirement(name="Python", category="skill", importance="required"),
            Requirement(name="PyTorch", category="framework", importance="required"),
            Requirement(name="SQL", category="skill", importance="required"),
            Requirement(name="Docker", category="tool", importance="preferred"),
            Requirement(name="AWS", category="cloud", importance="preferred"),
        ],
    )


def make_resume() -> ResumeProfile:
    return ResumeProfile(
        name="Test Candidate",
        skills=["Python", "PyTorch", "Docker"],
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


@pytest.fixture
def deterministic_semantics(monkeypatch):
    """Replace the embedding model with a deterministic stub.

    The stub scores specific term pairs with hand-picked values so tests
    do not depend on network/model downloads, while everything else
    falls back to a low default.
    """
    from app.matching import matcher as matcher_module

    fixed_scores = {
        ("python", "python"): 1.0,
        ("pytorch", "pytorch"): 1.0,
        ("sql", "mysql"): 0.80,
        ("deep learning", "neural network modeling"): 0.80,
        ("docker", "docker"): 1.0,
    }

    def fake_similarity_matrix(requirements, evidence):
        matrix = [
            [
                fixed_scores.get(
                    (req.lower().strip(), ev.lower().strip()), 0.10
                )
                for ev in evidence
            ]
            for req in requirements
        ]
        return matrix

    monkeypatch.setattr(matcher_module, "similarity_matrix", fake_similarity_matrix)
    return fake_similarity_matrix
