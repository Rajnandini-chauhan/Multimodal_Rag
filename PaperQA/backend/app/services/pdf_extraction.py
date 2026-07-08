from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass
class PageText:
    page_number: int  # 1-indexed, matches how a human would cite a page
    text: str


def extract_pages(pdf_path: str) -> list[PageText]:
    """Extract raw text from each page of a PDF, preserving page numbers.

    Page numbers are 1-indexed so citations later match what a reader
    would see printed on the page / in a PDF viewer's page counter.
    """
    pages: list[PageText] = []

    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc):
            text = page.get_text().strip()
            pages.append(PageText(page_number=index + 1, text=text))

    return pages


def get_page_count(pdf_path: str) -> int:
    with fitz.open(pdf_path) as doc:
        return doc.page_count