import chromadb

from app.config import CHROMA_DIR
from app.services import embeddings

_client: chromadb.PersistentClient | None = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name="notes",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _chunk_content(content: str, note_id: str) -> list[tuple[str, str]]:
    """Split content into chunks. Returns list of (chunk_id, chunk_text)."""
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    if not paragraphs:
        return [(f"{note_id}__0", content.strip() or "(empty)")]

    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        word_count = len(para.split())
        if current_len + word_count > 400 and current:
            chunks.append("\n\n".join(current))
            # overlap: keep last paragraph
            current = [current[-1]] if len(current) > 1 else []
            current_len = len(current[0].split()) if current else 0
        current.append(para)
        current_len += word_count

    if current:
        chunks.append("\n\n".join(current))

    return [(f"{note_id}__{i}", chunk) for i, chunk in enumerate(chunks)]


def index_note(note_id: str, content: str) -> None:
    collection = _get_collection()

    # Remove old chunks for this note
    remove_note(note_id)

    chunks = _chunk_content(content, note_id)
    if not chunks:
        return

    ids = [cid for cid, _ in chunks]
    texts = [text for _, text in chunks]
    embs = embeddings.embed_texts(texts)
    metadatas = [{"note_id": note_id, "chunk_index": i} for i in range(len(chunks))]

    collection.upsert(ids=ids, embeddings=embs, documents=texts, metadatas=metadatas)


def remove_note(note_id: str) -> None:
    collection = _get_collection()
    # Find all chunks for this note
    results = collection.get(where={"note_id": note_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def search(query: str, top_k: int = 5) -> list[tuple[str, str, float]]:
    """Returns list of (note_id, snippet, score)."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    query_emb = embeddings.embed_text(query)
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=min(top_k * 2, collection.count()),  # get extra to dedupe by note
    )

    seen_notes = set()
    output = []
    for i, doc_id in enumerate(results["ids"][0]):
        note_id = results["metadatas"][0][i]["note_id"]
        if note_id in seen_notes:
            continue
        seen_notes.add(note_id)
        snippet = results["documents"][0][i][:300]
        distance = results["distances"][0][i]
        score = 1 - distance  # cosine distance to similarity
        output.append((note_id, snippet, score))
        if len(output) >= top_k:
            break

    return output


def reindex_all(notes: list[tuple[str, str]]) -> int:
    """Reindex all notes. Takes list of (note_id, content). Returns count."""
    collection = _get_collection()
    # Clear existing
    if collection.count() > 0:
        all_ids = collection.get()["ids"]
        if all_ids:
            collection.delete(ids=all_ids)

    count = 0
    for note_id, content in notes:
        index_note(note_id, content)
        count += 1
    return count
