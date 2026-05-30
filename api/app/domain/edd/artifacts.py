from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml_document(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = f"Expected mapping at root of {path.name}"
        raise ValueError(msg)
    return payload
