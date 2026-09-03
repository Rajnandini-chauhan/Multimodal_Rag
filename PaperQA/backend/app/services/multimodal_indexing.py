import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.content_block import ContentBlock, ContentType
from app.services.indexing import (
    embed_texts,
    get_chroma_client,
    get_multimodal_collection_name,
)
from app.services.vlm import describe_figure, describe_table

logger = logging.getLogger(__name__)

EXT_TO_MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


def index_multimodal_blocks(db: Session, paper_id: str, blocks: list[ContentBlock]) -> int:
    """Generate VLM descriptions for figure/table blocks, save them back onto
    each block's extra_data, and embed the descriptions into a dedicated
    ChromaDB collection so they become semantically retrievable alongside
    plain text chunks.

    Returns the number of descriptions successfully generated and indexed.
    """
    client = get_chroma_client()

    try:
        client.delete_collection(name=get_multimodal_collection_name(paper_id))
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=get_multimodal_collection_name(paper_id)
    )

    ids, texts, metadatas = [], [], []

    # Tables first (cheap, no vision call needed), then figures.
    tables = [b for b in blocks if b.content_type == ContentType.TABLE]
    figures = [b for b in blocks if b.content_type == ContentType.FIGURE]
    candidates = tables + figures
    total = len(candidates)

    for idx, block in enumerate(candidates, start=1):
        logger.info(
            "Describing %s %d/%d (block %s)",
            block.content_type.value, idx, total, block.id,
        )
        description = None

        if block.content_type == ContentType.FIGURE:
            storage_path = (block.extra_data or {}).get("storage_path")
            if not storage_path or not Path(storage_path).exists():
                continue

            ext = Path(storage_path).suffix.lstrip(".").lower()
            mime_type = EXT_TO_MIME.get(ext, "image/png")
            image_bytes = Path(storage_path).read_bytes()

            description = describe_figure(image_bytes, mime_type)

        elif block.content_type == ContentType.TABLE:
            try:
                rows = json.loads(block.content) if block.content else []
            except json.JSONDecodeError:
                rows = []
            if not rows:
                continue

            description = describe_table(rows)

        else:
            continue

        if not description:
            logger.warning("No description generated for block %s", block.id)
            continue

        # Persist the description on the block itself so it's visible via
        # the /figures and /tables endpoints too, not just used internally.
        block.extra_data = {**(block.extra_data or {}), "description": description}
        db.add(block)

        ids.append(str(block.id))
        texts.append(description)

        metadata = {
            "block_id": str(block.id),
            "content_type": block.content_type.value,
            "page_number": block.page_number,
        }
        figure_number = (block.extra_data or {}).get("figure_number")
        table_number = (block.extra_data or {}).get("table_number")
        if figure_number is not None:
            metadata["figure_number"] = figure_number
        if table_number is not None:
            metadata["table_number"] = table_number
        metadatas.append(metadata)

    if texts:
        embeddings = embed_texts(texts, input_type="passage")
        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        db.commit()

    logger.info("Multimodal indexing complete: %d/%d described", len(texts), total)
    return len(texts)
