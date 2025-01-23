from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = Field("mock-key", env="OPENAI_API_KEY")
    db_host: str = Field("localhost", env="DB_HOST")
    db_port: int = Field(5432, env="DB_PORT")
    db_user: str = Field("postgres", env="DB_USER")
    db_password: str = Field("postgres", env="DB_PASSWORD")
    db_name: str = Field("pdf_chat", env="DB_NAME")

    use_postgres_db: bool = Field(True, env="USE_POSTGRES_DB")
    document_store_type: str = Field("s3", env="DOCUMENT_STORE_TYPE")

    s3_bucket_name: str = Field("pdf-chat-lambda-state", env="S3_BUCKET_NAME")

    embedding_model: str = Field("text-embedding-3-large", env="EMBEDDING_MODEL")
    embedding_size: int = Field(1536, env="EMBEDDING_SIZE")

    @property
    def connection_string(self):
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def is_local(self):
        return True if self.db_host == "localhost" else False

    class Config:
        env_file = ".env"


settings = Settings()
