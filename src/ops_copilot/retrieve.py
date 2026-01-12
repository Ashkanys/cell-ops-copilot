# src/ops_copilot/retrieve.py
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_PATH = Path("indexes/faiss.index")
META_PATH = Path("indexes/meta.json")


class Retriever:
    def __init__(self):
        if not INDEX_PATH.exists() or not META_PATH.exists():
            raise FileNotFoundError("Index not found. Run: python scripts/build_index.py")

        self.model = SentenceTransformer(MODEL_NAME)
        self.index = faiss.read_index(str(INDEX_PATH))
        self.meta: List[Dict[str, Any]] = json.loads(META_PATH.read_text(encoding="utf-8"))

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        q_emb = self.model.encode([query], normalize_embeddings=True)
        q_emb = np.asarray(q_emb, dtype=np.float32)
        scores, idxs = self.index.search(q_emb, k)

        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0:
                continue
            item = dict(self.meta[idx])
            item["score"] = float(score)
            results.append(item)
        return results
