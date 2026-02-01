# Build Log — Cell-Ops Copilot (RAG for Cell-Culture SOPs)

This log tracks the *major project steps*, the *reasoning behind each change*, and the *practical outcome* (what it enabled / fixed).  
Scope: SOP authoring → indexing MVPs → early Streamlit UI → refactor into modular ingest/chunk/index pipeline.

---

## 0) Corpus creation: 8 SOPs (domain-authored, standardized Markdown)

**What I did**
- Wrote 8 common day-to-day cell culture SOPs from my 10+ years of lab experience.
- Enforced a consistent Markdown structure across SOPs with predictable headers/subheaders:
  - Purpose, Scope, Materials, Safety, Preparation, Procedure, QC checks, Troubleshooting, Critical Points

**Why it mattered**
- A structured corpus is the foundation for any reliable RAG system.
- Consistent headings enable section-aware chunking and clearer citations.

**Outcome**
- A clean, uniform SOP dataset ready for indexing and retrieval.

---

## 1) v0 Indexing MVP: single-file “Build_index” (fast prototype)

**Key implementation**
- Read `docs/sops/*.md`
- Chunking:
  - split on *any* heading starting with `#`
  - fallback split large chunks by blank lines
  - max chunk size ≈ 1600 chars
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (normalized vectors)
- Index: FAISS `IndexFlatIP` (cosine via normalization)
- Outputs:
  - `indexes/faiss.index`
  - `indexes/chunks.jsonl` with minimal metadata (`chunk_id`, `source_file`, `text`)

**Why this version existed**
- Establish end-to-end feasibility with minimal moving parts.

**Limitations observed**
- Chunk boundaries were not aligned to SOP sections in a consistent way.
- Metadata was too thin for good UI citations (“file + chunk number” is hard to trust/interpret).
- Chunk IDs were sequential, and unstable when the document changes.

---

## 2) v1 Indexer improvement: section-aware split + richer metadata (still one script)

**Key changes**
- Split by `##` (H2) sections first (SOP section structure)
- Subchunk oversized sections by:
  - `###` (H3) if available, otherwise blank lines
- Larger max chunk size (≈ 2200 chars) to reduce fragmentation
- Added metadata for RAG + UI:
  - `doc_title`, `section`, `anchor` (virtual), etc.
- Output changed to `meta.json` (more readable during iteration)

**Why**
- Retrieval becomes easier to interpret when results map to “Purpose / Safety / Procedure …”.
- UI needs better citations than “chunk023”.

**Outcome**
- Better chunk semantics and better display in UI, but still not enough control to prevent “header-only” or low-signal chunks.

---

## 3) Preliminary UI: legacy Streamlit app (app/legacy_streamlit_app.py)

**What I added**
- Streamlit interface to:
  - enter a query
  - choose `top-k`
  - show a “citations-first” answer + the retrieved chunks side-by-side
  - display chunk metadata (file, section, score, anchor) and raw chunk text in expanders

**Why**
- Rapid debugging: immediately see what retrieval is returning.
- Helps validate whether chunking strategy is actually separating information usefully.

**What it revealed**
- Chunking quality is the bottleneck: retrieval often returns low-information chunks (e.g., headers/titles).

---

## 4) v2 Refactor: new pipeline (config + ingest + chunker) to fix chunk quality and traceability

After the Streamlit-driven debugging, I restarted the ingestion/chunking layer with a more “production-shaped” design.

### 4.1 Config-driven parameters (app/config.py)

**Change**
- Introduced `SETTINGS` for key knobs (examples implied in code):
  - `sops_dir`, `processed_dir`
  - `max_chars`
  - `procedure_steps_per_chunk`
  - (later) chunk filters like minimum text length

**Why**
- Makes experiments reproducible and reviewable (no more “magic numbers” scattered in scripts).
- Enables quick iteration without rewriting code.

---

### 4.2 Ingestion stage (ingest.py): document identity + versioning

**Key changes**
- Added `infer_doc_id()` to map filenames like `sop-tc-007-...md` → stable `doc_id` (`sop-tc-007`)
- Added `infer_title()` reading `# ` as the human title (fallback to filename stem)
- Stored documents as structured JSONL:
  - `doc_id`, `title`, `source_path`, `version`, `lines`
