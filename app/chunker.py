from app.utils import stable_chunk_id, read_jsonl, write_jsonl
# app/chunker.py
import re
from typing import List, Optional, Tuple, Dict, Iterable, TypeVar

from app.config import SETTINGS
from app.models import Document, Chunk


# -------------------------
# Regex
# -------------------------

# Markdown headers: # / ## / ### / ####
HEADER_RE = re.compile(r"^(#{1,4})\s+(.*)\s*$")

# Numbered procedure steps: "1) ...", "2. ...", "3 - ..."
STEP_RE = re.compile(r"^\s*(\d+)\s*[\).\:-]\s+(.*)$")

# Subprocedure separators like "A) ...", "B. ...", "C - ..."
# NOTE: letters only (avoid colliding with STEP_RE)
SUBPROC_RE = re.compile(r"^\s*([A-Za-z])\s*[\).\:-]\s+(.*)$")

# Strip leading enumerator like "A) " or "1) " from titles
SUBSECTION_PREFIX_RE = re.compile(r"^\s*([A-Za-z]|\d+)\s*[\).\:-]\s+")


def normalize_subsection_title(s: str) -> str:
    """
    Normalizes subsection titles:
      "A) Countess 3" -> "Countess 3"
      "B. Hemocytometer" -> "Hemocytometer"
    """
    return SUBSECTION_PREFIX_RE.sub("", s.strip()).strip()


# -------------------------
# Section classification
# -------------------------

def classify_section(header_text: str) -> str:
    h = header_text.strip().lower()
    h = h.replace("&", "and")

    if "purpose" in h or "goal" in h or "objective" in h:
        return "Purpose"
    if "scope" in h or "applies to" in h:
        return "Scope"
    if "safety" in h or "biosafety" in h or "ppe" in h or "hazard" in h:
        return "Safety"
    if "material" in h or "reagent" in h or "consumable" in h or "equipment" in h or "disinfectant" in h or "suppl" in h:
        return "Materials"
    if "preparation" in h or "setup" in h or "before you begin" in h:
        return "Preparation"
    if "procedure" in h or "steps" in h or "protocol" in h or "method" in h:
        return "Procedure"
    if "critical" in h or "critical point" in h or "warnings" in h or "caution" in h or "do not" == h.strip():
        return "Critical Points"
    if "qc" in h or "quality" in h or "acceptance" in h or "criteria" in h:
        return "QC"
    if "reference" in h or "citation" in h or "link" in h:
        return "References"
    if "troubleshoot" in h or "troubleshooting" in h or "common issues" in h:
        return "Troubleshooting"

    return "Other"


def join_lines(lines: List[str]) -> str:
    return "\n".join(lines).strip()


# -------------------------
# Chunking functions
# -------------------------

def chunk_by_chars(
    doc: Document,
    section: str,
    subsection: Optional[str],
    start_line_idx: int,
    block_lines: List[str],
) -> List[Chunk]:
    chunks: List[Chunk] = []
    max_chars = SETTINGS.max_chars

    acc: List[str] = []
    acc_start = 0
    cur_chars = 0

    def flush(end_local_idx: int):
        nonlocal acc, acc_start, cur_chars
        if not acc:
            return
        text = join_lines(acc)
        line_start = start_line_idx + acc_start
        line_end = start_line_idx + end_local_idx
        chunk_id = stable_chunk_id(doc.doc_id, section, subsection or "", str(line_start), str(line_end))
        chunks.append(Chunk(
            chunk_id=chunk_id,
            doc_id=doc.doc_id,
            doc_title=doc.title,
            source_path=doc.source_path,
            version=doc.version,
            section=section,
            subsection=subsection,
            line_start=line_start + 1,
            line_end=line_end + 1,
            text=text,
            tags={}
        ))
        acc = []
        acc_start = end_local_idx + 1
        cur_chars = 0

    for i, ln in enumerate(block_lines):
        add_len = len(ln) + 1
        if acc and cur_chars + add_len > max_chars:
            flush(i - 1)
        if not acc:
            acc_start = i
        acc.append(ln)
        cur_chars += add_len

    flush(len(block_lines) - 1)
    return chunks


