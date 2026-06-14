from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str = ""

    # Model name — leave empty for default gemini-2.0-flash
    model_name: str = "gemini-2.5-flash"

    llm_provider: str = "google"  # kept for reference

    embedding_model: str = "all-MiniLM-L6-v2"
    vector_store_path: str = "data/faiss_index"
    top_k: int = 5

    app_name: str = "Python Programming Q&A Assistant"
    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
