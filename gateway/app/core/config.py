from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    internal_service_key: str = "changeme"

    auth_service_url: str = "http://auth-service:8001"
    book_service_url: str = "http://book-service:8002"
    member_service_url: str = "http://member-service:8003"
    loan_service_url: str = "http://loan-service:8004"
    fine_service_url: str = "http://fine-service:8005"

    model_config = {"env_file": ".env"}


settings = Settings()
