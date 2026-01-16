import re
from typing import List, Optional, Tuple

from sympy import sec
from app.models import Document, Chunk
from app.config import SETTINGS
from app.utils import stable_chunk_id, read_jsonl, write_jsonl


HEADER_RE = re.compile(r"^(#{1,4})\s+(.*)\s*$")
STEP_RE = re.compile(r"^\s*(\d+)\s*[\).\:-]\s+(.*)$")


def classify_section(header_text: str) -> str:
    h = header_text.strip().lower()

    # normalize a bit
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


def chunk_procedure_block(
    doc: Document,
    section: str,
    subsection: Optional[str],
    start_line_idx: int,
    block_lines: List[str],
) -> List[Chunk]:
    """
    Takes a contiguous "Procedure" block and chunks it by grouping numbered steps.
    """
    chunks: List[Chunk] = []

    # Identify numbered steps + their line offsets within block
    steps: List[Tuple[int, int, str]] = []  # (step_num, local_line_idx, raw_line)
    for i, ln in enumerate(block_lines):
        m = STEP_RE.match(ln)
        if m:
            steps.append((int(m.group(1)), i, ln))

    # If no numbered steps, fallback to char-based chunking
    if not steps:
        return chunk_by_chars(doc, section, subsection, start_line_idx, block_lines)

    # Build step-range chunks
    max_steps = SETTINGS.procedure_steps_per_chunk
    for i in range(0, len(steps), max_steps):
        group = steps[i:i + max_steps]
        step_start = group[0][0]
        step_end = group[-1][0]

        local_start = group[0][1]
        # end at next group's start or end of block
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
            line_start=line_start + 1,  # 1-based for humans
            line_end=line_end + 1,
            step_start=step_start,
            step_end=step_end,
            text=text,
            tags={}
        ))

    return chunks


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
            chunks.extend(chunk_procedure_block(doc, current_section, current_subsection, block_start_line_idx, current_block_lines))
        else:
            chunks.extend(chunk_by_chars(doc, current_section, current_subsection, block_start_line_idx, current_block_lines))
        current_block_lines = []

    for idx, ln in enumerate(doc.lines):
        m = HEADER_RE.match(ln)
        if m:
            # New header: flush previous block
            flush_block(idx - 1)

            header_text = m.group(2).strip()
            sec = classify_section(header_text)

            # Track section + subsection
            if m.group(1) == "#":
                current_section = sec
                current_subsection = None
            elif m.group(1) == "##":
                # For ## headers: treat as subsection only, don't change section unless explicitly recognized
                if sec != "Other":
                    current_section = sec
                current_subsection = header_text
            else:
                # deeper headers become subsection names
                current_subsection = header_text

            block_start_line_idx = idx + 1  # skips the header line in block
            current_block_lines = []
        else:
            if not current_block_lines:
                block_start_line_idx = idx
            current_block_lines.append(ln)

    flush_block(len(doc.lines) - 1)
    return chunks


def main():
    docs = [Document(**row) for row in read_jsonl(SETTINGS.processed_dir / "docs.jsonl")]
    all_chunks: List[Chunk] = []
    for d in docs:
        all_chunks.extend(chunk_document(d))

    def is_useful_chunk(c: Chunk) -> bool:
    # remove super-short chunks like "# Passaging adherent cells"
        return len(c.text.strip()) >= 80 and len(c.text.strip().split()) >= 12

    all_chunks = [c for c in all_chunks if is_useful_chunk(c)]
    
    out = SETTINGS.processed_dir / "chunks.jsonl"
    write_jsonl(out, (c.model_dump() for c in all_chunks))
    print(f"Wrote {len(all_chunks)} chunks → {out}")


if __name__ == "__main__":
    main()
