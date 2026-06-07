from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str = "changeme"

    model_config = {"env_file": ".env"}


settings = Settings()
