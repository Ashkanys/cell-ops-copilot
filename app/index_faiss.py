import json
from pathlib import Path
import numpy as np
import faiss
from tqdm import tqdm

from app.config import SETTINGS
from app.models import Chunk
from app.utils import read_jsonl, write_jsonl
from app.embedder import Embedder


def main():
    chunks_path = SETTINGS.processed_dir / "chunks.jsonl"
    chunks = [Chunk(**row) for row in read_jsonl(chunks_path)]
    texts = [c.text for c in chunks]

    embedder = Embedder(SETTINGS.embedding_model_name)

    # Batch embed
    embs = []
    bs = 64
    for i in tqdm(range(0, len(texts), bs), desc="Embedding"):
        embs.append(embedder.embed_texts(texts[i:i+bs]))
    X = np.vstack(embs).astype("float32")

    d = X.shape[1]
    index = faiss.IndexFlatIP(d)  # cosine if normalized (we normalized)
    index.add(X)

    SETTINGS.index_dir.mkdir(parents=True, exist_ok=True)
    faiss_path = SETTINGS.index_dir / "faiss.index"
    meta_path = SETTINGS.index_dir / "meta.jsonl"

    faiss.write_index(index, str(faiss_path))
    write_jsonl(meta_path, (c.model_dump() for c in chunks))

    manifest = {
        "n_chunks": len(chunks),
        "dim": d,
        "embedding_model": SETTINGS.embedding_model_name,
        "faiss_index": str(faiss_path),
        "meta": str(meta_path),
    }
    (SETTINGS.index_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Index built: {faiss_path}")
    print(f"Meta saved : {meta_path}")


if __name__ == "__main__":
    main()
