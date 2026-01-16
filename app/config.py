from pydantic import BaseModel
from pathlib import Path


class Settings(BaseModel):
    sops_dir: Path = Path("docs/sops")
    processed_dir: Path = Path("data/processed")
    index_dir: Path = Path("data/index")
    logs_dir: Path = Path("data/logs")

    # Chunking knobs
    max_chars: int = 1400
    procedure_steps_per_chunk: int = 6

    # Retrieval knobs
    top_k: int = 5

    # Embeddings
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"


SETTINGS = Settings()
