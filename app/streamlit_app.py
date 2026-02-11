import json
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import streamlit as st

try:
    import faiss  # type: ignore
except Exception:
    st.error("FAISS import failed. Did you install faiss-cpu?")
    st.stop()

from app.config import SETTINGS
from app.embedder import Embedder
from app.models import Chunk
from app.utils import read_jsonl

# Week 3 additions
from app.llm_client import get_llm
from app.rag_answer import answer_query


# ---------- helpers ----------

def format_citation(c: Chunk) -> str:
    step_part = ""
    if c.step_start is not None and c.step_end is not None:
        step_part = f" • steps {c.step_start}–{c.step_end}"
    sub = f" • {c.subsection}" if c.subsection else ""
    return f"{c.doc_id} • {c.section}{sub}{step_part} (L{c.line_start}–L{c.line_end})"


def load_manifest(index_dir: Path) -> dict:
    p = index_dir / "manifest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


@st.cache_resource
def load_index_and_meta(index_dir_str: str) -> Tuple["faiss.Index", List[Chunk], dict]:
    index_dir = Path(index_dir_str)
    faiss_path = index_dir / "faiss.index"
    meta_path = index_dir / "meta.jsonl"

    if not faiss_path.exists() or not meta_path.exists():
        raise FileNotFoundError(
            f"Missing index files. Expected:\n- {faiss_path}\n- {meta_path}\n"
            f"Run: python -m app.index_faiss"
        )

    index = faiss.read_index(str(faiss_path))
    meta = [Chunk(**row) for row in read_jsonl(meta_path)]
    manifest = load_manifest(index_dir)
    return index, meta, manifest


@st.cache_resource
def load_embedder(model_name: str) -> Embedder:
    return Embedder(model_name)


def search(
    index: "faiss.Index",
    meta: List[Chunk],
    embedder: Embedder,
    query: str,
    k: int,
    doc_filter: Optional[str] = None,
    section_filter: Optional[str] = None,
) -> List[Tuple[float, Chunk]]:
    q = embedder.embed_query(query).reshape(1, -1).astype("float32")

    # Over-retrieve then filter
    over_k = min(max(k * 5, k), len(meta))
    scores, idxs = index.search(q, over_k)

    results: List[Tuple[float, Chunk]] = []
    for s, i in zip(scores[0].tolist(), idxs[0].tolist()):
        c = meta[int(i)]

        if doc_filter and c.doc_id != doc_filter:
            continue
        if section_filter and c.section != section_filter:
            continue

        if len(c.text.strip()) < 80:  # skip short chunks
            continue

        results.append((float(s), c))
        if len(results) >= k:
            break

    return results


# ---------- UI ----------

st.set_page_config(page_title="Cell Ops SOP RAG (Retriever + Week 3 Answering)", layout="wide")

st.title("Cell Ops SOP RAG — Retrieval + Answering")
st.caption("Retrieve SOP chunks with citations, or generate a grounded answer from retrieved chunks.")

with st.sidebar:
    st.header("Index & Model")
    index_dir = st.text_input("Index directory", value=str(SETTINGS.index_dir))
    model_name = st.text_input("Embedding model", value=SETTINGS.embedding_model_name)
    top_k = st.slider("Top-k", min_value=1, max_value=20, value=SETTINGS.top_k)

    st.divider()
    st.header("Mode")
    generate_answer = st.checkbox("Generate answer (Week 3)", value=False)
    show_sources = st.checkbox("Show sources panel", value=True)

    st.divider()
    st.header("Filters")
    load_btn = st.button("Reload index (if you rebuilt)")

# Load resources
try:
    if load_btn:
        load_index_and_meta.clear()
        load_embedder.clear()
        st.cache_resource.clear()

    index, meta, manifest = load_index_and_meta(index_dir)
    embedder = load_embedder(model_name)
except Exception as e:
    st.error(str(e))
    st.stop()

