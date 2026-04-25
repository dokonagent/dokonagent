import json
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    ADMIN_IDS: List[int] = []
    WEBAPP_URL: str = ""
    WEB_HOST: str = "0.0.0.0"
    PORT: Optional[int] = None
    WEB_PORT: int = 8080
    DB_PATH: str = "zakaz_bot.db"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, (int, float)):
            return [int(value)]
        if isinstance(value, list):
            return [int(v) for v in value]
        if isinstance(value, str):
            raw = value.strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [int(v) for v in parsed]
            except json.JSONDecodeError:
                pass
            return [int(v.strip()) for v in raw.split(",") if v.strip()]
        return value


settings = Settings()

if settings.PORT is not None:
    settings.WEB_PORT = settings.PORT

if not settings.BOT_TOKEN:
    # Keep startup error explicit instead of a cryptic pydantic traceback.
    raise RuntimeError("BOT_TOKEN is empty. Set BOT_TOKEN in Railway Variables.")
