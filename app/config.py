from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://cle:cle_dev_password@localhost:5434/cle_db"
    summarization_model: str = "sshleifer/distilbart-cnn-12-6"
    embedding_model: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"

settings = Settings()
