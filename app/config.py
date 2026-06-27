from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    output_dir: Path = PROJECT_ROOT / "outputs"
    replay_file: Path = PROJECT_ROOT / "demo" / "replay_ai_news.json"
    sources_file: Path = PROJECT_ROOT / "config" / "sources.yaml"
    llm_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_temperature: float = 0.0

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv(PROJECT_ROOT / ".env")
        return cls(
            llm_model=os.getenv("LLM_MODEL", "deepseek-chat"),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
        )

    def load_sources(self) -> dict:
        with self.sources_file.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

