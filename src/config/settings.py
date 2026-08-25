from dataclasses import dataclass
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _float_env(name: str, default: float) -> float:
    raw = getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _int_env(name: str, default: int) -> int:
    raw = getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(getenv("DATA_DIR", "data"))
    gemini_api_key: str | None = getenv("GEMINI_API_KEY")
    llm_model: str = getenv("LLM_MODEL", "gemini-3.6-flash")
    llm_temperature: float = _float_env("LLM_TEMPERATURE", 0.0)
    llm_timeout_seconds: float = _float_env("LLM_TIMEOUT_SECONDS", 10.0)
    llm_max_retries: int = _int_env("LLM_MAX_RETRIES", 1)
    exchange_api_url: str = getenv("EXCHANGE_API_URL", "https://open.er-api.com/v6/latest")


settings = Settings()
