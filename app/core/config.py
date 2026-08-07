import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = "AI Knowledge Agent"

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://ai_user:ai_password@localhost:5432/ai_knowledge",
    )

    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

    MINIO_BUCKET = "documents"


settings = Settings()