- Added git SHA versioning (`get_git_sha()`), embedded into each document record

**Why**
- Stable IDs are critical for evaluation, debugging, and regression tracking.
- Versioning ties embeddings/chunks back to a specific corpus revision.

**Outcome**
- `processed/docs.jsonl` becomes the canonical “source of truth” input for chunking and indexing.

---

### 4.3 Chunker redesign (chunker.py): section classification + step-aware procedure chunking

**Key changes**
- Header parsing via regex for `#{1,4}` (up to H4)
- Section classification (`classify_section`) normalizes headings into canonical labels:
  - Purpose, Scope, Safety, Materials, Preparation, Procedure, QC, Troubleshooting, Critical Points, etc.
- **Procedure-specific chunking**:
  - Detect numbered steps (`STEP_RE`)
  - Chunk by *groups of N steps* (`SETTINGS.procedure_steps_per_chunk`)
  - Fall back to char-based chunking if steps aren’t detected
- **Char-based chunking** for non-procedure sections using `SETTINGS.max_chars`
- Added **line-level provenance** per chunk:
  - `line_start`, `line_end` (1-based for humans)
  - (Procedure chunks) `step_start`, `step_end`
- Introduced stable chunk IDs:
  - `stable_chunk_id(doc_id, section, subsection, line_start, line_end)`

**Why**
- Procedure sections are the most queried; step chunking produces more “actionable” retrieval results.
- Line ranges make citations precise and debuggable.
- Stable chunk IDs prevent evaluation drift when content shifts slightly.

**Outcome**
- Chunks are more semantically aligned with SOP usage (especially procedures), with better traceability.

---

### 4.4 Chunk cleanup: removing low-information “header-only” chunks

**Problem discovered**
- Early chunking still produced tiny/low-signal chunks (often just headers/titles).

**Fix**
- Added a usefulness filter:
  - minimum characters (e.g., `>= 80`)
  - minimum word count (e.g., `>= 12`)

**Why**
- Low-signal chunks pollute retrieval, especially with small corpora.
- Removing them increases the probability that top-k hits contain actual instructions.

**Outcome**
- Cleaner metadata, more useful retrieval results, and better UI experience.

---
## 5) Evaluation + “No Answer” support (regression tracking)

After refactoring ingestion/chunking, I added an evaluation harness so improvements are measurable instead of subjective.

### 5.1 Added “no_answer” threshold (abstention behavior)
**Change**
- Introduced `NO_ANSWER_THRESHOLD` in `config.py`.
- Implemented `should_abstain(index, top_score)` inside `eval.py`:
  - If FAISS metric is **inner product** (cosine-like when embeddings are normalized): abstain when `top_score < threshold`
  - If metric is **distance** (e.g., L2): abstain when `top_score > threshold`
- Gold items can be labeled with `{"no_answer": true}`.

**Why**
- A citations-first SOP copilot should **refuse** when the corpus does not support the question.
- Prevents hallucinated “best guesses” when similarity is low.

**Outcome**
- Evaluation now measures both retrieval quality *and* abstention correctness.

---

### 5.2 Added git SHA versioning for regression tracking
**Change**
- `ingest.py` writes a `version` field into each `Document` using `get_git_sha()`.

**Why**
- Ties artifacts (docs/chunks/index) to an exact repo revision.
- Makes regressions debuggable: “did this change because SOP text changed or because chunking/index code changed?”

**Outcome**
- Each rebuild produces version-stamped data usable for comparisons over time.

---

### 5.3 Wrote a small gold set for repeatable scoring
**Change**
- Created `eval/gold_questions.jsonl` with **11** questions:
  - **10 answerable** (some may have multiple valid targets)
  - **1 no-answer** example (`no_answer: true`) to validate abstention

**Gold schema supported**
- Preferred format:
  - `expected: [{"doc_id":"sop-tc-007","section":"Procedure"}, ...]`
- Backward-compatible fallbacks:
  - `expected_doc_id(s)` and/or `expected_section(s)`

**Why**
- With a small corpus (8 SOPs), even minor chunking or indexing changes can swing results.
- A consistent gold set prevents “moving goalposts” and enables fast iteration.

**Outcome**
- Repeatable metrics that can be re-run on every change.

---

