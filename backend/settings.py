from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    db_host: str = Field("localhost", env="DB_HOST")
    db_port: int = Field(5432, env="DB_PORT")
    db_user: str = Field("postgres", env="DB_USER")
    db_password: str = Field("postgres", env="DB_PASSWORD")
    db_name: str = Field("pdf_chat", env="DB_NAME")

    use_postgres_db: bool = Field(True, env="USE_POSTGRES_DB")

    @property
    def connection_string(self):
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def is_local(self):
        return True if self.db_host == "localhost" else False
    
    @property
    def use_postgres_db(self):
        return True if self.use_postgres_db else False

    class Config:
        env_file = ".env"


settings = Settings()
