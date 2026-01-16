import json
import statistics
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, TypeVar, Iterable

import faiss

from app.config import SETTINGS
from app.models import Chunk
from app.utils import read_jsonl
from app.embedder import Embedder

T = TypeVar("T")


def load_gold(path: Path) -> List[Dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _as_set(x) -> Set[str]:
    if x is None:
        return set()
    if isinstance(x, list):
        return set(x)
    return {x}


def get_expected_doc_ids(ex: Dict) -> Set[str]:
    # supports: expected_doc_ids (list), expected_doc_id (str)
    return _as_set(ex.get("expected_doc_ids") or ex.get("expected_doc_id"))


def get_expected_sections(ex: Dict) -> Set[str]:
    # supports: expected_sections (list), expected_section (str)
    return _as_set(ex.get("expected_sections") or ex.get("expected_section"))


def get_expected_pairs(ex: Dict) -> Set[Tuple[str, str]]:
    """
    Preferred gold format:
      {"expected":[{"doc_id":"...", "section":"procedure"}, ...]}
    Falls back to doc_ids + sections if no explicit pairs exist.
    """
    pairs = set()
    if "expected" in ex and isinstance(ex["expected"], list):
        for item in ex["expected"]:
            doc_id = item.get("doc_id")
            section = item.get("section")
            if doc_id and section:
                pairs.add((doc_id, section))
        if pairs:
            return pairs

    # Fallback (less precise): treat any (doc_id, section) combination as acceptable
    # Only use this if you truly mean "any of these docs" AND "any of these sections"
    doc_ids = get_expected_doc_ids(ex)
    sections = get_expected_sections(ex)
    if doc_ids and sections:
        return {(d, s) for d in doc_ids for s in sections}

    return set()


def first_hit_rank(items: List, predicate) -> Optional[int]:
    """
    Returns 1-based rank of first item satisfying predicate, else None.
    """
    for i, it in enumerate(items, start=1):
        if predicate(it):
            return i
    return None


def safe_median(xs: List[int]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    return float(statistics.median(xs))

def unique_in_order(xs: Iterable[T]) -> List[T]:
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def main():
    gold = load_gold(Path("eval/gold_questions.jsonl"))
    index = faiss.read_index(str(SETTINGS.index_dir / "faiss.index"))
    meta = [Chunk(**row) for row in read_jsonl(SETTINGS.index_dir / "meta.jsonl")]
    embedder = Embedder(SETTINGS.embedding_model_name)

    ks = [1, 3, 5, 10]
    K = max(ks)

    # hit@k counters
    hits_doc = {k: 0 for k in ks}
    hits_pair = {k: 0 for k in ks}

    # rank / first_hit_k tracking (1..K), None if miss
    ranks_doc: List[Optional[int]] = []
    ranks_pair: List[Optional[int]] = []

    for ex in gold:
        q = embedder.embed_query(ex["query"]).reshape(1, -1).astype("float32")
        K_search = max(50, K * 10)   # retrieve more chunks, then dedupe down
        scores, idxs = index.search(q, K_search)
        #print(f"Query: {ex['query']}")
        # FAISS can return -1 if something goes wrong / empty index
        idx_list = [int(i) for i in idxs[0] if int(i) >= 0]
        retrieved_chunks = [meta[i] for i in idx_list]
        #print(f"Retrieved Chunks: {[c.doc_id + (':' + c.section if hasattr(c, 'section') and c.section else '') for c in retrieved_chunks]}")   
        # What we evaluate against
        exp_docs = get_expected_doc_ids(ex)
        exp_pairs = get_expected_pairs(ex)

        if not exp_docs and exp_pairs:
            exp_docs = {d for (d, _) in exp_pairs}

        # Chunk-level lists
        doc_ids_by_chunk = [c.doc_id for c in retrieved_chunks]
        pairs_by_chunk = [(c.doc_id, getattr(c, "section", None)) for c in retrieved_chunks]

        # Dedup in rank order (what a user actually experiences)
        retrieved_doc_ids = unique_in_order(doc_ids_by_chunk)
        retrieved_pairs = unique_in_order(pairs_by_chunk)

        # Trim to K
        retrieved_doc_ids = retrieved_doc_ids[:K]
        retrieved_pairs = retrieved_pairs[:K]   

        # --- Doc-only metrics ---
        rank_doc = first_hit_rank(retrieved_doc_ids, lambda d: d in exp_docs)
        ranks_doc.append(rank_doc)

        for k in ks:
            topk = set(retrieved_doc_ids[:k])
            if exp_docs.intersection(topk):
                hits_doc[k] += 1

        # --- Doc+Section metrics ---
        if exp_pairs:
            rank_pair = first_hit_rank(retrieved_pairs, lambda p: p in exp_pairs)
        else:
            # If no expected section provided, treat doc+section as "not applicable"
            rank_pair = None
        ranks_pair.append(rank_pair)

        for k in ks:
            if not exp_pairs:
                continue
            topk_pairs = set(retrieved_pairs[:k])
            if exp_pairs.intersection(topk_pairs):
                hits_pair[k] += 1
        
        # print("GOLD exp_docs:", exp_docs)
        # print("GOLD exp_pairs:", exp_pairs)
        # print("TOP retrieved_doc_ids:", retrieved_doc_ids[:10])
        # print("TOP retrieved_pairs:", retrieved_pairs[:10])
        # break
    

    n = len(gold)

    def mrr_at_10(ranks: List[Optional[int]]) -> float:
        return sum((1.0 / r) if r else 0.0 for r in ranks) / max(1, n)

    mrr_doc = mrr_at_10(ranks_doc)
    mrr_pair = mrr_at_10(ranks_pair)

    # Optional combined score: weight section correctness higher
    combined = 0.3 * mrr_doc + 0.7 * mrr_pair

    print(f"Examples: {n}")

    print("\n=== DOC-ONLY ===")
    for k in ks:
        print(f"hit@{k}: {hits_doc[k]}/{n} = {hits_doc[k]/n:.3f}")
    doc_median = safe_median(ranks_doc)
    doc_miss = sum(1 for r in ranks_doc if r is None)
    print(f"first_hit_k@10 median: {doc_median if doc_median is not None else 'NA'} | miss@10: {doc_miss}/{n}")
    print(f"MRR@10 (doc): {mrr_doc:.3f}")

    print("\n=== DOC+SECTION ===")
    if any(r is not None for r in ranks_pair):
        for k in ks:
            print(f"hit@{k}: {hits_pair[k]}/{n} = {hits_pair[k]/n:.3f}")
        pair_median = safe_median(ranks_pair)
        pair_miss = sum(1 for r in ranks_pair if r is None)
        print(f"first_hit_k@10 median: {pair_median if pair_median is not None else 'NA'} | miss@10: {pair_miss}/{n}")
        print(f"MRR@10 (doc+section): {mrr_pair:.3f}")
        print(f"\nCombined score (0.3*doc + 0.7*doc+section): {combined:.3f}")
    else:
        print("No section labels found in gold (or meta lacks chunk.section). Add expected section info to enable this metric.")


if __name__ == "__main__":
    main()
