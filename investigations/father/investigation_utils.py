"""Helpers for the Father investigation notebooks.

The unified notebook uses run_command to print commands and save their latest
stdout and stderr. Paths are supplied by the notebook; this module does not define the case layout.
Parsers only summarize tool text; interpretation belongs in the notebook.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import warnings
from pathlib import Path
from typing import Optional


def run_command(command, label, out_dir) -> subprocess.CompletedProcess[str]:
    """Save exact stdout/stderr bytes in out_dir, replacing draft files.

    Return decoded text for display/parsing; read the saved file for binary data.
    Nonzero exits raise CalledProcessError; stderr is saved only when nonempty.
    """
    args = (
        shlex.split(command)
        if isinstance(command, str)
        else [str(arg) for arg in command]
    )
    print("$", shlex.join(args))
    stdout_path = out_dir / label
    stderr_path = out_dir / (label + ".stderr.txt")
    stderr_path.unlink(
        missing_ok=True
    )  # Clear this label's previous draft error on rerun.
    with stdout_path.open("wb") as stdout:
        result = subprocess.run(
            args, stdout=stdout, stderr=subprocess.PIPE, env={**os.environ, "TZ": "UTC"}
        )
    if result.stderr:
        stderr_path.write_bytes(result.stderr)
    text_result = subprocess.CompletedProcess(
        result.args,
        result.returncode,
        stdout_path.read_text(errors="replace"),
        result.stderr.decode(errors="replace"),
    )
    text_result.check_returncode()
    return text_result


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


# --------------------------------------------------------------------------
# Hashing
# --------------------------------------------------------------------------


def safe_sha256(data_or_path) -> Optional[str]:
    """SHA-256 of bytes, or of a file's content if given a Path/str path.
    Returns None (never raises) if the path does not exist or is empty."""
    try:
        if isinstance(data_or_path, (str, Path)) and Path(data_or_path).is_file():
            data = Path(data_or_path).read_bytes()
        elif isinstance(data_or_path, (bytes, bytearray)):
            data = bytes(data_or_path)
        else:
            return None
    except OSError:
        return None
    if not data:
        return None
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------
# Small parsers for known command output (TSK text formats only)
# --------------------------------------------------------------------------


def parse_label_lines(text: str) -> dict:
    """Split each 'Label: value' line in TSK text output on its first ':'.
    Reused by istat/fsstat parsing -- both are the same plain-text shape,
    and a colon inside a value (e.g. a timestamp's HH:MM:SS) is preserved
    since only the first ':' on the line is used as the split point."""
    fields = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        label, _, value = line.partition(":")
        fields[label.strip()] = value.strip()
    return fields


def parse_mmls_root_offset(mmls_text: str) -> Optional[str]:
    """Pick the root-filesystem candidate from `mmls` output: the largest
    real (numbered, non-Meta/Unallocated) partition slot. Column 3 is the
    start sector, column 5 is the length in sectors."""
    candidates = []
    for line in mmls_text.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        slot = parts[0]
        if not (slot.endswith(":") and slot[:-1].isdigit()):
            continue  # not a numbered slot row (e.g. "Meta", "-------")
        if not parts[1].isdigit():
            continue
        start_sector, length_sectors = parts[2], parts[4]
        candidates.append((int(length_sectors), start_sector))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return str(int(candidates[0][1]))


def get_rootfs_offset(disk_image) -> Optional[str]:
    """Return the first Ext4 partition offset reported by TSK."""
    mmls = subprocess.run(
        ["mmls", str(disk_image)], capture_output=True, text=True, check=True
    )
    # mmls columns: slot, partition number, start sector.
    offsets = re.findall(r"^\s*\d+:\s+\d+\s+(\d+)", mmls.stdout, re.MULTILINE)
    ext4_offsets = []
    for offset in offsets:
        fsstat = subprocess.run(
            ["fsstat", "-o", offset, str(disk_image)], capture_output=True, text=True
        )
        if "File System Type: Ext4" in fsstat.stdout:
            ext4_offsets.append(offset)
    if len(ext4_offsets) > 1:
        warnings.warn(
            f"Multiple Ext4 partitions found: {', '.join(ext4_offsets)}", stacklevel=2
        )
    return ext4_offsets[0] if ext4_offsets else None


def parse_ewfverify(output: str) -> dict:
    """Parse `ewfverify -d <digest>` output for the computed hash and the
    overall SUCCESS/FAILURE verdict."""
    computed_hash = None
    for line in output.splitlines():
        if "calculated over data:" in line:
            _, _, value = line.partition("calculated over data:")
            computed_hash = value.strip()
            break
    return {
        "computed_hash": computed_hash,
        "success": "ewfverify: SUCCESS" in output,
    }


def parse_fsstat(fsstat_text: str) -> dict:
    fields = parse_label_lines(fsstat_text)
    return {
        "fs_type": fields.get("File System Type"),
        "volume_name": fields.get("Volume Name"),
        "unmounted_properly": "Unmounted properly" in fsstat_text,
        "journal_inode": fields.get("Journal Inode"),
        "block_size": int(fields["Block Size"]) if "Block Size" in fields else None,
    }


def parse_istat(istat_text: str) -> dict:
    """`istat` output is plain 'Label: value' lines -- split each line on
    its first ':' rather than using regex."""
    lines = istat_text.splitlines()
    fields = parse_label_lines(istat_text)
    return {
        "inode": fields.get("inode"),
        "allocated": "Allocated" in lines[1] if len(lines) > 1 else None,
        "size_bytes": int(fields["size"]) if "size" in fields else None,
        "symlink_target": fields.get("symbolic link to"),
        "file_modified": fields.get("File Modified"),
        "inode_modified": fields.get("Inode Modified"),
        "file_created": fields.get("File Created"),
        "accessed": fields.get("Accessed"),
    }


def parse_istat_timestamp(ts_str: Optional[str]) -> Optional[str]:
    """Normalize TSK timestamp for comparison. Returns None if invalid or '0000-00-00'."""
    if not ts_str or "0000-00-00" in ts_str:
        return None
    # Strip timezone suffix to ensure sortable YYYY-MM-DD HH:MM:SS.NNNNNNNNN
    return ts_str.partition(" (")[0].strip()


def detect_timestomp(istat_info: dict) -> bool:
    """
    Return True if simple heuristics detect likely timestamp backdating.

    Heuristics:
    1. mtime < crtime (logical impossibility: modification predates birth).
    2. mtime < ctime (supporting signal: mtime pushed back while ctime records metadata change).
    """
    m = parse_istat_timestamp(istat_info.get("file_modified"))
    c = parse_istat_timestamp(istat_info.get("inode_modified"))
    cr = parse_istat_timestamp(istat_info.get("file_created"))

    if not m:
        return False

    # Heuristic 1: Backdating relative to creation (Birth)
    if cr and m < cr:
        return True

    # Heuristic 2: Backdating relative to metadata change (Status Change)
    if c and m < c:
        return True

    return False


def parse_fls_regular_files(fls_text: str) -> list:
    """Parse `fls -p` output lines of the form `r/r 12345:  name` into
    [(inode, name), ...] for live regular files. Deleted entries (marked
    with a leading `*`) are excluded -- use a separate parser/grep for those
    since their inode is frequently reused/unreliable."""
    out = []
    for line in fls_text.splitlines():
        if not line.startswith("r/r"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        inode = parts[1].rstrip(":").split("-")[0]
        name = parts[2].strip()
        out.append((inode, name))
    return out
