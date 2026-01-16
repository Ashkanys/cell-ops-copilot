from pathlib import Path
from typing import List
from app.models import Document
from app.config import SETTINGS
from app.utils import get_git_sha, write_jsonl


def infer_doc_id(filename: str) -> str:
    # sop-tc-007-counting.md -> sop-tc-007
    # safe fallback: stem
    stem = Path(filename).stem
    parts = stem.split("-")
    if len(parts) >= 3 and parts[0] == "sop" and parts[1] == "tc":
        return "-".join(parts[:3])
    return stem


def infer_title(lines: List[str], fallback: str) -> str:
    for ln in lines:
        if ln.strip().startswith("# "):
            return ln.strip()[2:].strip()
    return fallback


def load_documents() -> List[Document]:
    sha = get_git_sha()
    docs: List[Document] = []
    for p in sorted(SETTINGS.sops_dir.glob("*.md")):
        lines = p.read_text(encoding="utf-8").splitlines()
        doc_id = infer_doc_id(p.name)
        title = infer_title(lines, fallback=p.stem)
        docs.append(Document(
            doc_id=doc_id,
            title=title,
            source_path=str(p),
            version=sha,
            lines=lines
        ))
    return docs


def main():
    docs = load_documents()
    out = SETTINGS.processed_dir / "docs.jsonl"
    write_jsonl(out, (d.model_dump() for d in docs))
    print(f"Wrote {len(docs)} docs → {out}")


if __name__ == "__main__":
    main()
