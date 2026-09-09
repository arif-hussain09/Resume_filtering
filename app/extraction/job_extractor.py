"""Job description -> JobProfile extraction via Groq LLM."""

from __future__ import annotations

from langchain_groq import ChatGroq

from app import config
from app.schemas.jobs import JobProfile

LLM_MAX_RETRIES = 2


def create_llm() -> ChatGroq:
    api_key = config.get_groq_api_key()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file "
            "(see .env.example) or enter it in the app sidebar."
        )

    return ChatGroq(
        model=config.get_groq_model(),
        temperature=0,
        api_key=api_key,
        max_retries=LLM_MAX_RETRIES,
    )


def extract_job_profile(text: str) -> JobProfile:
    """Extract a structured JobProfile from raw job-description text."""
    llm = create_llm()
    structured_llm = llm.with_structured_output(JobProfile)

    prompt = f"""
You are an expert job-description parser.

Extract the requirements from the following job description.

Rules:
- Identify the exact job title.
- Extract technical and non-technical requirements.
- Each requirement must be a SINGLE atomic skill/tool/concept
  (e.g. "Python, PyTorch, SQL" must become three separate requirements).
- Mark each requirement as required or preferred.
- Categorize each requirement appropriately:
  skill, framework, tool, language, cloud, domain, etc.
- Extract explicitly stated minimum experience.
  Express minimum_years as a decimal number (e.g. "3+ years" -> 3).
- Extract education requirements.
- Extract responsibilities.
- Extract relevant domain context.
- Do not invent information.
- If something is missing, return an empty list, not null.

JOB DESCRIPTION:

{text}
"""

    return structured_llm.invoke(prompt)
