from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str = "changeme"
    member_service_url: str = "http://member-service:8003"

    model_config = {"env_file": ".env"}


settings = Settings()
