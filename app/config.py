"""
Application Configuration
Environment variables management using Pydantic Settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Qdrant Configuration
    qdrant_url: str
    qdrant_master_api_key: str

    # Gemini API Configuration
    gemini_api_key: str

    # Dense Vector Configuration
    dense_vector_name: str = "ocr-dense-vector"
    dense_model: str = "gemini-embedding-001"
    dense_dimension: int = 1536

    # Sparse Vector Configuration
    sparse_vector_name: str = "ocr-sparse-vector"
    sparse_model: str = "gemini-2.5-flash-lite"

    # Server Configuration
    port: int = 6030
    host: str = "0.0.0.0"

    # Concurrency Controls
    embedding_concurrency: int = 4  # Limit concurrent external embedding calls
    health_cache_ttl: float = 2.0   # Seconds to cache /health backend status

    # CPU-bound offloading controls for sparse embedding
    # Choose executor type for CPU tasks: 'thread' or 'process'
    sparse_offload_executor: str = "thread"
    # If 0, size is auto-computed (threads ~ 2xCPU up to 32, process = CPU)
    cpu_threadpool_workers: int = 0
    cpu_processpool_workers: int = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
