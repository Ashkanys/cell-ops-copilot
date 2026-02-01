"""
app/eval.py

Evaluation for Cell-Ops-Copilot retrieval.

Supports:
1) Retrieval metrics on answerable questions:
   - hit@k for:
       (a) doc_id
       (b) (doc_id, section)
       (c) (doc_id, section, subsection)
   - first_hit_k (rank) and MRR@K for each level
2) no_answer: true support via score-threshold abstention
   - abstain accuracy on no_answer questions
   - false abstain rate on answerable questions

Gold JSONL formats supported (one object per line):

Preferred (supports subsection):
  {"query":"...", "expected":[{"doc_id":"sop-tc-007","section":"Procedure","subsection":"Countess 3"}]}

Also ok (no subsection):
  {"query":"...", "expected":[{"doc_id":"sop-tc-006","section":"Critical Points"}]}

Alternative fallback (section only):
  {"query":"...", "expected_doc_ids":["sop-tc-002"], "expected_sections":["Procedure"]}

No-answer:
  {"query":"...", "no_answer": true}

Notes:
- Section/subsection strings are case-sensitive; keep consistent with meta.jsonl.
- This eval does NOT compare answer text; it evaluates retrieval correctness + abstention behavior.
"""

import json
import statistics
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Iterable, TypeVar

import faiss

from app.config import SETTINGS
from app.models import Chunk
from app.utils import read_jsonl
from app.embedder import Embedder


# -------------------------
# Helpers
# -------------------------

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
    return _as_set(ex.get("expected_doc_ids") or ex.get("expected_doc_id"))


def get_expected_sections(ex: Dict) -> Set[str]:
    return _as_set(ex.get("expected_sections") or ex.get("expected_section"))


def get_expected_pairs(ex: Dict) -> Set[Tuple[str, str]]:
    """
    Returns expected (doc_id, section) pairs.

    Preferred gold format:
      {"expected":[{"doc_id":"...", "section":"Procedure"}, ...]}

    Fallback:
      expected_doc_ids + expected_sections -> cartesian product
    """
    pairs: Set[Tuple[str, str]] = set()

    exp = ex.get("expected", None)
    if isinstance(exp, list):
        for item in exp:
            doc_id = item.get("doc_id")
            section = item.get("section")
            if doc_id and section:
                pairs.add((doc_id, section))
        if pairs:
            return pairs

    doc_ids = get_expected_doc_ids(ex)
    sections = get_expected_sections(ex)
    if doc_ids and sections:
        return {(d, s) for d in doc_ids for s in sections}

    return set()


def get_expected_triples(ex: Dict) -> Set[Tuple[str, str, Optional[str]]]:
    """
    Returns expected (doc_id, section, subsection) triples, when present.

    Gold format:
      {"expected":[{"doc_id":"...", "section":"Procedure", "subsection":"Countess 3"}, ...]}

    We only include triples for items that include doc_id + section + subsection.
    (subsection can be None, but only if explicitly provided as null.)
    """
    triples: Set[Tuple[str, str, Optional[str]]] = set()

    exp = ex.get("expected", None)
    if isinstance(exp, list):
        for item in exp:
            doc_id = item.get("doc_id")
            section = item.get("section")
            # subsection may be omitted; only build triple if key exists
            if "subsection" in item:
                subsection = item.get("subsection")  # may be None
                if doc_id and section:
                    triples.add((doc_id, section, subsection))
    return triples


def first_hit_rank(items: List, predicate) -> Optional[int]:
    """1-based rank of first item satisfying predicate, else None."""
    for i, it in enumerate(items, start=1):
        if predicate(it):
            return i
    return None


def safe_median(ranks: List[Optional[int]]) -> Optional[float]:
    xs = [r for r in ranks if r is not None]
    if not xs:
        return None
    return float(statistics.median(xs))


T = TypeVar("T")


def unique_in_order(xs: Iterable[T]) -> List[T]:
    seen = set()
    out: List[T] = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def mrr(ranks: List[Optional[int]], denom: int) -> float:
    if denom <= 0:
        return 0.0
    return sum((1.0 / r) if r else 0.0 for r in ranks) / denom


def should_abstain(index, top_score: Optional[float]) -> bool:
    """
    Uses SETTINGS.NO_ANSWER_THRESHOLD and FAISS metric_type to decide abstention.

    - Inner product (cosine-like when normalized): higher is better -> abstain if score < threshold
    - L2 distance: lower is better -> abstain if score > threshold
    """
    if top_score is None:
        return True

    thr = getattr(SETTINGS, "NO_ANSWER_THRESHOLD", None)
    if thr is None:
        return False

    metric_type = getattr(index, "metric_type", None)
    if metric_type == faiss.METRIC_INNER_PRODUCT:
        return float(top_score) < float(thr)

    # default: treat as distance (e.g. L2)
    return float(top_score) > float(thr)


