import re

from app.services.extraction.block_extractor import ExtractedBlock

CAPTION_PATTERN = re.compile(
    r"^(Fig(?:ure)?\.?\s*(\d+)|Table\s*(\d+)|Eq(?:uation)?\.?\s*(\d+))\b",
    re.IGNORECASE,
)


def _bbox_center_y(bbox: list[float]) -> float:
    return (bbox[1] + bbox[3]) / 2


def link_captions(blocks: list[ExtractedBlock]) -> list[ExtractedBlock]:
    """Reclassify caption-like TEXT blocks as CAPTION, then link each
    caption to its nearest FIGURE/TABLE on the same page.

    A caption ("Figure 3: ...") is identified by its leading text pattern.
    Linking is done by vertical proximity on the same page -- captions are
    conventionally placed directly above or below the item they describe,
    so the closest figure/table by y-distance is almost always the
    correct match.
    """
    captions: list[ExtractedBlock] = []
    for block in blocks:
        if block.content_type != "text":
            continue

        match = CAPTION_PATTERN.match(block.content.strip())
        if not match:
            continue

        block.content_type = "caption"

        if match.group(2):
            block.extra_data["figure_number"] = int(match.group(2))
            target_type = "figure"
        elif match.group(3):
            block.extra_data["table_number"] = int(match.group(3))
            target_type = "table"
        else:
            block.extra_data["equation_number"] = int(match.group(4))
            target_type = "equation"

        block.extra_data["_target_type"] = target_type
        captions.append(block)

    for caption in captions:
        target_type = caption.extra_data.pop("_target_type")
        same_page_candidates = [
            b
            for b in blocks
            if b.content_type == target_type and b.page_number == caption.page_number
        ]

        if not same_page_candidates:
            continue

        caption_y = _bbox_center_y(caption.bounding_box)
        nearest = min(
            same_page_candidates,
            key=lambda b: abs(_bbox_center_y(b.bounding_box) - caption_y),
        )

        # Link both directions so either side can be looked up from the other.
        caption.extra_data["linked_block_id"] = str(nearest.id)
        nearest.extra_data["caption_block_id"] = str(caption.id)
        if "figure_number" in caption.extra_data:
            nearest.extra_data["figure_number"] = caption.extra_data["figure_number"]
        if "table_number" in caption.extra_data:
            nearest.extra_data["table_number"] = caption.extra_data["table_number"]

    return blocks