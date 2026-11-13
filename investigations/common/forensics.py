from __future__ import annotations

import hashlib
import json
import posixpath
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

import pandas as pd


@dataclass
class Finding:
    claim_id: str
    source: str
    status: Literal[
        "supported",
        "partial",
        "unsupported",
        "not_applicable",
        "not_examined",
        "tool_failure",
    ]
    locator: str
    observation: str
    limitation: str


STATUSES = ("supported", "partial", "unsupported", "not_applicable", "not_examined", "tool_failure")
SOURCES = ("disk", "timeline", "ram")


def dump_findings(findings: list[Finding], path: str | Path) -> None:
    Path(path).write_text(
        json.dumps([asdict(finding) for finding in findings], indent=2) + "\n",
        encoding="utf-8",
    )


def propose(elements: dict[str, bool] | None, failed: bool = False) -> str:
    """Strict element rule (ac, 2026-10-01): every element of the claim observed in the source is
    supported, some is partial, none is unsupported; None means the examination did not run."""
    if failed:
        return "tool_failure"
    if elements is None:
        return "not_examined"
    seen = sum(bool(value) for value in elements.values())
    return "supported" if seen == len(elements) else "partial" if seen else "unsupported"


def finding(store: dict, claim_id: str, source: str, elements: dict[str, bool] | None, *,
            origins: list[int], locator: str, observation: str, limitation: str,
            failed: bool = False) -> dict[str, Any]:
    """Record the proposed finding for one claim/source cell; a rerun replaces it."""
    store[(claim_id, source)] = {
        "claim_id": claim_id, "source": source, "status": propose(elements, failed),
        "elements": dict(elements or {}), "origins": sorted(set(origins)),
        "locator": locator, "observation": observation, "limitation": limitation,
    }
    marks = "; ".join(f"{name} {'yes' if seen else 'no'}" for name, seen in (elements or {}).items())
    print(f"proposed {claim_id} / {source}: {store[(claim_id, source)]['status']} "
          f"({marks or 'no examination'})")
    return store[(claim_id, source)]


def check_findings(rows: list[dict[str, Any]], claim_ids: list[str], complete: bool = True) -> None:
    """Raise on an unknown claim, source or status, a duplicate cell, or (if complete) a missing
    cell: omission never stands for a status."""
    seen = set()
    for row in rows:
        key = (row["claim_id"], row["source"])
        if row["claim_id"] not in claim_ids or row["source"] not in SOURCES:
            raise ValueError(f"unknown cell {key}")
        if row["status"] not in STATUSES:
            raise ValueError(f"unknown status {row['status']!r} for {key}")
        if key in seen:
            raise ValueError(f"duplicate cell {key}")
        seen.add(key)
    missing = [(c, s) for c in claim_ids for s in SOURCES if (c, s) not in seen]
    if complete and missing:
        raise ValueError(f"cells without an explicit status: {missing}")


def support_rates(grid: pd.DataFrame) -> pd.DataFrame:
    """Per-source status counts and support rate S / (S + P + U); a zero denominator is not
    calculable. N/A, not_examined and tool_failure stay outside the denominator."""
    rows = []
    for source in grid.columns:
        n = {status: int((grid[source] == status).sum()) for status in STATUSES}
        investigated = n["supported"] + n["partial"] + n["unsupported"]
        rows.append({"source": source, **n, "investigated": investigated,
                     "support_rate": f"{n['supported']}/{investigated}" if investigated
                     else "not calculable"})
    return pd.DataFrame(rows).set_index("source")


def contribution(cells: pd.DataFrame, joint: dict[str, str]) -> pd.DataFrame:
    """Table 3 counts. Corroborated: two supported sources whose origin sets are disjoint.
    Jointly sufficient: claims the analyst argued in `joint`. Source totals overlap."""
    supported = cells[cells["status"] == "supported"]
    by_claim = supported.groupby("claim_id")
    claims = list(dict.fromkeys(cells["claim_id"]))

    def corroborated(group: pd.DataFrame) -> bool:
        origin_sets = [set(origins) for origins in group["origins"]]
        return any(a.isdisjoint(b) for i, a in enumerate(origin_sets) for b in origin_sets[i + 1:])

    sources_of = {claim: set(group["source"]) for claim, group in by_claim}
    measures = [(f"independently sufficient: {source}",
                 sorted(supported.loc[supported["source"] == source, "claim_id"]))
                for source in SOURCES]
    measures += [
        ("corroborated (disjoint origins)", [c for c, g in by_claim if corroborated(g)]),
        ("jointly sufficient (analyst argument)", [c for c in claims if c in joint]),
        ("unresolved", [c for c in claims if c not in sources_of and c not in joint]),
        ("supported by exactly one source", [c for c, s in sources_of.items() if len(s) == 1]),
        ("RAM-only support", [c for c, s in sources_of.items() if s == {"ram"}]),
        ("disk/timeline-only support", [c for c, s in sources_of.items() if "ram" not in s]),
    ]
    return pd.DataFrame([{"measure": m, "count": len(c), "claims": ", ".join(c)}
                         for m, c in measures]).set_index("measure")


