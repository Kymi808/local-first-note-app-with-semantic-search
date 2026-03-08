import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NOTES_DIR = BASE_DIR / "data" / "notes"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

NOTES_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
