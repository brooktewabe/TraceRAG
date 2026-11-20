from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Project paths
    BASE_DIR: Path = BASE_DIR
    CHROMA_DIR: Path = BASE_DIR / "chroma_data"
    DATA_PATH: Path = BASE_DIR / "data" / "documents.json"

    # Vector store & Model
    COLLECTION_NAME: str = "company_knowledge_base"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    DISTANCE_METRIC: str = "cosine"

    # Retrieval & RAG Guardrails
    RELEVANCE_DISTANCE_THRESHOLD: float = 0.55
    DEFAULT_TOP_K: int = 3
    MAX_RETRIES: int = 2

    # LLM API Keys (optional; system falls back to grounded extractive citations if unset)
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # API Server
    API_TITLE: str = "Enterprise AI Knowledge Platform API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

