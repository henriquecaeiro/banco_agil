from dataclasses import dataclass
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(getenv("DATA_DIR", "data"))
    gemini_api_key: str | None = getenv("GEMINI_API_KEY")
    llm_model: str = getenv("LLM_MODEL", "gemini-2.0-flash")
    exchange_api_url: str = getenv("EXCHANGE_API_URL", "https://open.er-api.com/v6/latest")


settings = Settings()
