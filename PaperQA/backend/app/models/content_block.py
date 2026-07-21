import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ContentType(str, enum.Enum):
    TITLE = "title"
    HEADING = "heading"
    TEXT = "text"
    CAPTION = "caption"
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"
    REFERENCE = "reference"


class ContentBlock(Base):
    """A single structural item extracted from a paper: a paragraph, a
    figure, a table, a caption, an equation, etc. This is the README's
    'Unified Content Model' -- every extracted item, regardless of type,
    shares this same shape so the rest of the pipeline (retrieval,
    citation, linking) can treat them uniformly.
    """

    __tablename__ = "content_blocks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )

    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, name="content_type"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # For TEXT/HEADING/CAPTION: the actual text.
    # For TABLE: a JSON-serialized string of rows (kept in `content` for
    # simplicity; see `extra_data` for the structured version).
    # For FIGURE/EQUATION: a short label; the real content is the image
    # file on disk, referenced via `extra_data.storage_path`.
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # [x0, y0, x1, y1] in PDF page coordinate space.
    bounding_box: Mapped[list[float] | None] = mapped_column(
        ARRAY(Float), nullable=True
    )

    # Free-form structured data: section name, figure_number, table_number,
    # storage_path (for images), linked_block_id (for relationship linking),
    # structured table cells, etc. Kept as JSONB rather than a rigid set of
    # columns since different content types need very different metadata.
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    paper = relationship("Paper")