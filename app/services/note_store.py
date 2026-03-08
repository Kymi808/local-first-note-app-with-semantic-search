import re
import yaml
from datetime import datetime, timezone
from pathlib import Path

from app.config import NOTES_DIR
from app.models import Note, NoteMetadata


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower().strip())
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "untitled"


def _unique_slug(title: str) -> str:
    slug = _slugify(title)
    if not (NOTES_DIR / f"{slug}.md").exists():
        return slug
    i = 2
    while (NOTES_DIR / f"{slug}-{i}.md").exists():
        i += 1
    return f"{slug}-{i}"


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return meta, body
    return {}, raw.strip()


def _build_frontmatter(meta: dict) -> str:
    return f"---\n{yaml.dump(meta, default_flow_style=False).strip()}\n---\n"


def _read_note_file(path: Path) -> Note:
    raw = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(raw)
    note_id = meta.get("id", path.stem)
    return Note(
        id=note_id,
        title=meta.get("title", path.stem),
        created_at=meta.get("created_at", datetime.now(timezone.utc)),
        updated_at=meta.get("updated_at", datetime.now(timezone.utc)),
        tags=meta.get("tags", []),
        content=body,
    )


def list_notes() -> list[NoteMetadata]:
    notes = []
    for path in sorted(NOTES_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        note = _read_note_file(path)
        notes.append(NoteMetadata(**note.model_dump(exclude={"content"})))
    return notes


def get_note(note_id: str) -> Note | None:
    path = NOTES_DIR / f"{note_id}.md"
    if not path.exists():
        return None
    return _read_note_file(path)


def create_note(title: str, content: str, tags: list[str] | None = None) -> Note:
    now = datetime.now(timezone.utc)
    note_id = _unique_slug(title)
    meta = {
        "id": note_id,
        "title": title,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "tags": tags or [],
    }
    path = NOTES_DIR / f"{note_id}.md"
    path.write_text(_build_frontmatter(meta) + "\n" + content, encoding="utf-8")
    return _read_note_file(path)


def update_note(note_id: str, title: str, content: str, tags: list[str] | None = None) -> Note | None:
    path = NOTES_DIR / f"{note_id}.md"
    if not path.exists():
        return None
    existing = _read_note_file(path)
    now = datetime.now(timezone.utc)
    meta = {
        "id": note_id,
        "title": title,
        "created_at": existing.created_at.isoformat(),
        "updated_at": now.isoformat(),
        "tags": tags or [],
    }
    path.write_text(_build_frontmatter(meta) + "\n" + content, encoding="utf-8")
    return _read_note_file(path)


def delete_note(note_id: str) -> bool:
    path = NOTES_DIR / f"{note_id}.md"
    if not path.exists():
        return False
    path.unlink()
    return True