def sh(
    cmd: str,
    *,
    label: str | None = None,
    out_dir: str | Path | None = None,
    binary: bool = False,
    check: bool = False,
    show: bool = True,
    tail: int | None = None,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    """Run a Bash command, preserving stdout and stderr as separate streams."""
    if show:
        print(f"$ {cmd}", flush=True)
    result = subprocess.run(
        cmd,
        shell=True,
        executable="/bin/bash",
        capture_output=True,
        text=not binary,
        errors=None if binary else "backslashreplace",
        check=False,
    )

    if label is not None and out_dir is not None:
        output_dir = Path(out_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_name = label if (binary or label.endswith(".txt")) else f"{label}.txt"
        stdout_path = output_dir / output_name
        stderr_path = output_dir / f"{output_name}.stderr.txt"

        if binary:
            stdout_path.write_bytes(result.stdout)
            if result.stderr:
                stderr_path.write_bytes(result.stderr)
            elif stderr_path.exists():
                stderr_path.unlink()
        else:
            stdout_path.write_text(result.stdout)
            if result.stderr:
                stderr_path.write_text(result.stderr)
            elif stderr_path.exists():
                stderr_path.unlink()

    if show:
        stdout = result.stdout
        stderr = result.stderr
        if tail is not None:
            if tail < 0:
                raise ValueError("tail must be non-negative")
            if binary:
                stdout = b"" if tail == 0 else b"".join(stdout.splitlines(keepends=True)[-tail:])
                stderr = b"" if tail == 0 else b"".join(stderr.splitlines(keepends=True)[-tail:])
            else:
                stdout = "" if tail == 0 else "".join(stdout.splitlines(keepends=True)[-tail:])
                stderr = "" if tail == 0 else "".join(stderr.splitlines(keepends=True)[-tail:])
        if binary:
            sys.stdout.buffer.write(stdout)
            sys.stdout.buffer.flush()
            sys.stderr.buffer.write(stderr)
            sys.stderr.buffer.flush()
        else:
            sys.stdout.write(stdout)
            sys.stdout.flush()
            sys.stderr.write(stderr)
            sys.stderr.flush()

    if check and result.returncode:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result


def q(value: Any) -> str:
    """Quote an evidence-derived value for use in a shell command."""
    return shlex.quote(str(value))


def load_case(project_root: str | Path, run_id: str) -> SimpleNamespace:
    """Load one run's manifest, acquisition record, evidence, and work paths."""
    root = Path(project_root)
    run_root = root / "shared" / "experiments" / run_id
    manifest = json.loads((run_root / "manifest.json").read_text())
    acquisition = json.loads((run_root / "dumps" / "acquisition.json").read_text())
    if manifest["run_id"] != run_id:
        raise ValueError(
            f"manifest run_id {manifest['run_id']!r} does not match {run_id!r}"
        )

    platform = manifest["platform"]
    kernel = manifest.get("kernel_release")
    if kernel is None and isinstance(platform, dict):
        kernel = platform.get("kernel_release") or platform.get("kernel")
    if not kernel:
        raise KeyError("manifest does not record a kernel release")
    isf_matches = sorted((root / "shared" / "isf").glob(f"*{kernel}*.json*"))
    if len(isf_matches) != 1:
        raise ValueError(f"expected one ISF for kernel {kernel!r}, found {isf_matches}")

    dumps = run_root / "dumps"
    disk_image = dumps / acquisition["disk"]["path"]
    memory_image = dumps / acquisition["memory"]["path"]
    disk_segments = tuple(dumps / segment for segment in acquisition["disk"]["segments"])
    return SimpleNamespace(
        run_root=run_root,
        disk_image=disk_image,
        disk_segments=disk_segments,
        memory_image=memory_image,
        claims=manifest["claims"],
        platform=platform,
        timezone=platform["timezone"],
        manifest=manifest,
        acquisition=acquisition,
        isf_path=isf_matches[0],
        data=run_root / "investigation" / "data",
        output=run_root / "investigation" / "output",
        recovered=run_root / "investigation" / "recovered",
        findings=run_root / "investigation" / "findings",
        prepared=run_root / "investigation" / "prepared",
    )


def root_fs(image: str | Path) -> tuple[int, int, str]:
    """Return the unique Ext4 partition's sector offset, sector size, and type."""
    image_arg = q(image)
    layout = sh(f"mmls {image_arg}", check=True, show=False)
    unit_match = re.search(r"Units are in (\d+)-byte sectors", layout.stdout)
    if unit_match is None:
        raise ValueError("mmls output does not contain a sector-size declaration")
    sector_size = int(unit_match.group(1))

    starts: list[int] = []
    for line in layout.stdout.splitlines():
        match = re.match(r"^\s*\d+:\s+\S+\s+(\d+)\s+\d+\s+\d+\s+", line)
        if match:
            starts.append(int(match.group(1)))

    candidates: list[tuple[int, int, str]] = []
    for offset in starts:
        stats = sh(
            f"fsstat -b {q(sector_size)} -o {q(offset)} {image_arg}",
            show=False,
        )
        fs_match = re.search(r"^File System Type:\s*(Ext4[^\r\n]*)", stats.stdout, re.M)
        if stats.returncode == 0 and fs_match:
            candidates.append((offset, sector_size, fs_match.group(1).strip()))

    if len(candidates) != 1:
        raise ValueError(
            f"expected one Ext4 partition, found {len(candidates)}: {candidates}"
        )
    return candidates[0]


class ResolveError(Exception):
    """A guest path could not be resolved; .chain holds what was observed."""

    def __init__(self, message: str, chain: list[dict[str, Any]]):
        super().__init__(message)
        self.chain = chain


def _ifind(image: str | Path, offset: int, path: str, chain: list) -> str:
    found = sh(f"ifind -o {q(offset)} -n {q(path)} {q(image)}", show=False)
    lines = [line.strip() for line in found.stdout.splitlines() if line.strip()]
    if found.returncode or len(lines) != 1 or not re.match(r"^\d+", lines[0]):
        raise ResolveError(f"ifind did not return one inode for {path}: {lines}", chain)
    return re.match(r"^(\d+(?:-\d+-\d+)?)", lines[0]).group(1)


def _symlink_target(image: str | Path, offset: int, inode: str, chain: list) -> str | None:
    stats = sh(f"istat -o {q(offset)} {q(image)} {q(inode)}", show=False)
    if stats.returncode:
        raise ResolveError(f"istat failed for inode {inode}", chain)
    match = re.search(r"^\s*symbolic link to:?\s*(.+?)\s*$", stats.stdout, re.M | re.I)
    return match.group(1).strip("'\"`") if match else None


def resolve(image: str | Path, offset: int, guest_path: str) -> tuple[str, list[dict[str, Any]]]:
    """Resolve a guest path to an inode, following symlinks observed in the evidence.

    Returns (inode, chain); each chain entry is {"path", "inode"} plus "target" when that
    component was a symlink. Raises ResolveError, carrying the partial chain, when the path
    cannot be resolved. Guest paths are never resolved against the examiner's filesystem.
    """
    chain: list[dict[str, Any]] = []
    parts = [part for part in posixpath.normpath("/" + guest_path).split("/") if part]
    seen: set[str] = set()

    while True:
        prefix = ""
        for index, part in enumerate(parts):
            prefix = f"{prefix}/{part}"
            entry = {"path": prefix, "inode": _ifind(image, offset, prefix, chain)}
            chain.append(entry)

            target = _symlink_target(image, offset, entry["inode"], chain)
            if target is None:
                continue
            entry["target"] = target

            base = target if target.startswith("/") else posixpath.join(
                posixpath.dirname(prefix), target)
            following = posixpath.normpath(
                "/" + "/".join([base.lstrip("/"), *parts[index + 1:]]))
            if following in seen:
                raise ResolveError(f"symlink cycle at {prefix}", chain)
            seen.add(following)
            parts = [part for part in following.split("/") if part]
            break
        else:
            return chain[-1]["inode"], chain


def load_bodyfile(path: str | Path) -> pd.DataFrame:
    """Read an 11-field TSK bodyfile with source locators and UTC timestamps.

    Filename bytes that are not valid UTF-8 are shown escaped (\\xNN) rather than
    aborting the load; the raw bytes remain in the preserved bodyfile.
    """
    source = Path(path)
    fields = [
        "md5",
        "name",
        "inode",
        "mode",
        "uid",
        "gid",
        "size",
        "atime",
        "mtime",
        "ctime",
        "crtime",
    ]
    records: list[dict[str, Any]] = []
    malformed: list[int] = []
    with source.open(encoding="utf-8", errors="backslashreplace") as bodyfile:
        for line_number, line in enumerate(bodyfile, 1):
            values = line.rstrip("\r\n").split("|")
            if len(values) < 11:
                malformed.append(line_number)
                continue
            if len(values) > 11:
                values = values[:1] + ["|".join(values[1 : len(values) - 9])] + values[-9:]
            record = dict(zip(fields, values, strict=True))
            record["name_raw"] = record["name"]
            if record["name"].endswith("(deleted-realloc)"):
                record["name_state"] = "deleted-realloc"
            elif record["name"].endswith("(deleted)"):
                record["name_state"] = "deleted"
            else:
                record["name_state"] = "allocated"
            record["locator"] = f"{source.name}#L{line_number}"
            records.append(record)
    if malformed:
        print(
            f"warning: {len(malformed)} unparsable rows in {source.name}"
            f" (first lines: {malformed[:10]})"
        )

    frame = pd.DataFrame(records)
    if frame.empty:
        return pd.DataFrame(
            columns=fields
            + ["name_raw", "name_state", "locator"]
            + [f"{column}_utc" for column in ("atime", "mtime", "ctime", "crtime")]
        )
    for column in ("uid", "gid", "size", "atime", "mtime", "ctime", "crtime"):
        frame[column] = pd.to_numeric(frame[column], errors="raise").astype("Int64")
    for column in ("atime", "mtime", "ctime", "crtime"):
        values = frame[column].mask(frame[column] == 0)
        frame[f"{column}_utc"] = pd.to_datetime(values, unit="s", utc=True)
    return frame


def load_vol(path: str | Path) -> pd.DataFrame:
    """Flatten Volatility 3 JSON rows while retaining hierarchy and locators."""
    source = Path(path)
    payload = json.loads(source.read_text())
    if isinstance(payload, list):
        roots = payload
        root_pointer = ""
    elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        roots = payload["rows"]
        root_pointer = "/rows"
    elif isinstance(payload, dict):
        roots = [payload]
        root_pointer = ""
    else:
        raise ValueError(f"unsupported Volatility JSON root in {source}")

    records: list[dict[str, Any]] = []
    stack: list[tuple[Any, str, str | None]] = [
        (row, f"{root_pointer}/{index}", None)
        for index, row in reversed(list(enumerate(roots)))
    ]
    while stack:
        node, pointer, parent = stack.pop()
        if not isinstance(node, dict):
            raise ValueError(f"non-object Volatility row at {pointer}")
        children = node.get("__children", [])
        if not isinstance(children, list):
            raise ValueError(f"non-list __children at {pointer}")
        locator = f"{source.name}#{pointer}"
        record = {key: value for key, value in node.items() if key != "__children"}
        record["parent_locator"] = parent
        record["locator"] = locator
        records.append(record)
        for index, child in reversed(list(enumerate(children))):
            stack.append((child, f"{pointer}/__children/{index}", locator))

    frame = pd.DataFrame(records)
    for column in frame.columns:
        if pd.api.types.is_float_dtype(frame[column]):
            present = frame[column].dropna()
            if present.empty or present.map(lambda value: float(value).is_integer()).all():
                frame[column] = frame[column].astype("Int64")
    return frame


def load_plaso(path: str | Path) -> pd.DataFrame:
    """Read Plaso JSONL in chunks with raw timestamps and line locators."""
    source = Path(path)
    frames: list[pd.DataFrame] = []
    records: list[dict[str, Any]] = []
    with source.open(encoding="utf-8", errors="backslashreplace") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"non-object Plaso record at {source.name}#L{line_number}")
            record["locator"] = f"{source.name}#L{line_number}"
            records.append(record)
            if len(records) == 50_000:
                frames.append(pd.DataFrame.from_records(records))
                records = []
    if records:
        frames.append(pd.DataFrame.from_records(records))
    if not frames:
        return pd.DataFrame(columns=["locator"])

    frame = pd.concat(frames, ignore_index=True)
    if "timestamp" in frame:
        timestamps = pd.to_numeric(frame["timestamp"], errors="coerce")
        if timestamps.dropna().map(lambda value: float(value).is_integer()).all():
            frame["timestamp"] = timestamps.astype("Int64")
        frame["timestamp_utc"] = pd.to_datetime(timestamps, unit="us", utc=True)
    return frame


def sha256_file(path: str | Path) -> str:
    """Return a streaming SHA-256 digest for a file."""
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def show(
    df: pd.DataFrame,
    cols: list[str] | tuple[str, ...] | None = None,
    n: int = 20,
    caption: str | None = None,
) -> None:
    """Display a bounded DataFrame view with an explicit row count."""
    from IPython.display import Markdown, display

    view = df if cols is None else df.loc[:, list(cols)]
    heading = f"{caption} — " if caption else ""
    display(Markdown(f"**{heading}showing {min(n, len(view))} of {len(df)} rows**"))
    with pd.option_context("display.max_columns", None, "display.width", 200,
                           "display.max_colwidth", 60):
        display(view.head(n))