### 5.4 eval.py metrics (what is tracked)
**Retrieval (answerable-only)**
- `hit@k` for **doc-only** targets at k ∈ {1,3,5,10}
- `first_hit_rank` + median rank and miss rate
- `MRR@K` (mean reciprocal rank)

**Retrieval with structure (answerable-only)**
- `hit@k` for **(doc_id, section)** pairs when gold provides section labels
- `MRR@K` for doc+section
- Optional combined score:
  - `0.3 * MRR(doc) + 0.7 * MRR(doc+section)` (emphasize section correctness)

**No-answer behavior**
- Abstain accuracy on `no_answer:true` examples
- False positives: gold says abstain, model answered
- False abstains: gold answerable, model abstained

**Why**
- Doc-only answers can be “kind of right” but still unhelpful if the system surfaces the wrong SOP section.
- Explicit no-answer scoring prevents optimizing retrieval at the expense of unsafe/confident hallucinations.

---

### Notes
- `eval.py` intentionally excludes gold `no_answer:true` examples from hit@k and MRR calculations, to avoid mixing “should answer” and “should abstain” into the same retrieval score.

---
## 6) Evaluation upgrade: subsection-aware chunking + 3-level scoring

As chunking improved, a new mismatch showed up during evaluation: the retriever often returned the correct **doc** and correct **section** (e.g., “Procedure”), but the wrong **subsection** when Procedure content was split into labeled parts (e.g., A/B/C).

---

### 6.1 Problem observed
- Some SOPs contain subsections inside sections (especially **Procedure**) such as “A”, “B”, “C”, or named sub-steps.
- Chunks were produced using `(section, subsection)` boundaries.
- Retrieval frequently surfaced the correct section but mismatched the subsection, which matters for correctness and citations.
- The existing evaluation (doc-only or doc+section) could score these as “correct” even when the retrieved chunk was the wrong part of the SOP.

---
### 6.2 Change: normalize subsection labels, preserve them as metadata
**Decision**
- Normalize by *removing subsection text from the chunk’s canonical identity* (so evaluation doesn’t fail due to formatting differences like “A.” vs “A)” vs “Part A”).
- Preserve subsection information separately in chunk metadata.

**Implementation notes**
- Chunk schema now includes an explicit `subsection` field:
  - `subsection: <string>` when present
  - `subsection: null` when the chunk has no subsection
- Chunks that do not belong to a subsection remain `null` to distinguish “no subsection” from “unknown subsection”.

**Outcome**
- Retrieval results can still display the subsection (useful in UI/citations),
  while evaluation can treat subsection matching as an *optional stricter tier*.

---
### 6.3 Change: extend evaluation to 3 levels of granularity
To avoid over-crediting “almost correct” hits, evaluation was expanded to report accuracy at three depths:

1. **Doc-only**
   - Correct SOP file/doc_id is retrieved.
2. **Doc + Section**
   - Correct SOP doc_id *and* correct section (e.g., Procedure, Safety, Troubleshooting).
3. **Doc + Section + Subsection**
   - Correct doc_id *and* correct section *and* correct subsection (A/B/C or named subsection).
   - If gold does not specify a subsection, this tier is skipped (or treated as not applicable).

**Why**
- This reflects real user experience:
  - doc-only can still be too broad
  - doc+section is better but can still land you in the wrong part of a long Procedure
  - doc+section+subsection is the most precise and best proxy for “correct chunk landed”

**Outcome**
- Metrics now distinguish:
  - “found the right SOP”
  - “found the right SOP + right area”
  - “found the right SOP + right area + right sub-area”

---
### 6.4 Gold data and reporting implications
- Gold questions can now specify expected targets at multiple levels:
  - `doc_id` only
  - `doc_id + section`
  - `doc_id + section + subsection`
- Report includes hit@k / first-hit rank / MRR at each tier (where applicable).
- This makes regressions more interpretable:
  - e.g., doc+section stable but subsection tier drops → likely chunk boundary or subsection labeling issue.

---
### Notes / future refinements
- Subsection normalization should be consistent in both:
  - chunk metadata creation
  - gold label creation
- If subsections are purely structural (“A/B/C”) and not meaningful to users, consider mapping them to more descriptive subsection titles when possible (e.g., “A. Setup” instead of “A”).

---