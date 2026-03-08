from fastapi import APIRouter

from app.models import SearchQuery, SearchResult
from app.services import vector_store, note_store

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=list[SearchResult])
def search_notes(data: SearchQuery):
    results = vector_store.search(data.query, data.top_k)
    output = []
    for note_id, snippet, score in results:
        note = note_store.get_note(note_id)
        if note:
            from app.models import NoteMetadata
            meta = NoteMetadata(**note.model_dump(exclude={"content"}))
            output.append(SearchResult(note=meta, snippet=snippet, score=round(score, 4)))
    return output
