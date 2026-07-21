import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.papers import _get_owned_paper
from app.database.session import get_db
from app.models.content_block import ContentBlock, ContentType
from app.models.user import User
from app.schemas.content import EquationOut, FigureOut, TableOut

router = APIRouter(prefix="/api/papers/{paper_id}", tags=["content"])


def _get_caption_text(db: Session, block: ContentBlock) -> str | None:
    caption_id = (block.extra_data or {}).get("caption_block_id")
    if not caption_id:
        return None
    caption = db.get(ContentBlock, uuid.UUID(caption_id))
    return caption.content if caption else None


@router.get("/figures", response_model=list[FigureOut])
def list_figures(
    paper_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_paper(paper_id, db, current_user)

    figures = (
        db.query(ContentBlock)
        .filter(
            ContentBlock.paper_id == paper_id,
            ContentBlock.content_type == ContentType.FIGURE,
        )
        .order_by(ContentBlock.page_number)
        .all()
    )

    return [
        FigureOut(
            id=f.id,
            page_number=f.page_number,
            figure_number=(f.extra_data or {}).get("figure_number"),
            caption=_get_caption_text(db, f),
            bounding_box=f.bounding_box,
        )
        for f in figures
    ]


@router.get("/figures/{figure_id}/image")
def get_figure_image(
    paper_id: uuid.UUID,
    figure_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_paper(paper_id, db, current_user)

    figure = db.get(ContentBlock, figure_id)
    if (
        figure is None
        or figure.paper_id != paper_id
        or figure.content_type != ContentType.FIGURE
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Figure not found")

    storage_path = (figure.extra_data or {}).get("storage_path")
    if not storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Figure image not available"
        )

    return FileResponse(storage_path)


@router.get("/tables", response_model=list[TableOut])
def list_tables(
    paper_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_paper(paper_id, db, current_user)

    tables = (
        db.query(ContentBlock)
        .filter(
            ContentBlock.paper_id == paper_id,
            ContentBlock.content_type == ContentType.TABLE,
        )
        .order_by(ContentBlock.page_number)
        .all()
    )

    return [
        TableOut(
            id=t.id,
            page_number=t.page_number,
            table_number=(t.extra_data or {}).get("table_number"),
            caption=_get_caption_text(db, t),
            rows=json.loads(t.content) if t.content else [],
            bounding_box=t.bounding_box,
        )
        for t in tables
    ]


@router.get("/equations", response_model=list[EquationOut])
def list_equations(
    paper_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_paper(paper_id, db, current_user)

    equations = (
        db.query(ContentBlock)
        .filter(
            ContentBlock.paper_id == paper_id,
            ContentBlock.content_type == ContentType.EQUATION,
        )
        .order_by(ContentBlock.page_number)
        .all()
    )

    return [
        EquationOut(
            id=e.id,
            page_number=e.page_number,
            equation_number=(e.extra_data or {}).get("equation_number"),
            content=e.content,
            surrounding_caption=_get_caption_text(db, e),
            bounding_box=e.bounding_box,
        )
        for e in equations
    ]