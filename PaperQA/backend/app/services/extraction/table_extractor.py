import json

import pdfplumber

from app.services.extraction.block_extractor import ExtractedBlock


def extract_table_blocks(pdf_path: str) -> list[ExtractedBlock]:
    """Extract TABLE blocks with structured cell data using pdfplumber.

    pdfplumber's table detection is based on ruling lines and text
    alignment, which handles the bordered/grid-style tables common in
    academic papers well. Each table's rows are preserved as structured
    data (list of lists), not flattened into prose, so downstream code
    can render or reason over the actual cells.
    """
    blocks: list[ExtractedBlock] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            page_number = page_index + 1

            for table in page.find_tables():
                rows = table.extract()
                if not rows or all(not any(cell for cell in row) for row in rows):
                    continue  # skip empty/false-positive table detections

                x0, top, x1, bottom = table.bbox

                blocks.append(
                    ExtractedBlock(
                        content_type="table",
                        page_number=page_number,
                        content=json.dumps(rows),
                        bounding_box=[x0, top, x1, bottom],
                        extra_data={"row_count": len(rows), "col_count": len(rows[0])},
                    )
                )

    return blocks