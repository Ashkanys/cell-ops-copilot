from pydantic import BaseModel
from pathlib import Path


class Settings(BaseModel):
    sops_dir: Path = Path("data_raw/sops")
    processed_dir: Path = Path("data/processed")
    index_dir: Path = Path("data/index")
    logs_dir: Path = Path("data/logs")

    # Chunking knobs
    max_chars: int = 1400
    procedure_steps_per_chunk: int = 30

    # Retrieval knobs
    top_k: int = 5
    NO_ANSWER_THRESHOLD: float = 0.25  # for the eval "no answer" decision

    # Embeddings
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"


SETTINGS = Settings()
