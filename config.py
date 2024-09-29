import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    PATH_WORK: str = os.getcwd()
    PATH_ENV: str = f'{PATH_WORK}/.env'
    LEVEL_LOGGER: str
    TOKEN_TELEGRAM_BOT: str
    OPENAI_API_KEY: str
    NOT_OFFICIAL_OPENAI_API_KEY: str
    USEAPI_API_KEY: str
    RAPID_API_TOKEN: str
    PROXY: str
    OPENAI_BASE_URL: str
    NOT_OFFICIAL_OPENAI_BASE_URL: str
    ROBOKASSA_LOGIN: str
    ROBOKASSA_PASS_1: str
    ROBOKASSA_PASS_2: str
    # CHANNELS_IDS: list = [-1001381927809, -1001763475267]
    # CHANNELS_IDS: list = ['https://t.me/+GdDYmSqNFzI5NjEy', -1001763475267]
    CHANNELS_IDS: list = [-1002331503013]
    CHANNELS_NAMES: list = ['sdfafasfdasdfsa']

    @property
    def url_connect_with_psycopg2(self):
        # postgresql+psycopg2://db_user:db_pass@db_host:db_port/db_name
        return f'postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def url_connect_with_asyncpg(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    model_config = SettingsConfigDict(env_file=PATH_ENV)


settings = Settings()