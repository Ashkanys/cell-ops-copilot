from pydantic import BaseModel, Field
from typing import List, Optional, Literal


Confidence = Literal["low", "medium", "high"]


class RetrievedSource(BaseModel):
    chunk_id: str
    citation: str
    score: float
    text: str


class Answer(BaseModel):
    final_answer_md: str = Field(..., description="Markdown answer grounded in provided sources")
    citations: List[str] = Field(default_factory=list, description="List of chunk_ids cited")
    confidence: Confidence = "low"
    warnings: List[str] = Field(default_factory=list)
    followups: List[str] = Field(default_factory=list)

    # Useful for UI/debug
    sources: List[RetrievedSource] = Field(default_factory=list)
    abstained: bool = False
    abstain_reason: Optional[str] = None
