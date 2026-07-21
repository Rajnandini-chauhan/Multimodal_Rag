import uuid

from app.services.extraction.block_extractor import (
    ExtractedBlock,
    extract_text_and_figure_blocks,
)
from app.services.extraction.caption_linker import link_captions
from app.services.extraction.equation_extractor import extract_equation_blocks
from app.services.extraction.table_extractor import extract_table_blocks
from app.storage.figure_storage import save_figure_image


def extract_all_content_blocks(pdf_path: str, paper_id: uuid.UUID) -> list[ExtractedBlock]:
    """Run the full Milestone 7 extraction pipeline for one paper.

    1. Extract text/heading/title blocks and raw figure (image) blocks
    2. Extract table blocks (pdfplumber)
    3. Extract equation-line candidates (heuristic)
    4. Detect captions and link them to their nearest figure/table
    5. Save figure image bytes to disk, replacing raw bytes in extra_data
       with a storage_path so the DB row stays lightweight

    Returns a flat list of ExtractedBlock, ready to be persisted as
    ContentBlock rows.
    """
    blocks = extract_text_and_figure_blocks(pdf_path)
    blocks += extract_table_blocks(pdf_path)
    blocks += extract_equation_blocks(pdf_path)

    blocks = link_captions(blocks)

    for block in blocks:
        if block.content_type != "figure":
            continue

        raw_bytes = block.extra_data.pop("_raw_image_bytes", None)
        ext = block.extra_data.pop("image_bytes_ext", "png")

        if not raw_bytes:
            continue

        storage_path = save_figure_image(paper_id, block.id, raw_bytes, ext)
        block.extra_data["storage_path"] = storage_path

    return blocks