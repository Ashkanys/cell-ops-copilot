import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# def read_markdown_files(docs_dir: Path) -> List[Dict]:
#     items = []
#     for p in sorted(docs_dir.glob("*.md")):
#         text = p.read_text(encoding="utf-8")
#         items.append({"source_file": p.name, "text": text})
#     return items


# def chunk_markdown(md: str) -> List[str]:
#     """
#     Simple chunker:
#     - split by headings
#     - keep non-empty blocks
#     """
#     lines = md.splitlines()
#     chunks = []
#     cur = []
#     for line in lines:
#         if line.strip().startswith("#") and cur:
#             block = "\n".join(cur).strip()
#             if block:
#                 chunks.append(block)
#             cur = [line]
#         else:
#             cur.append(line)
#     block = "\n".join(cur).strip()
#     if block:
#         chunks.append(block)

#     # Optional: further split very large chunks
#     final = []
#     for c in chunks:
#         if len(c) <= 1600:
#             final.append(c)
#         else:
#             # split on blank lines
#             parts = [p.strip() for p in c.split("\n\n") if p.strip()]
#             buf = ""
#             for part in parts:
#                 if len(buf) + len(part) + 2 <= 1600:
#                     buf = (buf + "\n\n" + part).strip()
#                 else:
#                     if buf:
#                         final.append(buf)
#                     buf = part
#             if buf:
#                 final.append(buf)
#     return final


# def main():
#     docs_dir = Path("docs/sops")
#     out_dir = Path("indexes")
#     out_dir.mkdir(parents=True, exist_ok=True)

#     model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

#     docs = read_markdown_files(docs_dir)

#     rows = []
#     for d in docs:
#         chunks = chunk_markdown(d["text"])
#         for i, ch in enumerate(chunks):
#             rows.append({
#                 "chunk_id": f'{d["source_file"]}::chunk{i:03d}',
#                 "source_file": d["source_file"],
#                 "text": ch
#             })

#     texts = [r["text"] for r in rows]
#     emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
#     emb = np.asarray(emb, dtype="float32")

#     dim = emb.shape[1]
#     index = faiss.IndexFlatIP(dim)  # cosine-sim via normalized vectors + inner product
#     index.add(emb)

#     faiss.write_index(index, str(out_dir / "faiss.index"))

#     with (out_dir / "chunks.jsonl").open("w", encoding="utf-8") as f:
#         for r in rows:
#             f.write(json.dumps(r, ensure_ascii=False) + "\n")

#     print(f"Built index with {len(rows)} chunks from {len(docs)} SOP files.")
#     print(f"Saved: {out_dir/'faiss.index'} and {out_dir/'chunks.jsonl'}")


# if __name__ == "__main__":
#     main()


CORPUS_DIR = Path("docs/sops")
OUT_DIR = Path("indexes")
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_CHARS_PER_CHUNK = 2200  # if a section is longer, split further


def read_markdown_files(folder: Path) -> List[Tuple[str, str]]:
    files = sorted(folder.glob("*.md"))
    items = []
    for fp in files:
        text = fp.read_text(encoding="utf-8")
        items.append((fp.name, text))
    return items


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\s\-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s


def split_by_h2_sections(md: str) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Returns (title, sections) where sections is list of (section_name, section_text).
    Splits by '## ' headings. Keeps content under each heading.
    """
    lines = md.splitlines()
    title = ""
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()

    # Find all H2 headings
    h2_indices = [i for i, line in enumerate(lines) if line.startswith("## ")]
    if not h2_indices:
        # fallback: treat whole doc as one section
        return title, [("Document", md.strip())]

    sections = []
    for idx, start in enumerate(h2_indices):
        end = h2_indices[idx + 1] if idx + 1 < len(h2_indices) else len(lines)
        section_name = lines[start][3:].strip()
        section_text = "\n".join(lines[start:end]).strip()
        sections.append((section_name, section_text))
    return title, sections


def subchunk_if_needed(section_text: str) -> List[str]:
    """
    If a section is too big, split on blank lines or numbered-step boundaries.
    Keeps chunks reasonably coherent.
    """
    if len(section_text) <= MAX_CHARS_PER_CHUNK:
        return [section_text]

    # First try splitting by '### ' (H3) if present
    if "### " in section_text:
        parts = re.split(r"(?m)^(### .+)$", section_text)
        chunks = []
        buf = ""
        for p in parts:
            if p.startswith("### "):
                if buf.strip():
                    chunks.extend(subchunk_if_needed(buf.strip()))
                buf = p
            else:
                buf += "\n" + p
        if buf.strip():
            chunks.extend(subchunk_if_needed(buf.strip()))
        return chunks

    # Otherwise split by blank lines
    paras = [p.strip() for p in section_text.split("\n\n") if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 2 <= MAX_CHARS_PER_CHUNK:
            cur = (cur + "\n\n" + p).strip()
        else:
            if cur.strip():
                chunks.append(cur.strip())
            cur = p
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def build_chunks() -> List[Dict[str, Any]]:
    docs = read_markdown_files(CORPUS_DIR)
    all_chunks: List[Dict[str, Any]] = []
    for filename, md in docs:
        title, sections = split_by_h2_sections(md)
        for sec_name, sec_text in sections:
            sec_slug = slugify(sec_name) if sec_name else "section"
            subchunks = subchunk_if_needed(sec_text)
            for j, chunk_text in enumerate(subchunks):
                chunk_id = f"{filename}::{sec_slug}::{j}"
                all_chunks.append({
                    "chunk_id": chunk_id,
                    "doc_file": filename,
                    "doc_title": title or filename,
                    "section": sec_name or "Document",
                    "anchor": f"{filename}#{sec_slug}",
                    "text": chunk_text,
                })
    return all_chunks


def main():
    if not CORPUS_DIR.exists():
        raise SystemExit(f"Missing corpus folder: {CORPUS_DIR.resolve()}")

    chunks = build_chunks()
    if not chunks:
        raise SystemExit("No chunks built. Check your docs/seed_corpus/*.md files.")

    print(f"Built {len(chunks)} chunks from {len(list(CORPUS_DIR.glob('*.md')))} markdown files.")

    model = SentenceTransformer(MODEL_NAME)
    texts = [c["text"] for c in chunks]
    emb = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    emb = np.asarray(emb, dtype=np.float32)

    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine similarity via normalized vectors
    index.add(emb)

    faiss.write_index(index, str(OUT_DIR / "faiss.index"))
    (OUT_DIR / "meta.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved index to {OUT_DIR/'faiss.index'} and metadata to {OUT_DIR/'meta.json'}")


if __name__ == "__main__":
    main()
