# Local-First Note App with Semantic Search

A local-first note-taking app with embedding-based semantic search and an AI assistant that answers questions using only your notes.

## Features

- **Markdown notes** stored as plain `.md` files on disk (compatible with any editor)
- **Semantic search** powered by local embeddings (sentence-transformers, runs on CPU)
- **AI assistant** that answers questions using only your notes as context (RAG with Claude API)
- **YAML frontmatter** for metadata (title, tags, timestamps)
- **No cloud dependency** for core features — your data stays local

## Setup

```bash
pip install -r requirements.txt
python run.py
```

Open http://localhost:8000 in your browser.

The first run will download the embedding model (~80MB). Notes are stored in `data/notes/`.

## Assistant

To use the AI assistant, set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your-key-here
python run.py
```

## Architecture

- **Backend**: FastAPI + sentence-transformers + ChromaDB
- **Frontend**: Vanilla HTML/CSS/JS with marked.js for markdown rendering
- **Storage**: Markdown files on disk + ChromaDB for vector index
- **Embeddings**: `all-MiniLM-L6-v2` (384-dim, local, no API needed)
- **Assistant**: RAG pipeline using Claude API

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notes` | List all notes |
| GET | `/api/notes/:id` | Get a note |
| POST | `/api/notes` | Create a note |
| PUT | `/api/notes/:id` | Update a note |
| DELETE | `/api/notes/:id` | Delete a note |
| POST | `/api/search` | Semantic search |
| POST | `/api/assistant` | Ask the assistant |
| POST | `/api/reindex` | Rebuild vector index |
