import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.schemas.jobs import JobProfile


load_dotenv()


def create_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file."
        )

    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=api_key,
    )


def extract_job_profile(text: str) -> JobProfile:
    llm = create_llm()

    structured_llm = llm.with_structured_output(JobProfile)

    prompt = f"""
You are an expert job-description parser.

Extract the requirements from the following job description.

Rules:
- Identify the exact job title.
- Extract technical and non-technical requirements.
- Mark each requirement as required or preferred.
- Categorize each requirement appropriately:
  skill, framework, tool, language, cloud, domain, etc.
- Extract explicitly stated minimum experience.
- Extract education requirements.
- Extract responsibilities.
- Extract relevant domain context.
- Do not invent information.

JOB DESCRIPTION:

{text}
"""

    return structured_llm.invoke(prompt)