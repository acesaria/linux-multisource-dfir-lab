"""Small shared helpers for forensic provenance records."""

from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    """ISO-8601 UTC with microsecond resolution."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_output(
    command: list[str],
    *,
    allow_nonzero: bool = False,
    timeout: int = 30,
) -> str | None:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 and not allow_nonzero:
        return None
    return "\n".join(
        stream.strip()
        for stream in (result.stdout, result.stderr)
        if stream and stream.strip()
    )
