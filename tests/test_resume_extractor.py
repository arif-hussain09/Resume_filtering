from app.ingestion.pdf_parser import extract_pdf_pages
from app.extraction.resume_extractor import extract_resume_profile


def test_resume_extraction():
    pages = extract_pdf_pages("data/resumes/sample_resume.pdf")

    text = "\n".join(page["text"] for page in pages)

    resume = extract_resume_profile(text)

    print("\nRESUME PROFILE:")
    print(resume.model_dump_json(indent=2))

    assert resume.name
    assert len(resume.skills) > 0
    assert len(resume.experience) > 0