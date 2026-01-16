# app/app.py
import streamlit as st
from ops_copilot.retrieve import Retriever
from ops_copilot.answer import make_answer

st.set_page_config(page_title="Cell Culture OPS Copilot", layout="wide")
st.title("Cell Culture OPS Copilot (MVP)")
st.caption("Retrieval + citations-first. If not supported by SOPs, it refuses.")

@st.cache_resource
def get_retriever():
    return Retriever()

retriever = get_retriever()

query = st.text_input("Ask a question", placeholder="e.g., How do I plate cells from frozen stock into 384-well plates?")
k = st.slider("Top-k retrieval", min_value=3, max_value=12, value=6, step=1)

if st.button("Ask", type="primary") and query.strip():
    hits = retriever.search(query, k=k)

    col1, col2 = st.columns([1, 1])

    with col1:
        out = make_answer(query, hits)
        st.markdown(out["answer"])

    with col2:
        st.subheader("Retrieved chunks")
        for i, h in enumerate(hits, start=1):
            st.markdown(f"**{i}. {h['doc_file']} — {h['section']}**  \nScore: `{h['score']:.3f}`  \nAnchor: `{h['anchor']}`")
            with st.expander("Show text"):
                st.code(h["text"], language="markdown")
