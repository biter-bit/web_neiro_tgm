import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json


class Settings(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    TTL: int
    PATH_WORK: str = os.getcwd()
    PATH_ENV: str = f'{PATH_WORK}/.env'
    LEVEL_LOGGER: str
    TOKEN_TELEGRAM_BOT: str
    USERNAME_BOT: str
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
    RECURRING: bool
    REDIS_HOST: str
    REDIS_PORT: int
    CHANNELS_IDS: str
    CHANNELS_NAMES: str
    CHANNELS_INFO: str
    ADMIN_IDS: str

    model_config = SettingsConfigDict(env_file=PATH_ENV)

    @field_validator("ADMIN_IDS")
    def admins_ids_change_on_list(cls, v):
        return v.split(',')

    @field_validator("CHANNELS_IDS")
    def channels_ids_change_on_list(cls, v):
        return list(map(int, v.split(',')))

    @field_validator("CHANNELS_NAMES")
    def admins_names_change_on_list(cls, v):
        return v.split(',')

    @field_validator("CHANNELS_INFO")
    def admins_names_change_on_list(cls, v):
        return json.loads(v)

    # @model_validator(mode="before")
    # def admins_ids_change_on_list(cls, values):
    #     if 'ADMIN_IDS' in values:
    #         values['ADMIN_IDS'] = values['ADMIN_IDS'].split(',')
    #     if "CHANNELS_IDS" in values:
    #         print(f"Raw CHANNELS_IDS value: {values['CHANNELS_IDS']}")
    #         values['CHANNELS_IDS'] = list(map(int, values['CHANNELS_IDS'].split(',')))
    #     if "CHANNELS_NAMES" in values:
    #         values['CHANNELS_NAMES'] = values['CHANNELS_NAMES'].split(',')
    #     return values

    @property
    def url_connect_with_psycopg2(self):
        # postgresql+psycopg2://db_user:db_pass@db_host:db_port/db_name
        return f'postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def url_connect_with_asyncpg(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


settings = Settings()