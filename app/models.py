from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class Document(BaseModel):
    doc_id: str
    title: str
    source_path: str
    version: Optional[str] = None
    lines: List[str]  # raw markdown lines


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_title: str
    source_path: str
    version: Optional[str] = None

    section: str
    subsection: Optional[str] = None

    line_start: int
    line_end: int

    step_start: Optional[int] = None
    step_end: Optional[int] = None

    text: str
    tags: Dict[str, Any] = {}
