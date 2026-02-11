import json
from pathlib import Path
import faiss  # type: ignore

from app.config import SETTINGS
from app.models import Chunk
from app.utils import read_jsonl
from app.embedder import Embedder
from app.llm_client import get_llm
from app.rag_answer import answer_query


def load_gold(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def main():
    gold = load_gold(Path("eval/gold_questions.jsonl"))

    index = faiss.read_index(str(SETTINGS.index_dir / "faiss.index"))
    meta = [Chunk(**row) for row in read_jsonl(SETTINGS.index_dir / "meta.jsonl")]
    embedder = Embedder(SETTINGS.embedding_model_name)
    llm = get_llm()

    n = len(gold)
    with_citations = 0
    abstained = 0

    for ex in gold:
        q = ex["query"]
        ans = answer_query(llm, index, meta, embedder, q, k=SETTINGS.top_k)

        if ans.abstained:
            abstained += 1
        if ans.citations:
            with_citations += 1

    print(f"Examples: {n}")
    print(f"Answers with >=1 citation: {with_citations}/{n} = {with_citations/n:.3f}")
    print(f"Abstained: {abstained}/{n} = {abstained/n:.3f}")


if __name__ == "__main__":
    main()
