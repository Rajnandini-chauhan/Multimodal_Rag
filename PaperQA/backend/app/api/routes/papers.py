import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.ingestion_job import IngestionJob, IngestionStatus
from app.models.paper import Paper
from app.models.user import User
from app.schemas.paper import IngestionJobOut, PaperOut
from app.schemas.qa import AskRequest, AskResponse
from app.services.chunking import chunk_pages
from app.services.indexing import index_chunks
from app.services.pdf_extraction import extract_pages, get_page_count
from app.services.qa import generate_answer, retrieve_relevant_chunks
from app.storage.file_storage import InvalidPDFError, save_pdf, validate_pdf

router = APIRouter(prefix="/api/papers", tags=["papers"])


def _get_owned_paper(paper_id: uuid.UUID, db: Session, current_user: User) -> Paper:
    """Fetch a paper by id, ensuring it belongs to the current user.

    Returns 404 (not 403) for papers owned by someone else -- this avoids
    confirming to a client whether a given paper id exists at all.
    """
    paper = db.get(Paper, paper_id)
    if paper is None or paper.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return paper


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
    db.flush()

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


@router.post("/{paper_id}/index", response_model=PaperOut)
def index_paper(
    paper_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    paper = _get_owned_paper(paper_id, db, current_user)
    job = db.query(IngestionJob).filter(IngestionJob.paper_id == paper.id).first()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No ingestion job found for this paper",
        )

    job.status = IngestionStatus.PROCESSING
    db.commit()

    try:
        pages = extract_pages(paper.storage_path)
        chunks = chunk_pages(pages)
        index_chunks(str(paper.id), chunks)

        paper.page_count = get_page_count(paper.storage_path)
        job.status = IngestionStatus.COMPLETED
        job.error_message = None
    except Exception as exc:
        job.status = IngestionStatus.FAILED
        job.error_message = str(exc)

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


@router.post("/{paper_id}/ask", response_model=AskResponse)
def ask_paper(
    paper_id: uuid.UUID,
    payload: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    paper = _get_owned_paper(paper_id, db, current_user)
    job = db.query(IngestionJob).filter(IngestionJob.paper_id == paper.id).first()

    if job is None or job.status != IngestionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This paper has not finished indexing yet",
        )

    chunks = retrieve_relevant_chunks(str(paper.id), payload.question)
    result = generate_answer(payload.question, chunks)

    return AskResponse(answer=result.answer, sources=result.sources)