import fitz  # PyMuPDF
from pathlib import Path


def extract_pdf_pages(file_path: str | Path) -> list[dict]:
    """
    Extract text from a PDF while preserving page numbers.

    Returns:
        [
            {
                "page_number": 1,
                "text": "..."
            },
            ...
        ]
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {file_path.suffix}")

    pages = []

    with fitz.open(file_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                }
            )

    if not any(page["text"] for page in pages):
        raise ValueError(
            f"No text layer found in {file_path}. The PDF is probably a "
            "scanned image; OCR is not supported yet."
        )

    return pages
