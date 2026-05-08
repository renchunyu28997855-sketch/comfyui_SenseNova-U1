from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://token.sensenova.cn/v1"
BASE_URL_ENV = "SN_BASE_URL"
CONFIG_FILE = Path(__file__).parent / "api_key.txt"


@dataclass(frozen=True)
class SenseNovaConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL


def _load_api_key_from_file() -> str:
    """Load API key from api_key.txt file in the same directory."""
    if CONFIG_FILE.exists():
        content = CONFIG_FILE.read_text().strip()
        if content:
            return content
    return ""


def load_config() -> SenseNovaConfig:
    # Priority: environment variable > api_key.txt file
    api_key = os.getenv("SN_API_KEY", "").strip()
    if not api_key:
        api_key = _load_api_key_from_file()
    if not api_key:
        raise RuntimeError(
            "Missing SN_API_KEY. Set it in environment variable or create "
            "a 'api_key.txt' file in the plugin directory."
        )

    base_url = os.getenv(BASE_URL_ENV, DEFAULT_BASE_URL).strip().rstrip("/")
    if not base_url:
        base_url = DEFAULT_BASE_URL

    return SenseNovaConfig(api_key=api_key, base_url=base_url)
