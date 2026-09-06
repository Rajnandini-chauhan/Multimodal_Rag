import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.paper import Paper
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageOut,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionOut,
)
from app.services.agent.agent import run_paper_agent

router = APIRouter(tags=["chat"])


def _get_owned_session(session_id: uuid.UUID, db: Session, current_user: User) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return session


def _get_owned_paper(paper_id: uuid.UUID, db: Session, current_user: User) -> Paper:
    paper = db.get(Paper, paper_id)
    if paper is None or paper.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return paper


@router.post("/api/papers/{paper_id}/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    paper_id: uuid.UUID,
    payload: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    paper = _get_owned_paper(paper_id, db, current_user)
    session = ChatSession(
        paper_id=paper.id,
        user_id=current_user.id,
        title=payload.title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/api/papers/{paper_id}/sessions", response_model=list[ChatSessionOut])
def list_chat_sessions(
    paper_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    paper = _get_owned_paper(paper_id, db, current_user)
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.paper_id == paper.id, ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return sessions


@router.get("/api/sessions/{session_id}/messages", response_model=ChatSessionDetail)
def get_chat_session_detail(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(session_id, db, current_user)
    return session


@router.post("/api/sessions/{session_id}/messages", response_model=ChatMessageOut)
def send_chat_message(
    session_id: uuid.UUID,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(session_id, db, current_user)
    try:
        assistant_msg = run_paper_agent(session.id, payload.content, db)
        return assistant_msg
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution error: {str(exc)}",
        )


@router.delete("/api/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(session_id, db, current_user)
    db.delete(session)
    db.commit()
