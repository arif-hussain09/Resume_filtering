from app.ingestion.pdf_parser import extract_pdf_pages
from app.extraction.job_extractor import extract_job_profile


def test_job_extraction():

    pages = extract_pdf_pages("data/jobs/sample_job.pdf")

    text = "\n".join(
        page["text"]
        for page in pages
    )

    job = extract_job_profile(text)
    
    print("\nJOB PROFILE:")
    print(job.model_dump_json(indent=2))

    assert job.title
    assert len(job.requirements) > 0