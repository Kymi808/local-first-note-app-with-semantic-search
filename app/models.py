from pydantic import BaseModel
from datetime import datetime


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: list[str] = []


class NoteMetadata(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    tags: list[str] = []


class Note(NoteMetadata):
    content: str


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    note: NoteMetadata
    snippet: str
    score: float


class AssistantQuery(BaseModel):
    question: str


class AssistantResponse(BaseModel):
    answer: str
    sources: list[NoteMetadata]
