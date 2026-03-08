import anthropic

from app.config import ANTHROPIC_API_KEY
from app.services import vector_store, note_store
from app.models import NoteMetadata


def ask(question: str) -> tuple[str, list[NoteMetadata]]:
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set. Export it as an environment variable.")

    # Retrieve relevant notes
    results = vector_store.search(question, top_k=5)
    if not results:
        return "I couldn't find any relevant notes to answer your question.", []

    # Fetch full note content
    sources = []
    context_parts = []
    for note_id, snippet, score in results:
        note = note_store.get_note(note_id)
        if note:
            sources.append(NoteMetadata(**note.model_dump(exclude={"content"})))
            context_parts.append(f"## {note.title}\n{note.content}")

    if not context_parts:
        return "I couldn't find any relevant notes to answer your question.", []

    context = "\n\n---\n\n".join(context_parts)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=(
            "You are a helpful assistant that answers questions based ONLY on the user's "
            "personal notes provided below. Do not use any outside knowledge. If the notes "
            "don't contain enough information to answer the question, say so clearly. "
            "Reference which notes you drew from in your answer.\n\n"
            f"USER'S NOTES:\n\n{context}"
        ),
        messages=[{"role": "user", "content": question}],
    )

    answer = response.content[0].text
    return answer, sources
