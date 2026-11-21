"""Core configuration management for AyurEval using pydantic-settings.

Loads environment variables, defines server defaults, and configures API prefixes.
"""

from typing import List, Union
from pydantic import field_validator

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Graceful fallback if pydantic-settings is not yet installed in the current environment
    from pydantic import BaseModel as BaseSettings  # type: ignore
    SettingsConfigDict = dict  # type: ignore


class Settings(BaseSettings):
    """Application runtime settings and configuration using Pydantic Settings."""

    # Core Application Metadata
    app_name: str = "AyurEval Verification API"
    version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"

    # Server Configuration
    env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS Configuration
    allowed_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Allow origins as a JSON array string, comma-separated string, or list."""
        if isinstance(v, str):
            v = v.strip()
            # Handle JSON array format: ["http://...", "http://..."]
            if v.startswith("["):
                import json as _json
                try:
                    return _json.loads(v)
                except Exception:
                    pass
            # Fallback: comma-separated
            return [i.strip() for i in v.split(",") if i.strip()]
        return list(v)

    # Vector Database & Embeddings Configuration
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "ayurveda_canonical_corpus"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Knowledge Base Corpus Directories
    samhitas_path: str = "./data/samhitas"
    commentaries_path: str = "./data/commentaries"
    scientific_path: str = "./data/scientific"

    # Optional LLM Provider Keys & Model Configurations
    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "mock"
    llm_model: str = "ayurparam-v1"
    llm_temperature: float = 0.3
    ollama_base_url: str = "http://localhost:11434"

    # Compatibility properties for uppercase access
    @property
    def LLM_PROVIDER(self) -> str:
        return self.llm_provider

    @property
    def LLM_MODEL(self) -> str:
        return self.llm_model

    @property
    def LLM_TEMPERATURE(self) -> float:
        return self.llm_temperature
    @property
    def APP_NAME(self) -> str:
        return self.app_name

    @property
    def VERSION(self) -> str:
        return self.version

    @property
    def API_V1_PREFIX(self) -> str:
        return self.api_v1_prefix

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return self.allowed_origins

    @property
    def HOST(self) -> str:
        return self.host

    @property
    def PORT(self) -> int:
        return self.port

    @property
    def DEBUG(self) -> bool:
        return self.debug

    @property
    def CHROMA_PERSIST_DIRECTORY(self) -> str:
        return self.chroma_persist_directory

    @property
    def CHROMA_COLLECTION_NAME(self) -> str:
        return self.chroma_collection_name

    @property
    def EMBEDDING_MODEL_NAME(self) -> str:
        return self.embedding_model_name

    try:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )
    except NameError:
        pass


settings = Settings()
