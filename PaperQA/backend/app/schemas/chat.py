import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    title: str = Field(default="New Chat", max_length=255)


class ChatSessionOut(BaseModel):
    id: uuid.UUID
    paper_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: list[int] | None = None
    figures: list[int] | None = None
    tables: list[int] | None = None
    visualization_spec: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionDetail(ChatSessionOut):
    messages: list[ChatMessageOut] = Field(default_factory=list)
