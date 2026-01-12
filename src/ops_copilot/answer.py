# src/ops_copilot/answer.py
from typing import List, Dict, Any


def make_answer(query: str, hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Simple rule: if retrieval is weak, refuse.
    if not hits or hits[0]["score"] < 0.30:
        return {
            "answer": "I can’t find strong support for that question in the current SOP library. Try rephrasing, or add a protocol covering this topic.",
            "citations": [],
        }

    # Otherwise: summarize by listing key sections and point user to the cited SOPs.
    lines = []
    citations = []
    lines.append(f"**Question:** {query}\n")
    lines.append("**Supported guidance (from SOP library):**")

    for i, h in enumerate(hits, start=1):
        cite = f"[{i}] {h['doc_file']} — {h['section']} ({h['anchor']})"
        citations.append(cite)
        # show a short excerpt
        excerpt = h["text"].strip().splitlines()
        excerpt = "\n".join(excerpt[:8]).strip()
        lines.append(f"\n{i}) **{h['doc_title']} / {h['section']}**  \n{excerpt}\n")

    lines.append("\n**Citations:**")
    for c in citations:
        lines.append(f"- {c}")

    return {"answer": "\n".join(lines), "citations": citations}
