# cell-ops-copilot - LLM-Based Assistant for Cell Culture Protocols (Mini RAG Project)
A retrieval-augmented LLM system to answer procedural and troubleshooting questions grounded in specific cell culture SOPs, reducing ambiguity and training overhead in laboratory workflows.


It includes:
- **Deterministic ingestion + SOP-aware chunking**
- **Vector indexing (FAISS) + retrieval with citations**
- **Streamlit UI** for interactive search + source inspection
- **Optional local generative layer (Ollama)** to synthesize grounded answers from retrieved chunks
- **Gold question set + eval** to track retrieval quality

> Default mode is **retrieve-only** (no LLM required).  
> If you enable Ollama, you can turn on **Generate answer** in the UI.

---

## Project structure

- `sops/` — Markdown SOPs (knowledge base)
- `app/` — core pipeline code (ingest, chunking, embeddings, index, retrieval, answering)
- `eval/` — gold questions + evaluation inputs
- `data/processed/` — generated artifacts (`docs.jsonl`, `chunks.jsonl`)
- `data/index/` — FAISS index + metadata (`faiss.index`, `meta.jsonl`, `manifest.json`)
- `streamlit_app.py` — Streamlit entrypoint (UI)

---

## Quickstart (retrieve-only)

### 1) Clone and install

```bash
git clone https://github.com/Ashkanys/cell-ops-copilot.git
cd cell-ops-copilot

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```


### 2) Build chunks + index
```bash
python -m app.ingest
python -m app.chunker
python -m app.index_faiss
```

### 3) Run the Streamlit UI
```bash
python -m streamlit run streamlit_app.py
```
Open the printed local URL in your browser.

## Optional: enable local generation (Ollama)

This adds a local LLM step:
retrieve top-k chunks → generate a grounded answer with citations.

### 1) Install Ollama + pull a small model

Recommended on Apple Silicon + 16GB RAM:
```bash
ollama pull qwen2.5:3b-instruct
```

### 2) Run Streamlit with Ollama enabled
```bash
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=qwen2.5:3b-instruct
export OLLAMA_TEMPERATURE=0.2

python -m streamlit run streamlit_app.py
```

In the UI, enable **Generate answer (Week 3)**.

## Evaluation
### Retrieval quality
```bash
python -m app.eval
```

## Notes on grounding / safety

The project is designed so the answering layer:

- Uses **only retrieved SOP text** as context (no external knowledge).
- Includes **citations** (chunk IDs / line ranges) for instructions and key claims.
- Can **abstain** when evidence is weak or the SOPs don’t contain enough information to answer safely.

This is intentional for SOP workflows, where reliability and provenance matter more than “creative” generation.

---
