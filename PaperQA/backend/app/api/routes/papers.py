from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.ingestion_job import IngestionJob, IngestionStatus
from app.models.paper import Paper
from app.models.user import User
from app.schemas.paper import IngestionJobOut, PaperOut
from app.storage.file_storage import InvalidPDFError, save_pdf, validate_pdf

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("/upload", response_model=PaperOut, status_code=status.HTTP_201_CREATED)
async def upload_paper(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contents = await file.read()

    try:
        validate_pdf(file, contents)
    except InvalidPDFError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    storage_path = save_pdf(owner_id=current_user.id, contents=contents)

    paper = Paper(
        owner_id=current_user.id,
        original_filename=file.filename,
        storage_path=storage_path,
        file_size_bytes=len(contents),
    )
    db.add(paper)
    db.flush()  # assigns paper.id without committing yet

    job = IngestionJob(paper_id=paper.id, status=IngestionStatus.PENDING)
    db.add(job)

    db.commit()
    db.refresh(paper)
    db.refresh(job)

    return PaperOut(
        id=paper.id,
        original_filename=paper.original_filename,
        file_size_bytes=paper.file_size_bytes,
        page_count=paper.page_count,
        created_at=paper.created_at,
        ingestion_job=IngestionJobOut.model_validate(job),
    )