def chunk_procedure_block(
    doc: Document,
    section: str,
    subsection: Optional[str],
    start_line_idx: int,
    block_lines: List[str],
) -> List[Chunk]:
    """
    Takes a contiguous Procedure block and chunks it by grouping numbered steps.
    """
    chunks: List[Chunk] = []

    # Identify numbered steps + their line offsets within block
    steps: List[Tuple[int, int, str]] = []
    for i, ln in enumerate(block_lines):
        m = STEP_RE.match(ln)
        if m:
            steps.append((int(m.group(1)), i, ln))

    # If no numbered steps, fallback to char-based chunking
    if not steps:
        return chunk_by_chars(doc, section, subsection, start_line_idx, block_lines)

    max_steps = SETTINGS.procedure_steps_per_chunk
    for i in range(0, len(steps), max_steps):
        group = steps[i:i + max_steps]
        step_start = group[0][0]
        step_end = group[-1][0]

        local_start = group[0][1]
        local_end = (steps[i + max_steps][1] if (i + max_steps) < len(steps) else len(block_lines)) - 1

        lines_slice = block_lines[local_start:local_end + 1]
        text = join_lines(lines_slice)

        line_start = start_line_idx + local_start
        line_end = start_line_idx + local_end

        chunk_id = stable_chunk_id(doc.doc_id, section, subsection or "", str(line_start), str(line_end))

        chunks.append(Chunk(
            chunk_id=chunk_id,
            doc_id=doc.doc_id,
            doc_title=doc.title,
            source_path=doc.source_path,
            version=doc.version,
            section=section,
            subsection=subsection,
            line_start=line_start + 1,
            line_end=line_end + 1,
            step_start=step_start,
            step_end=step_end,
            text=text,
            tags={}
        ))

    return chunks


# -------------------------
# Document-level chunking
# -------------------------

def chunk_document(doc: Document) -> List[Chunk]:
    chunks: List[Chunk] = []

    current_section = "Other"
    current_subsection: Optional[str] = None
    current_block_lines: List[str] = []
    block_start_line_idx = 0

    def flush_block(end_line_idx: int):
        nonlocal current_block_lines, block_start_line_idx, chunks
        if not current_block_lines:
            return
        if current_section == "Procedure":
            chunks.extend(
                chunk_procedure_block(
                    doc, current_section, current_subsection, block_start_line_idx, current_block_lines
                )
            )
        else:
            chunks.extend(
                chunk_by_chars(
                    doc, current_section, current_subsection, block_start_line_idx, current_block_lines
                )
            )
        current_block_lines = []

    for idx, ln in enumerate(doc.lines):
        m = HEADER_RE.match(ln)
        if m:
            # Flush previous block (up to the line before this header)
            flush_block(idx - 1)

            header_level = m.group(1)  # "#", "##", "###", "####"
            header_text = m.group(2).strip()
            sec = classify_section(header_text)

            if header_level == "#":
                # Top-level title: treat as doc title-ish header -> reset subsection
                current_section = sec
                current_subsection = None

            elif header_level == "##":
                # If this is a recognized main section (Procedure, Safety, etc.):
                # set section and reset subsection to None
                if sec != "Other":
                    current_section = sec
                    current_subsection = None
                else:
                    # Rare: a ## header that isn't a known section -> treat as subsection label
                    current_subsection = normalize_subsection_title(header_text)

            else:
                # ### / #### headers are subsection labels (e.g. "A) Countess3")
                current_subsection = normalize_subsection_title(header_text)

            block_start_line_idx = idx + 1
            current_block_lines = []  # keep header line in the chunk text
        else:
            if not current_block_lines:
                block_start_line_idx = idx
            current_block_lines.append(ln)

    flush_block(len(doc.lines) - 1)
    return chunks


# -------------------------
# Entry point
# -------------------------

def main():
    docs = [Document(**row) for row in read_jsonl(SETTINGS.processed_dir / "docs.jsonl")]
    all_chunks: List[Chunk] = []
    for d in docs:
        all_chunks.extend(chunk_document(d))

    # Optional filtering (you had it commented out)
    def is_useful_chunk(c: Chunk) -> bool:
        return len(c.text.strip()) >= SETTINGS.min_chars and len(c.text.strip().split()) >= SETTINGS.min_words

    # If you want filtering, uncomment:
    all_chunks = [c for c in all_chunks if is_useful_chunk(c) and c.section != "References"]

    out = SETTINGS.processed_dir / "chunks.jsonl"
    write_jsonl(out, (c.model_dump() for c in all_chunks))
    print(f"Wrote {len(all_chunks)} chunks → {out}")


if __name__ == "__main__":
    main()
