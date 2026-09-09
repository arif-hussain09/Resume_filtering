from app.ingestion.pdf_parser import extract_pdf_pages


def test_extract_pdf_pages():

    pdf_path = r"data\jobs\sample_job.pdf"

    pages = extract_pdf_pages(pdf_path)

    assert isinstance(pages, list)
    assert len(pages) > 0

    assert "page_number" in pages[0]
    assert "text" in pages[0]