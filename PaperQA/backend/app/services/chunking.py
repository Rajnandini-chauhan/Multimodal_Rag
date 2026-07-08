import re
from dataclasses import dataclass

from app.services.pdf_extraction import PageText

# A line that looks like a heading: short, and starts with a number/bullet
# pattern (e.g. "1. What is Data?", "3.2 Normalization") or is short and
# title-cased. This is a heuristic, not a perfect parser -- real academic
# PDFs don't expose semantic structure, so we approximate based on formatting.
HEADING_PATTERN = re.compile(r"^(\d+(\.\d+)*\.?\s+\S)|^([A-Z][A-Za-z ]{2,60})$")

MAX_CHUNK_CHARS = 1200
MIN_CHUNK_CHARS = 200


@dataclass
class Chunk:
    text: str
    page_number: int


def _looks_like_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 80:
        return False
    return bool(HEADING_PATTERN.match(line))


def _split_into_sections(page: PageText) -> list[str]:
    """Split a page's text into sections at heading-like lines."""
    lines = page.text.split("\n")
    sections: list[str] = []
    current: list[str] = []

    for line in lines:
        if _looks_like_heading(line) and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    return [s for s in sections if s]


def chunk_pages(pages: list[PageText]) -> list[Chunk]:
    """Chunk extracted page text into section-aware pieces.

    Strategy:
    - Split each page at heading-like lines first (keeps related content together)
    - Merge sections that are too small (avoids tiny, low-context chunks)
    - Split sections that are too large (avoids chunks too big for good retrieval)
    - Chunks never span across pages, so every chunk has one unambiguous page citation
    """
    chunks: list[Chunk] = []

    for page in pages:
        if not page.text:
            continue

        sections = _split_into_sections(page)
        buffer = ""

        for section in sections:
            candidate = f"{buffer}\n\n{section}".strip() if buffer else section

            if len(candidate) <= MAX_CHUNK_CHARS:
                buffer = candidate
                continue

            if buffer:
                chunks.append(Chunk(text=buffer, page_number=page.page_number))

            if len(section) <= MAX_CHUNK_CHARS:
                buffer = section
            else:
                # section itself is too long -- hard-split on paragraph boundaries
                for i in range(0, len(section), MAX_CHUNK_CHARS):
                    piece = section[i : i + MAX_CHUNK_CHARS]
                    chunks.append(Chunk(text=piece, page_number=page.page_number))
                buffer = ""

        if buffer and len(buffer) >= MIN_CHUNK_CHARS:
            chunks.append(Chunk(text=buffer, page_number=page.page_number))
        elif buffer and chunks and chunks[-1].page_number == page.page_number:
            # merge a too-small trailing buffer into the previous chunk on the same page
            chunks[-1] = Chunk(
                text=f"{chunks[-1].text}\n\n{buffer}", page_number=page.page_number
            )
        elif buffer:
            chunks.append(Chunk(text=buffer, page_number=page.page_number))

    return chunks