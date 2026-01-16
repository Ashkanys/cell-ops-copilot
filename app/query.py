import faiss
import numpy as np

from app.config import SETTINGS
from app.models import Chunk
from app.utils import read_jsonl
from app.embedder import Embedder

def format_citation(c: Chunk) -> str:
    step_part = ""
    if c.step_start is not None and c.step_end is not None:
        step_part = f" • steps {c.step_start}–{c.step_end}"
    sub = f" • {c.subsection}" if c.subsection else ""
    return f"{c.doc_id} • {c.section}{sub}{step_part} (L{c.line_start}–L{c.line_end})"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True, help="Query text")
    ap.add_argument("--k", type=int, default=SETTINGS.top_k)
    args = ap.parse_args()

    index = faiss.read_index(str(SETTINGS.index_dir / "faiss.index"))
    meta = [Chunk(**row) for row in read_jsonl(SETTINGS.index_dir / "meta.jsonl")]

    embedder = Embedder(SETTINGS.embedding_model_name)
    q = embedder.embed_query(args.q).reshape(1, -1).astype("float32")

    scores, idxs = index.search(q, args.k)

    for rank, (i, s) in enumerate(zip(idxs[0], scores[0]), start=1):
        c = meta[int(i)]
        print(f"\n#{rank} score={float(s):.4f} | {format_citation(c)}\n")
        print(c.text[:1500])


if __name__ == "__main__":
    main()
