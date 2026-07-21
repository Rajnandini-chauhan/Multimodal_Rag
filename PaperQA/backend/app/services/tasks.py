import uuid

from app.celery_app import celery_app
from app.database.session import SessionLocal
from app.models.content_block import ContentBlock
from app.models.ingestion_job import IngestionJob, IngestionStatus
from app.models.paper import Paper
from app.models.user import User  # noqa: F401 -- ensures SQLAlchemy can resolve Paper.owner relationship
from app.services.chunking import chunk_pages
from app.services.extraction.pipeline import extract_all_content_blocks
from app.services.indexing import index_chunks
from app.services.pdf_extraction import extract_pages, get_page_count


@celery_app.task(
    name="app.services.tasks.run_ingestion",
    bind=True,
    max_retries=3,
    default_retry_delay=10,  # seconds
)
def run_ingestion(self, paper_id: str) -> None:
    """Background task: extract, chunk, embed, and index a paper's PDF,
    plus run the Milestone 7 multimodal extraction pipeline (figures,
    tables, equations, captions, and their relationships).

    Updates IngestionJob.progress_percent as it goes, so clients can poll
    for status. Retries transient failures up to 3 times before marking
    the job as permanently failed.
    """
    db = SessionLocal()

    try:
        paper = db.get(Paper, uuid.UUID(paper_id))
        job = db.query(IngestionJob).filter(IngestionJob.paper_id == paper.id).first()

        if paper is None or job is None:
            return

        job.status = IngestionStatus.PROCESSING
        job.progress_percent = 5
        db.commit()

        pages = extract_pages(paper.storage_path)
        job.progress_percent = 20
        db.commit()

        chunks = chunk_pages(pages)
        job.progress_percent = 35
        db.commit()

        index_chunks(str(paper.id), chunks)
        job.progress_percent = 55
        db.commit()

        # Milestone 7: figures, tables, equations, captions, and linking.
        # Any previous extraction for this paper is cleared first, so
        # re-indexing fully replaces rather than accumulates blocks.
        db.query(ContentBlock).filter(ContentBlock.paper_id == paper.id).delete()

        extracted_blocks = extract_all_content_blocks(paper.storage_path, paper.id)
        for block in extracted_blocks:
            db.add(
                ContentBlock(
                    id=block.id,
                    paper_id=paper.id,
                    content_type=block.content_type,
                    page_number=block.page_number,
                    content=block.content,
                    bounding_box=block.bounding_box,
                    extra_data=block.extra_data,
                )
            )
        job.progress_percent = 90
        db.commit()

        paper.page_count = get_page_count(paper.storage_path)
        job.status = IngestionStatus.COMPLETED
        job.progress_percent = 100
        job.error_message = None
        db.commit()

    except Exception as exc:
        db.rollback()
        job = (
            db.query(IngestionJob)
            .filter(IngestionJob.paper_id == uuid.UUID(paper_id))
            .first()
        )

        try:
            # Retry transient failures (e.g. a momentary DB or model hiccup)
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            if job is not None:
                job.status = IngestionStatus.FAILED
                job.error_message = str(exc)
                db.commit()

    finally:
        db.close()