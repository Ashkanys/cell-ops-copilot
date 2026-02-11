from typing import List
from app.answer_schema import RetrievedSource


def build_grounded_prompt(user_query: str, sources: List[RetrievedSource]) -> str:
    """
    We embed the sources with explicit chunk_id and citation string.
    The model must cite as [chunk_id] in-line.
    """
    ctx_blocks = []
    for s in sources:
        ctx_blocks.append(
            f"---\n"
            f"chunk_id: {s.chunk_id}\n"
            f"citation: {s.citation}\n"
            f"text:\n{s.text}\n"
        )

    context = "\n".join(ctx_blocks)

    return f"""
You are a lab SOP assistant. You MUST follow these rules:

RULES:
1) Use ONLY the provided Context. Do NOT invent steps or details.
2) Every bullet or sentence that gives an instruction MUST include an in-line citation like [chunk_id].
3) If the Context does not contain enough information to answer safely, say so and ask 1–3 follow-up questions.
4) Prefer a structured answer with headings.

OUTPUT FORMAT (Markdown):
- Start with a short answer.
- Then sections as relevant:
  - Steps
  - Critical points
  - QC / Expected outcome
  - Troubleshooting (only if supported by Context)
  - When to escalate (e.g., suspected contamination)
- End with:
  Sources: [chunk_id, chunk_id, ...]

USER QUESTION:
{user_query}

CONTEXT:
{context}
""".strip()
