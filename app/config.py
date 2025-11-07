# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class SiteConfig(BaseSettings):
    base_url: str
    delay_between_requests: float
    max_workers: int
    user_agent: str


class TagsConfig(BaseSettings):
    links_selector: str
    file_link_selector: str


class PostgresConfig(BaseSettings):
    host: str
    port: int
    database: str
    username: str
    password: str
    echo: bool = False

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class MongodbConfig(BaseSettings):
    host: str
    port: int
    database: str
    collection: str

    @property
    def url(self) -> str:
        return f"mongodb://{self.host}:{self.port}"


class DatabaseConfig(BaseSettings):
    postgres: PostgresConfig
    mongodb: MongodbConfig


class LoggingConfig(BaseSettings):
    level: str
    file: str


class BlacklistConfig(BaseSettings):
    codes: List[str]
    file_extensions: List[str]


class GuiConfig(BaseSettings):
    refresh_interval: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(yaml_file="config.yaml")

    site: SiteConfig
    tags: TagsConfig
    database: DatabaseConfig
    logging: LoggingConfig
    blacklist: BlacklistConfig
    gui: GuiConfig

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (init_settings, env_settings, file_secret_settings, dotenv_settings)
