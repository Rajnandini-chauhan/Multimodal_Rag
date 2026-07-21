
import statistics
import uuid
from dataclasses import dataclass, field

import fitz  # PyMuPDF


@dataclass
class ExtractedBlock:
    content_type: str  # "title" | "heading" | "text" | "figure" | "table" | "equation" | "caption"
    page_number: int
    content: str
    bounding_box: list[float]
    extra_data: dict = field(default_factory=dict)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

def _median_font_size(doc: fitz.Document) -> float:
    """Find the 'body text' font size by taking the median span size across
    the whole document. Headings/titles are then detected relative to this
    baseline, rather than against a hardcoded absolute size -- papers vary
    a lot in base font size (9pt vs 11pt vs 12pt), so a relative comparison
    is far more reliable than a fixed threshold.
    """
    sizes = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span["text"].strip():
                        sizes.append(round(span["size"], 1))
    return statistics.median(sizes) if sizes else 10.0


def extract_text_and_figure_blocks(pdf_path: str) -> list[ExtractedBlock]:
    """Extract TITLE / HEADING / TEXT / FIGURE blocks with page-space
    coordinates from a PDF, using PyMuPDF's structured ('dict') text output.
    """
    blocks: list[ExtractedBlock] = []

    with fitz.open(pdf_path) as doc:
        body_size = _median_font_size(doc)

        for page_index, page in enumerate(doc):
            page_number = page_index + 1
            raw_blocks = page.get_text("dict")["blocks"]

            for block in raw_blocks:
                bbox = list(block["bbox"])

                if block["type"] == 1:
                    # Image block -- PyMuPDF already gives us the decoded
                    # image bytes and its format, so we don't need to
                    # re-render the page to get the figure's pixels.
                    blocks.append(
                        ExtractedBlock(
                            content_type="figure",
                            page_number=page_number,
                            content="",
                            bounding_box=bbox,
                            extra_data={
                                "image_bytes_ext": block.get("ext", "png"),
                                "_raw_image_bytes": block.get("image"),
                                "width": block.get("width"),
                                "height": block.get("height"),
                            },
                        )
                    )
                    continue

                if block["type"] != 0:
                    continue  # skip anything that's neither text nor image

                text_parts = []
                span_sizes = []
                for line in block.get("lines", []):
                    line_text = "".join(s["text"] for s in line["spans"])
                    text_parts.append(line_text)
                    span_sizes.extend(s["size"] for s in line["spans"])

                text = "\n".join(text_parts).strip()
                if not text:
                    continue

                avg_size = statistics.mean(span_sizes) if span_sizes else body_size

                if avg_size >= body_size * 1.4 and page_number == 1:
                    content_type = "title"
                elif avg_size >= body_size * 1.15:
                    content_type = "heading"
                else:
                    content_type = "text"

                blocks.append(
                    ExtractedBlock(
                        content_type=content_type,
                        page_number=page_number,
                        content=text,
                        bounding_box=bbox,
                        extra_data={"font_size": round(avg_size, 1)},
                    )
                )

    return blocks