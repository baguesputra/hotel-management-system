from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "Hotel Management System"
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str

    # Database
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str

    # Redis
    redis_host: str
    redis_port: int = 6379
    redis_url: str

    # Celery
    celery_broker_url: str
    celery_result_backend: str

    # Email
    mail_server: str
    mail_port: int = 587
    mail_username: str
    mail_password: str
    mail_from: str
    mail_from_name: str = "Hotel Management System"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env"


settings = Settings()