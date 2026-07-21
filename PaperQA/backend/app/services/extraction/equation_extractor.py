import re

import fitz  # PyMuPDF

from app.services.extraction.block_extractor import ExtractedBlock

MATH_SYMBOLS = set("=+±∑∫√≤≥≠∝∇∂αβγδθλμπσφω∞×÷")
WORD_PATTERN = re.compile(r"[A-Za-z]{3,}")


def _looks_like_equation(text: str, bbox: list[float], page_width: float) -> bool:
    text = text.strip()
    if not text or len(text) > 120:
        return False

    symbol_count = sum(1 for ch in text if ch in MATH_SYMBOLS)
    if symbol_count == 0:
        return False

    word_matches = WORD_PATTERN.findall(text)
    if len(word_matches) > 2:
        return False

    x0, _, x1, _ = bbox
    line_center = (x0 + x1) / 2
    page_center = page_width / 2
    is_roughly_centered = abs(line_center - page_center) < page_width * 0.2

    return is_roughly_centered


def extract_equation_blocks(pdf_path: str) -> list[ExtractedBlock]:
    """Heuristically detect standalone equation lines.

    This is a pattern-based heuristic, not a real math/LaTeX parser -- true
    equation transcription needs a specialized model (planned as part of
    Milestone 8's VLM work). This step's job is narrower: find likely
    equation lines and their page location, so they can be flagged,
    linked to surrounding explanatory text, and later handed to a VLM
    for actual interpretation.
    """
    blocks: list[ExtractedBlock] = []

    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc):
            page_number = page_index + 1
            page_width = page.rect.width

            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue

                for line in block.get("lines", []):
                    line_text = "".join(s["text"] for s in line["spans"]).strip()
                    if not line_text:
                        continue

                    if _looks_like_equation(line_text, line["bbox"], page_width):
                        blocks.append(
                            ExtractedBlock(
                                content_type="equation",
                                page_number=page_number,
                                content=line_text,
                                bounding_box=list(line["bbox"]),
                                extra_data={},
                            )
                        )

    return blocks