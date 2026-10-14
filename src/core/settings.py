from functools import cached_property
from pathlib import Path

from pydantic import AmqpDsn, Field, PostgresDsn
from pydantic_settings import BaseSettings


class PostgresConfig(BaseSettings):
    user: str = Field(alias='DB_USER')
    password: str = Field(alias='DB_PASSWORD')
    host: str = Field(alias='DB_HOST')
    port: int = Field(alias='DB_PORT')
    db_name: str = Field(alias='DB_NAME')

    @cached_property
    def url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme='postgresql+asyncpg',
                username=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                path=self.db_name,
            )
        )


class RabbitMQConfig(BaseSettings):
    url: AmqpDsn = Field(alias='RABBIT_URL')


class WebhookConfig(BaseSettings):
    timeout_seconds: float = Field(default=10.0, alias='WEBHOOK_TIMEOUT_SECONDS')


class AppConfig(BaseSettings):
    api_key: str = Field(alias='API_KEY')
    debug: bool = Field(default=False, alias='DEBUG')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def log_dir(self) -> Path:
        return self.base_dir / 'logs'


class Settings(BaseSettings):
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    rabbit: RabbitMQConfig = Field(default_factory=RabbitMQConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)


settings = Settings()
