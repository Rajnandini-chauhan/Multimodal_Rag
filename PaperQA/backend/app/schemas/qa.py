from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    sources: list[int] = Field(default_factory=list)   # page numbers the answer was grounded in
    figures: list[int] = Field(default_factory=list)   # figure numbers whose descriptions informed the answer
    tables: list[int] = Field(default_factory=list)    # table numbers whose summaries informed the answer
