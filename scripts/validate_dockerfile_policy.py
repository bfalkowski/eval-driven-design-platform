from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCKERFILES = (
    REPO_ROOT / "api" / "Dockerfile",
    REPO_ROOT / "console" / "Dockerfile",
    REPO_ROOT / "worker" / "Dockerfile",
)


def main() -> None:
    dockerfiles = [Path(path) for path in sys.argv[1:]] or list(DEFAULT_DOCKERFILES)
    errors: list[str] = []

    for dockerfile in dockerfiles:
        if not dockerfile.is_file():
            errors.append(f"{dockerfile}: Dockerfile not found.")
            continue
        errors.extend(_validate_dockerfile(dockerfile))

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)

    print(f"Dockerfile policy checks passed for {len(dockerfiles)} image(s)")


def _validate_dockerfile(dockerfile: Path) -> list[str]:
    text = dockerfile.read_text(encoding="utf-8")
    instructions = _instructions(text)
    label = str(dockerfile.relative_to(REPO_ROOT))
    errors: list[str] = []

    from_instruction = _first_instruction(instructions, "FROM")
    if from_instruction is None:
        errors.append(f"{label}: must define a base image with FROM.")
    elif ":latest" in from_instruction.lower():
        errors.append(f"{label}: base image must not use the latest tag.")

    if not _has_instruction(instructions, "USER", "app"):
        errors.append(f"{label}: must switch to the non-root app user.")

    if not re.search(r"^\s*RUN\s+.*pip install .*--no-cache-dir", text, re.MULTILINE | re.DOTALL):
        errors.append(f"{label}: pip installs must use --no-cache-dir.")

    if not _has_exec_form_command(instructions, "CMD"):
        errors.append(f"{label}: must use exec-form CMD.")

    return errors


def _strip_continuation(line: str) -> str:
    if line.endswith("\\"):
        return line[:-1].strip()
    return line.strip()


def _instructions(text: str) -> list[str]:
    lines: list[str] = []
    current = ""
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        continuation = _strip_continuation(stripped)
        if current:
            current = f"{current} {continuation}"
        else:
            current = continuation
        if not stripped.endswith("\\"):
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


def _first_instruction(instructions: list[str], name: str) -> str | None:
    prefix = f"{name} "
    for instruction in instructions:
        if instruction.upper().startswith(prefix):
            return instruction
    return None


def _has_instruction(instructions: list[str], name: str, value: str) -> bool:
    expected = f"{name} {value}".upper()
    return any(instruction.upper() == expected for instruction in instructions)


def _has_exec_form_command(instructions: list[str], name: str) -> bool:
    prefix = f"{name} "
    for instruction in instructions:
        if instruction.upper().startswith(prefix):
            return instruction[len(prefix) :].strip().startswith("[")
    return False


if __name__ == "__main__":
    main()
