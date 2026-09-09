from typing import TypedDict

from app.schemas.jobs import JobProfile
from app.schemas.resume import ResumeProfile


class PipelineState(TypedDict, total=False):
    # inputs
    job_pdf: str
    resume_pdf: str

    # intermediate
    job_text: str
    resume_text: str
    job_profile: JobProfile
    resume_profile: ResumeProfile

    # outputs
    match_results: list
    evaluation: dict
    errors: list