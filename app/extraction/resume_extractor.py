from app.extraction.job_extractor import create_llm
from app.schemas.resume import ResumeProfile


def extract_resume_profile(text: str) -> ResumeProfile:
    structured_llm = create_llm().with_structured_output(ResumeProfile)

    prompt = f"""
You are an expert resume parser.

Extract structured information from the following resume.

Rules:
- Extract the candidate's full name.
- Extract every skill as an INDIVIDUAL item:
  "Python, PyTorch, SQL" must become three separate skills,
  not one combined string.
- Extract work experience entries with job title, company,
  duration, and a description of responsibilities.
- Keep experience and project descriptions CLOSE TO THE ORIGINAL
  WORDING of the resume. Do not paraphrase or summarize heavily.
- Extract education entries.
- Extract notable projects and the technologies used.
- Extract certifications and achievements if present.
- Do not invent information that is not in the resume.
- If something is missing, return an empty list, not null.
- Ignore contact details (email, phone, address).

RESUME:

{text}
"""

    return structured_llm.invoke(prompt)