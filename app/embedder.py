import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        emb = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(emb, dtype="float32")

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_texts([text])[0]