# LLM (Week 3) — defaults to stub unless you configure it
llm = get_llm()

# Build filter options
doc_ids = sorted({c.doc_id for c in meta})
sections = sorted({c.section for c in meta})

with st.sidebar:
    doc_filter = st.selectbox("Doc filter (optional)", options=["(all)"] + doc_ids, index=0)
    section_filter = st.selectbox("Section filter (optional)", options=["(all)"] + sections, index=0)

doc_filter_val = None if doc_filter == "(all)" else doc_filter
section_filter_val = None if section_filter == "(all)" else section_filter

default_q = "What are the critical points for passaging adherent cells?"
query_text = st.text_area("Ask a question", value=default_q, height=80)

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    run = st.button("Search", type="primary")
with col_b:
    show_raw = st.checkbox("Show raw chunk text", value=True)
with col_c:
    st.write("")

with st.expander("Index info"):
    st.write({
        "n_chunks": manifest.get("n_chunks", len(meta)),
        "dim": manifest.get("dim", "unknown"),
        "embedding_model": manifest.get("embedding_model", model_name),
        "faiss_index": manifest.get("faiss_index", str(Path(index_dir) / "faiss.index")),
        "meta": manifest.get("meta", str(Path(index_dir) / "meta.jsonl")),
    })

if run:
    q = query_text.strip()
    if not q:
        st.warning("Type a query first.")
        st.stop()

    if generate_answer:
        # Week 3 pipeline: retrieve -> (maybe abstain) -> generate -> show answer + sources
        ans = answer_query(
            llm=llm,
            index=index,
            meta=meta,
            embedder=embedder,
            query=q,
            k=top_k,
            doc_filter=doc_filter_val,
            section_filter=section_filter_val,
        )

        if show_sources:
            left, right = st.columns([1.1, 1])
        else:
            left, right = st.columns([1, 0.001])

        with left:
            st.subheader("Answer")
            st.markdown(ans.final_answer_md)

            st.write(f"**Confidence:** {ans.confidence}")
            if ans.abstained:
                st.warning(f"Abstained: {ans.abstain_reason}")

            if ans.warnings:
                st.divider()
                for w in ans.warnings:
                    st.info(w)

            if ans.followups:
                st.divider()
                st.markdown("**Follow-up questions:**")
                for fu in ans.followups:
                    st.markdown(f"- {fu}")

            if ans.citations:
                st.divider()
                st.markdown("**Cited chunk_ids:**")
                st.code(", ".join(ans.citations), language="text")

        if show_sources:
            with right:
                st.subheader("Sources")
                if not ans.sources:
                    st.info("No sources returned.")
                else:
                    for i, src in enumerate(ans.sources, start=1):
                        st.markdown(f"**#{i}** score={src.score:.4f}  \n{src.citation}")
                        st.code(src.chunk_id, language="text")
                        if show_raw:
                            with st.expander("Chunk text", expanded=(i == 1)):
                                st.text(src.text)
                        st.divider()

    else:
        # Retrieve-only (Week 2 behavior)
        results = search(
            index=index,
            meta=meta,
            embedder=embedder,
            query=q,
            k=top_k,
            doc_filter=doc_filter_val,
            section_filter=section_filter_val,
        )

        if not results:
            st.info("No results matched your filters. Try removing filters or increasing top-k.")
            st.stop()

        st.subheader(f"Top results ({len(results)})")
        for rank, (score, chunk) in enumerate(results, start=1):
            left, right = st.columns([3, 2])
            with left:
                st.markdown(f"### #{rank}")
                st.markdown(f"**Citation:** {format_citation(chunk)}")
                st.markdown(f"**Source:** `{chunk.source_path}`")
            with right:
                st.metric("Similarity", f"{score:.4f}")
                st.code(chunk.chunk_id, language="text")

            if show_raw:
                with st.expander("Chunk text", expanded=(rank == 1)):
                    st.text(chunk.text)

            st.divider()
