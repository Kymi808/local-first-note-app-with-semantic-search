const $ = (sel) => document.querySelector(sel);

let currentNoteId = null;
let isPreview = false;
let searchTimeout = null;

// --- API helpers ---
async function api(path, opts = {}) {
    const res = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...opts,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Request failed");
    }
    return res.json();
}

// --- Notes ---
async function fetchNotes() {
    const notes = await api("/api/notes");
    renderNoteList(notes);
}

function renderNoteList(notes, isSearch = false) {
    const list = $("#note-list");
    list.innerHTML = "";
    if (notes.length === 0) {
        list.innerHTML = `<p style="padding:12px;color:#999;font-size:0.85rem">${isSearch ? "No results" : "No notes yet"}</p>`;
        return;
    }
    for (const item of notes) {
        const note = item.note || item; // handle search results vs plain notes
        const score = item.score;
        const div = document.createElement("div");
        div.className = "note-item" + (note.id === currentNoteId ? " active" : "");
        const date = new Date(note.updated_at).toLocaleDateString();
        div.innerHTML = `
            <div class="note-item-title">
                ${escapeHtml(note.title || "Untitled")}
                ${score !== undefined ? `<span class="search-score">${Math.round(score * 100)}%</span>` : ""}
            </div>
            <div class="note-item-meta">${date}${note.tags?.length ? " · " + note.tags.join(", ") : ""}</div>
        `;
        div.addEventListener("click", () => loadNote(note.id));
        list.appendChild(div);
    }
}

async function loadNote(id) {
    const note = await api(`/api/notes/${id}`);
    currentNoteId = note.id;
    $("#note-title").value = note.title;
    $("#note-tags").value = (note.tags || []).join(", ");
    $("#note-body").value = note.content;
    $("#editor-empty").classList.add("hidden");
    $("#editor-content").classList.remove("hidden");
    if (isPreview) togglePreview();
    highlightActive();
}

function highlightActive() {
    document.querySelectorAll(".note-item").forEach((el) => el.classList.remove("active"));
    document.querySelectorAll(".note-item").forEach((el) => {
        if (el.querySelector(".note-item-title")?.textContent?.trim().length) {
            // re-fetch to highlight
        }
    });
    fetchNotes().catch(() => {});
}

async function saveNote() {
    const title = $("#note-title").value.trim() || "Untitled";
    const content = $("#note-body").value;
    const tags = $("#note-tags").value.split(",").map((t) => t.trim()).filter(Boolean);
    const body = JSON.stringify({ title, content, tags });

    if (currentNoteId) {
        await api(`/api/notes/${currentNoteId}`, { method: "PUT", body });
    } else {
        const note = await api("/api/notes", { method: "POST", body });
        currentNoteId = note.id;
    }
    await fetchNotes();
}

async function deleteNote() {
    if (!currentNoteId) return;
    if (!confirm("Delete this note?")) return;
    await api(`/api/notes/${currentNoteId}`, { method: "DELETE" });
    currentNoteId = null;
    $("#editor-empty").classList.remove("hidden");
    $("#editor-content").classList.add("hidden");
    await fetchNotes();
}

function newNote() {
    currentNoteId = null;
    $("#note-title").value = "";
    $("#note-tags").value = "";
    $("#note-body").value = "";
    $("#editor-empty").classList.add("hidden");
    $("#editor-content").classList.remove("hidden");
    if (isPreview) togglePreview();
    $("#note-title").focus();
}

function togglePreview() {
    isPreview = !isPreview;
    if (isPreview) {
        $("#note-body").classList.add("hidden");
        $("#note-preview").classList.remove("hidden");
        $("#note-preview").innerHTML = marked.parse($("#note-body").value);
        $("#preview-toggle").textContent = "Edit";
    } else {
        $("#note-body").classList.remove("hidden");
        $("#note-preview").classList.add("hidden");
        $("#preview-toggle").textContent = "Preview";
    }
}

// --- Search ---
async function searchNotes(query) {
    if (!query.trim()) {
        await fetchNotes();
        return;
    }
    const results = await api("/api/search", {
        method: "POST",
        body: JSON.stringify({ query, top_k: 10 }),
    });
    renderNoteList(results, true);
}

// --- Assistant ---
async function askAssistant() {
    const input = $("#assistant-question");
    const question = input.value.trim();
    if (!question) return;

    input.value = "";
    appendMessage(question, "user");

    try {
        const res = await api("/api/assistant", {
            method: "POST",
            body: JSON.stringify({ question }),
        });
        const sourcesHtml = res.sources.length
            ? `<div class="sources">Sources: ${res.sources.map((s) => escapeHtml(s.title)).join(", ")}</div>`
            : "";
        appendMessage(marked.parse(res.answer) + sourcesHtml, "assistant", true);
    } catch (e) {
        appendMessage(e.message, "error");
    }
}

function appendMessage(content, type, isHtml = false) {
    const div = document.createElement("div");
    div.className = `msg ${type}`;
    if (isHtml) {
        div.innerHTML = content;
    } else {
        div.textContent = content;
    }
    const container = $("#assistant-messages");
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// --- Utilities ---
function escapeHtml(str) {
    const el = document.createElement("span");
    el.textContent = str;
    return el.innerHTML;
}

// --- Keyboard shortcuts ---
document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        saveNote();
    }
});

// --- Event listeners ---
$("#new-note-btn").addEventListener("click", newNote);
$("#save-btn").addEventListener("click", saveNote);
$("#delete-btn").addEventListener("click", deleteNote);
$("#preview-toggle").addEventListener("click", togglePreview);
$("#ask-btn").addEventListener("click", askAssistant);
$("#assistant-question").addEventListener("keydown", (e) => {
    if (e.key === "Enter") askAssistant();
});
$("#search-input").addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => searchNotes(e.target.value), 300);
});

// --- Init ---
fetchNotes();
