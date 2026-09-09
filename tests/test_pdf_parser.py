from app.ingestion.pdf_parser import extract_pdf_pages

from conftest import SAMPLE_JOB_PDF, SAMPLE_RESUME_PDF


def test_extract_pdf_pages_job():
    pages = extract_pdf_pages(SAMPLE_JOB_PDF)

    assert isinstance(pages, list)
    assert len(pages) > 0
    assert "page_number" in pages[0]
    assert "text" in pages[0]
    assert pages[0]["page_number"] == 1


def test_extract_pdf_pages_resume():
    pages = extract_pdf_pages(SAMPLE_RESUME_PDF)
    assert any("Python" in page["text"] for page in pages)


def test_missing_file_raises():
    import pytest

    with pytest.raises(FileNotFoundError):
        extract_pdf_pages(SAMPLE_JOB_PDF.parent / "nope.pdf")


def test_non_pdf_raises():
    import pytest

    with pytest.raises(ValueError):
        extract_pdf_pages(__file__)
