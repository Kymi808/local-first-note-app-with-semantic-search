from fastapi import APIRouter, HTTPException

from app.models import Note, NoteCreate, NoteMetadata
from app.services import note_store, vector_store

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("", response_model=list[NoteMetadata])
def list_notes():
    return note_store.list_notes()


@router.get("/{note_id}", response_model=Note)
def get_note(note_id: str):
    note = note_store.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("", response_model=Note, status_code=201)
def create_note(data: NoteCreate):
    note = note_store.create_note(data.title, data.content, data.tags)
    vector_store.index_note(note.id, note.content)
    return note


@router.put("/{note_id}", response_model=Note)
def update_note(note_id: str, data: NoteCreate):
    note = note_store.update_note(note_id, data.title, data.content, data.tags)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    vector_store.index_note(note.id, note.content)
    return note


@router.delete("/{note_id}")
def delete_note(note_id: str):
    if not note_store.delete_note(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    vector_store.remove_note(note_id)
    return {"ok": True}
