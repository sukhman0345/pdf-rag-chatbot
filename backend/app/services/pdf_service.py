import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str):
    """
    Extract text from each page of the PDF.

    Returns:
        A list of dictionaries containing:
        - page number
        - extracted text
    """

    document = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text()

        pages.append(
            {
                "page": page_number,
                "text": text
            }
        )

    document.close()

    return pages