# -------------------------
# Main
# -------------------------

def main():
    gold = load_gold(Path("eval/gold_questions.jsonl"))
    index = faiss.read_index(str(SETTINGS.index_dir / "faiss.index"))
    meta = [Chunk(**row) for row in read_jsonl(SETTINGS.index_dir / "meta.jsonl")]
    embedder = Embedder(SETTINGS.embedding_model_name)

    ks = [1, 3, 5, 10]
    K = max(ks)

    # Retrieval counters (answerable only)
    hits_doc = {k: 0 for k in ks}
    hits_pair = {k: 0 for k in ks}
    hits_triple = {k: 0 for k in ks}
    answers_with_section_gold = {k: [] for k in ks}

    ranks_doc: List[Optional[int]] = []
    ranks_pair: List[Optional[int]] = []
    ranks_triple: List[Optional[int]] = []

    # No-answer counters
    n_total = len(gold)
    n_answerable = 0
    n_no_answer = 0

    no_answer_correct = 0
    no_answer_wrong = 0
    false_abstain = 0

    # Denominators for section/triple metrics (only count examples that specify them)
    n_answerable_with_section_gold = 0
    n_answerable_with_subsection_gold = 0

    for ex in gold:
        query = ex["query"]
        is_no_answer = bool(ex.get("no_answer", False))

        q = embedder.embed_query(query).reshape(1, -1).astype("float32")

        K_search = max(30, K * 10)
        scores, idxs = index.search(q, K_search)

        top_score = None
        if scores is not None and len(scores) > 0 and len(scores[0]) > 0:
            top_score = float(scores[0][0])

        pred_no_answer = should_abstain(index, top_score)

        # --- Handle gold no-answer examples ---
        if is_no_answer:
            n_no_answer += 1
            if pred_no_answer:
                no_answer_correct += 1
            else:
                no_answer_wrong += 1
            continue

        # --- Answerable example ---
        n_answerable += 1

        if pred_no_answer:
            false_abstain += 1
            ranks_doc.append(None)
            ranks_pair.append(None)
            ranks_triple.append(None)
            continue

        idx_list = [int(i) for i in idxs[0] if int(i) >= 0]
        retrieved_chunks = [meta[i] for i in idx_list]

        # Expected targets
        exp_docs = get_expected_doc_ids(ex)
        exp_pairs = get_expected_pairs(ex)
        exp_triples = get_expected_triples(ex)

        # If gold only provided expected pairs, derive expected docs for doc-only eval
        if not exp_docs and exp_pairs:
            exp_docs = {d for (d, _) in exp_pairs}
        # If gold only provided triples, derive pairs+docs too (makes doc-only and doc+sec work)
        if exp_triples:
            if not exp_pairs:
                exp_pairs = {(d, s) for (d, s, _) in exp_triples}
            if not exp_docs:
                exp_docs = {d for (d, _, _) in exp_triples}

        if exp_pairs:
            n_answerable_with_section_gold += 1
        if exp_triples:
            n_answerable_with_subsection_gold += 1

        # Build chunk-level sequences
        doc_ids_by_chunk = [c.doc_id for c in retrieved_chunks]
        pairs_by_chunk = [(c.doc_id, getattr(c, "section", None)) for c in retrieved_chunks]
        triples_by_chunk = [(c.doc_id, getattr(c, "section", None), getattr(c, "subsection", None)) for c in retrieved_chunks]

        # Dedup in rank order and trim to K
        retrieved_doc_ids = unique_in_order(doc_ids_by_chunk)[:K]
        retrieved_pairs = unique_in_order(pairs_by_chunk)[:K]
        retrieved_triples = unique_in_order(triples_by_chunk)[:K]

        # --- DOC-only metrics ---
        rank_doc = first_hit_rank(retrieved_doc_ids, lambda d: d in exp_docs)
        ranks_doc.append(rank_doc)
        for k in ks:
            topk = set(retrieved_doc_ids[:k])
            if exp_docs.intersection(topk):
                hits_doc[k] += 1

        # --- DOC+SECTION metrics ---
        if exp_pairs:
            rank_pair = first_hit_rank(retrieved_pairs, lambda p: p in exp_pairs)
        else:
            rank_pair = None
        ranks_pair.append(rank_pair)

        for k in ks:
            if not exp_pairs:
                continue
            topk_pairs = set(retrieved_pairs[:k])
            if exp_pairs.intersection(topk_pairs):
                hits_pair[k] += 1

        # --- DOC+SECTION+SUBSECTION metrics ---
        if exp_triples:
            rank_triple = first_hit_rank(retrieved_triples, lambda t: t in exp_triples)
        else:
            rank_triple = None
        ranks_triple.append(rank_triple)

        for k in ks:
            if not exp_triples:
                continue
            topk_triples = set(retrieved_triples[:k])
            if exp_triples.intersection(topk_triples):
                hits_triple[k] += 1
                answers_with_section_gold[k].append(ex["query"][:8]) # first 8 chars of query for ID"

    # -------------------------
    # Reporting
    # -------------------------

    print(f"Examples: {n_total}")
    print(f"Answerable: {n_answerable} | No-answer: {n_no_answer}")
    if getattr(SETTINGS, "NO_ANSWER_THRESHOLD", None) is not None:
        print(f"NO_ANSWER_THRESHOLD: {SETTINGS.NO_ANSWER_THRESHOLD}")

    # --- DOC-only ---
    print("\n=== DOC-ONLY (answerable only) ===")
    if n_answerable:
        for k in ks:
            print(f"hit@{k}: {hits_doc[k]}/{n_answerable} = {hits_doc[k]/n_answerable:.3f}")
        doc_median = safe_median(ranks_doc)
        doc_miss = sum(1 for r in ranks_doc if r is None)
        print(f"first_hit_k@{K} median: {doc_median if doc_median is not None else 'NA'} | miss@{K}: {doc_miss}/{n_answerable}")
        print(f"MRR@{K} (doc): {mrr(ranks_doc, n_answerable):.3f}")
    else:
        print("No answerable examples to score doc-only retrieval.")

    # --- DOC+SECTION ---
    print("\n=== DOC+SECTION (answerable only) ===")
    if n_answerable:
        print(f"Gold with section labels: {n_answerable_with_section_gold}/{n_answerable}")
    if n_answerable and n_answerable_with_section_gold:
        for k in ks:
            print(f"hit@{k}: {hits_pair[k]}/{n_answerable_with_section_gold} = {hits_pair[k]/n_answerable_with_section_gold:.3f}")
        pair_median = safe_median(ranks_pair)
        pair_miss = sum(1 for r in ranks_pair if r is None)
        print(f"first_hit_k@{K} median: {pair_median if pair_median is not None else 'NA'} | miss@{K}: {pair_miss}/{n_answerable_with_section_gold}")
        print(f"MRR@{K} (doc+section): {mrr(ranks_pair, n_answerable):.3f}")
    else:
        if n_answerable_with_section_gold == 0:
            print("No section labels in gold for answerable examples.")
        else:
            print("No answerable examples to score doc+section retrieval.")

    # --- DOC+SECTION+SUBSECTION ---
    print("\n=== DOC+SECTION+SUBSECTION (answerable only) ===")
    if n_answerable:
        print(f"Gold with subsection labels: {n_answerable_with_subsection_gold}/{n_answerable}")
    if n_answerable and n_answerable_with_subsection_gold:
        for k in ks:
            print(f"hit@{k}: {hits_triple[k]}/{n_answerable_with_subsection_gold} = {hits_triple[k]/n_answerable_with_subsection_gold:.3f}")
        tri_median = safe_median(ranks_triple)
        tri_miss = sum(1 for r in ranks_triple if r is None)
        print(f"first_hit_k@{K} median: {tri_median if tri_median is not None else 'NA'} | miss@{K}: {tri_miss}/{n_answerable_with_subsection_gold}")
        print(f"MRR@{K} (doc+sec+subsec): {mrr(ranks_triple, n_answerable):.3f}")
    else:
        if n_answerable_with_subsection_gold == 0:
            print("No subsection labels in gold for answerable examples.")
        else:
            print("No answerable examples to score doc+sec+subsec retrieval.")

    # --- Optional combined score (you can tweak weights) ---
    if n_answerable:
        mrr_doc = mrr(ranks_doc, n_answerable)
        mrr_pair = mrr(ranks_pair, n_answerable)
        mrr_tri = mrr(ranks_triple, n_answerable)
        combined = 0.2 * mrr_doc + 0.3 * mrr_pair + 0.5 * mrr_tri
        print(f"\nCombined score (0.2*doc + 0.3*doc+sec + 0.5*doc+sec+subsec): {combined:.3f}")

    # --- No-answer metrics ---
    print("\n=== NO-ANSWER ===")
    if n_no_answer:
        print(f"abstain accuracy: {no_answer_correct}/{n_no_answer} = {no_answer_correct/n_no_answer:.3f}")
        print(f"false positives (should abstain but didn't): {no_answer_wrong}/{n_no_answer} = {no_answer_wrong/n_no_answer:.3f}")
    else:
        print("No no_answer examples in gold.")
    if n_answerable:
        print(f"false abstains (should answer but abstained): {false_abstain}/{n_answerable} = {false_abstain/n_answerable:.3f}")


if __name__ == "__main__":
    main()
