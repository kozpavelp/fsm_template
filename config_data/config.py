from environs import Env
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str
#    admin_ids: list


@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str | None) -> Config:
    env: Env = Env()
    env.read_env(path)
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN')))
