"""RAM capture while the VM is on, and EWF disk acquisition after shutdown.

The orchestrator owns VM state and persists the records supplied to these
methods, including partial metadata when an acquisition raises.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TextIO, TypedDict

from orchestrator.core import console
from orchestrator.core.paths import ProjectPaths
from orchestrator.core.provenance import command_output, file_sha256, utc_now

_RAW_STAGING_DIR = Path("/dev/shm")


class AcquisitionMetadata(TypedDict):
    path: str
    sha256: str | None
    size_bytes: int | None
    tool: str
    tool_version: dict[str, str | None]
    started_at: str | None
    ended_at: str | None
    duration_seconds: float | None
    exit_status: int | None


class AcquisitionRecord(AcquisitionMetadata, total=False):
    segments: list[str]
    hash_scope: str
    error: str


class AcquisitionManifest(TypedDict):
    memory: AcquisitionRecord | None
    disk: AcquisitionRecord | None


def acquisition_record(path: Path, tool: str) -> AcquisitionRecord:
    """Paths in acquisition.json are relative to its dumps directory."""
    return {
        "path": str(path.relative_to(path.parent.parent)),
        "sha256": None,
        "size_bytes": None,
        "tool": tool,
        "tool_version": {},
        "started_at": None,
        "ended_at": None,
        "duration_seconds": None,
        "exit_status": None,
    }


class Dumper:
    def __init__(self, paths: ProjectPaths) -> None:
        self._paths = paths

    def run_dir(self, run_id: str) -> Path:
        directory = self._paths.run_dumps_dir(run_id)
        (directory / "memory").mkdir(parents=True, exist_ok=True)
        (directory / "disk").mkdir(parents=True, exist_ok=True)
        return directory

    def acquire_memory(
        self,
        domain: str,
        dest: Path,
        record: AcquisitionRecord,
        log: TextIO,
    ) -> None:
        """Update the caller's record even when capture or hashing fails."""
        record["tool_version"] = {"virsh": _tool_version(["virsh", "--version"])}
        dest.parent.mkdir(parents=True, exist_ok=True)
        # libvirt preserves this user-owned file; never replace prior evidence.
        dest.touch(mode=0o600, exist_ok=False)
        dest.chmod(0o600)
        console.step(f"acquiring memory from '{domain}'...")
        try:
            _run_command(
                ["virsh", "dump", domain, str(dest), "--memory-only"],
                record,
                log,
            )
        finally:
            if dest.exists():
                record["size_bytes"] = dest.stat().st_size
        if not record["size_bytes"]:
            record["error"] = "memory output is missing or empty"
            raise RuntimeError(record["error"])
        try:
            record["sha256"] = file_sha256(dest)
        except OSError:
            record["error"] = "memory output could not be hashed"
            raise
        console.ok(f"memory dump done: {dest} ({record['size_bytes']} bytes)")

    def acquire_disk(
        self,
        source: Path,
        dest: Path,
        record: AcquisitionRecord,
        log: TextIO,
    ) -> None:
        """Convert the offline disk, package EWF, and verify its logical SHA-256."""
        record["hash_scope"] = "logical_disk"
        record["segments"] = []
        record["tool_version"] = {
            "qemu-img": _tool_version(["qemu-img", "--version"]),
            "ewfacquire": _tool_version(["ewfacquire", "-V"]),
            "ewfverify": _tool_version(["ewfverify", "-V"]),
        }
        dest.parent.mkdir(parents=True, exist_ok=True)
        prefix = dest.with_suffix("")
        if any(dest.parent.glob(f"{prefix.name}.E??")):
            raise FileExistsError(f"EWF output already exists: {prefix}.E??")
        record["size_bytes"] = self._qemu_virtual_size(source)
        console.step(f"acquiring disk from '{source.stem}'...")
        # Keep only the temporary conversion on tmpfs; context cleanup also
        # handles conversion/packaging failures without deleting EWF evidence.
        with tempfile.TemporaryDirectory(
            prefix="dfir-disk-", dir=_RAW_STAGING_DIR
        ) as staging:
            raw = Path(staging) / "disk.raw"
            started = time.monotonic()
            try:
                _run_command(
                    ["qemu-img", "convert", "-O", "raw", str(source), str(raw)],
                    record,
                    log,
                    started=started,
                )
                _run_command(
                    [
                        "ewfacquire",
                        "-u",
                        "-q",
                        "-c",
                        "empty-block",
                        "-d",
                        "sha256",
                        "-j",
                        str(max(1, (os.cpu_count() or 4) // 2)),
                        "-t",
                        str(prefix),
                        str(raw),
                    ],
                    record,
                    log,
                    started=started,
                )
                segments = sorted(dest.parent.glob(f"{prefix.name}.E??"))
                if not segments or any(
                    segment.stat().st_size == 0 for segment in segments
                ):
                    record["error"] = (
                        "EWF output is missing or contains an empty segment"
                    )
                    raise RuntimeError(record["error"])
                result = _run_command(
                    ["ewfverify", "-d", "sha256", str(segments[0])],
                    record,
                    log,
                    started=started,
                )
                digest = _parse_ewfverify_sha256(result.stdout + "\n" + result.stderr)
                if digest is None:
                    record["error"] = "ewfverify did not report a calculated SHA-256"
                    raise RuntimeError(record["error"])
                record["sha256"] = digest
            finally:
                record["segments"] = [
                    str(segment.relative_to(dest.parent.parent))
                    for segment in sorted(dest.parent.glob(f"{prefix.name}.E??"))
                ]
        console.ok(
            f"disk acquisition verified: {dest} ({record['size_bytes']} logical bytes)"
        )

    def write_manifest(self, run_id: str, metadata: AcquisitionManifest) -> str:
        path = self.run_dir(run_id) / "acquisition.json"
        path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        return str(path)

    @staticmethod
    def _qemu_virtual_size(source: Path) -> int:
        command = ["qemu-img", "info", "--output", "json", str(source.absolute())]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                f"qemu-img info failed: {result.stderr or result.stdout}"
            )
        info = json.loads(result.stdout)
        size = info.get("virtual-size")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise RuntimeError(
                "qemu-img info did not report a positive integer virtual-size: "
                f"{result.stdout}\n{result.stderr}"
            )
        return size


def _tool_version(command: list[str]) -> str | None:
    output = command_output(command, allow_nonzero=True)
    return output.splitlines()[0] if output else None


def _run_command(
    command: list[str],
    record: AcquisitionRecord,
    log: TextIO,
    *,
    started: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Bracket the subprocess itself; send diagnostics only to the text log."""
    log.write(f"$ {shlex.join(command)}\n")
    log.flush()
    if started is None:
        started = time.monotonic()
    record["exit_status"] = None
    if record["started_at"] is None:
        record["started_at"] = utc_now()
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError:
        record["error"] = f"could not execute {command[0]}"
        raise
    finally:
        record["ended_at"] = utc_now()
        record["duration_seconds"] = time.monotonic() - started
    record["exit_status"] = result.returncode
    log.write(result.stdout or "")
    log.write(result.stderr or "")
    log.write(f"\nexit_status={result.returncode}\n")
    log.flush()
    if result.returncode != 0:
        record["error"] = f"{command[0]} exited with status {result.returncode}"
        raise RuntimeError(record["error"])
    return result


def _parse_ewfverify_sha256(output: str) -> str | None:
    match = re.search(
        r"^SHA256 hash calculated over data:\s*([0-9a-fA-F]{64})\s*$",
        output,
        flags=re.MULTILINE,
    )
    return match.group(1).lower() if match else None
