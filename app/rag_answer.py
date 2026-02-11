from typing import List, Optional, Tuple
import faiss  # type: ignore

from app.embedder import Embedder
from app.models import Chunk
from app.answer_schema import Answer, RetrievedSource
from app.prompting import build_grounded_prompt
from app.llm_client import LLM


def format_citation(c: Chunk) -> str:
    step_part = ""
    if c.step_start is not None and c.step_end is not None:
        step_part = f" • steps {c.step_start}–{c.step_end}"
    sub = f" • {c.subsection}" if c.subsection else ""
    return f"{c.doc_id} • {c.section}{sub}{step_part} (L{c.line_start}–L{c.line_end})"


def retrieve_topk(
    index: "faiss.Index",
    meta: List[Chunk],
    embedder: Embedder,
    query: str,
    k: int,
    min_chars: int = 80,
    doc_filter: Optional[str] = None,
    section_filter: Optional[str] = None,
) -> List[Tuple[float, Chunk]]:
    q = embedder.embed_query(query).reshape(1, -1).astype("float32")

    over_k = min(max(k * 6, k), len(meta))
    scores, idxs = index.search(q, over_k)

    out: List[Tuple[float, Chunk]] = []
    for s, i in zip(scores[0].tolist(), idxs[0].tolist()):
        c = meta[int(i)]
        if len(c.text.strip()) < min_chars:
            continue
        if doc_filter and c.doc_id != doc_filter:
            continue
        if section_filter and c.section != section_filter:
            continue
        out.append((float(s), c))
        if len(out) >= k:
            break
    return out


def confidence_from_scores(scores: List[float]) -> str:
    # Heuristic. Tune later with your eval.
    if not scores:
        return "low"
    top = scores[0]
    if top >= 0.50:
        return "high"
    if top >= 0.30:
        return "medium"
    return "low"


def should_abstain(scores: List[float], sources: List[RetrievedSource]) -> Optional[str]:
    """
    Conservative abstention:
    - no sources
    - or very low top score
    - or all sources are "Other" section (weak signal for procedure questions)
    """
    if not sources:
        return "No relevant SOP excerpts were retrieved."
    if scores and scores[0] < 0.22:
        return f"Top retrieval score is low ({scores[0]:.3f}); insufficient evidence to answer safely."
    return None


def extract_cited_chunk_ids(answer_md: str, allowed_chunk_ids: set[str]) -> List[str]:
    # Minimal parsing: citations are [chunk_id]
    # This expects chunk_ids are hex sha1; adapt if yours differs.
    import re
    cited = re.findall(r"\[([0-9a-f]{8,40})\]", answer_md)
    # Keep only those that are in allowed set and preserve order unique
    seen = set()
    out = []
    for cid in cited:
        if cid in allowed_chunk_ids and cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


def answer_query(
    llm: LLM,
    index: "faiss.Index",
    meta: List[Chunk],
    embedder: Embedder,
    query: str,
    k: int = 5,
    doc_filter: Optional[str] = None,
    section_filter: Optional[str] = None,
) -> Answer:
    retrieved = retrieve_topk(index, meta, embedder, query, k, doc_filter=doc_filter, section_filter=section_filter)
    scores = [s for s, _ in retrieved]

    sources: List[RetrievedSource] = []
    for s, c in retrieved:
        sources.append(RetrievedSource(
            chunk_id=c.chunk_id,
            citation=format_citation(c),
            score=s,
            text=c.text
        ))

    abstain_reason = should_abstain(scores, sources)
    conf = confidence_from_scores(scores)

    if abstain_reason:
        return Answer(
            final_answer_md=(
                f"I can’t answer this safely from the SOP text I retrieved.\n\n"
                f"**Reason:** {abstain_reason}\n\n"
                f"Check the Sources panel for the closest excerpts."
            ),
            citations=[],
            confidence="low",
            warnings=["Retrieve-only response (abstained)."],
            followups=[
                "Can you specify which SOP or step you’re referring to?",
                "What exact symptom/condition are you seeing (e.g., low viability, poor attachment, contamination signs)?"
            ],
            sources=sources,
            abstained=True,
            abstain_reason=abstain_reason,
        )

    prompt = build_grounded_prompt(query, sources)
    md = llm.generate(prompt)

    allowed_ids = {s.chunk_id for s in sources}
    cited = extract_cited_chunk_ids(md, allowed_ids)

    # If the model forgets citations, downgrade confidence and warn
    warnings = []
    if not cited:
        warnings.append("Generated answer contains no valid citations; treat as low confidence.")
        conf = "low"

    return Answer(
        final_answer_md=md,
        citations=cited,
        confidence=conf,  # heuristic
        warnings=warnings,
        followups=[],
        sources=sources,
        abstained=False,
    )
