"""Persistent config stored as JSON. No OS-specific logic."""

import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

_DEFAULTS: dict[str, Any] = {
    "device_address": None,
    "last_color": {"r": 255, "g": 255, "b": 255},
    "last_brightness": 100,
    "last_power": True,
}


def load() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            return {**_DEFAULTS, **data}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def save(data: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2))


def get(key: str) -> Any:
    return load().get(key)


def set_value(key: str, value: Any) -> None:
    data = load()
    data[key] = value
    save(data)
