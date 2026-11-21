import uuid
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


def save_figure_image(paper_id: uuid.UUID, block_id: uuid.UUID, image_bytes: bytes, ext: str) -> str:
    """Save an extracted figure's raw image bytes to disk, namespaced by
    paper, and return the storage path."""
    figures_dir = Path(settings.upload_dir).parent / "figures" / str(paper_id)
    figures_dir.mkdir(parents=True, exist_ok=True)

    file_path = figures_dir / f"{block_id}.{ext}"
    file_path.write_bytes(image_bytes)

    return str(file_path)