import uuid

from pydantic import BaseModel


class FigureOut(BaseModel):
    id: uuid.UUID
    page_number: int
    figure_number: int | None
    caption: str | None
    bounding_box: list[float] | None


class TableOut(BaseModel):
    id: uuid.UUID
    page_number: int
    table_number: int | None
    caption: str | None
    rows: list[list[str | None]]
    bounding_box: list[float] | None


class EquationOut(BaseModel):
    id: uuid.UUID
    page_number: int
    equation_number: int | None
    content: str
    surrounding_caption: str | None
    bounding_box: list[float] | None