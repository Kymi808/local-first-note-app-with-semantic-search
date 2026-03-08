from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import BASE_DIR
from app.routers import notes, search, assistant
from app.services import note_store, vector_store, embeddings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load embedding model on startup
    embeddings.get_model()

    # Index any notes that exist on disk
    all_notes = note_store.list_notes()
    if all_notes:
        pairs = []
        for meta in all_notes:
            note = note_store.get_note(meta.id)
            if note:
                pairs.append((note.id, note.content))
        if pairs:
            count = vector_store.reindex_all(pairs)
            print(f"Indexed {count} notes on startup.")

    yield


app = FastAPI(title="Local Notes", lifespan=lifespan)

app.include_router(notes.router)
app.include_router(search.router)
app.include_router(assistant.router)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/")
def root():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))


@app.post("/api/reindex")
def reindex():
    all_notes = note_store.list_notes()
    pairs = []
    for meta in all_notes:
        note = note_store.get_note(meta.id)
        if note:
            pairs.append((note.id, note.content))
    count = vector_store.reindex_all(pairs)
    return {"indexed": count}
