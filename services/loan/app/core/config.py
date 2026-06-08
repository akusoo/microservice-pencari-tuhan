from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str = "changeme"
    book_service_url: str = "http://book-service:8002"
    member_service_url: str = "http://member-service:8003"
    fine_service_url: str = "http://fine-service:8005"

    model_config = {"env_file": ".env"}


settings = Settings()
