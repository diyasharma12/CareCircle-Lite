import os


class Settings:
    """Runtime configuration, read from environment variables."""

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://carecircle:carecircle@localhost:5432/carecircle",
    )

    # Optional: if set, the assistant calls the Groq API for a sharper answer.
    # If unset (the default), a deterministic template builds the answer.
    # Streaming is the point of this endpoint, not which model produced the text.
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


settings = Settings()
