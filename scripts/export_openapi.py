from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "api"
sys.path.insert(0, str(API_ROOT))
os.environ.setdefault("APP_OTEL_ENABLED", "false")

from app.main import create_app  # noqa: E402


def main() -> None:
    output_path = API_ROOT / "openapi" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    schema = create_app().openapi()
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
