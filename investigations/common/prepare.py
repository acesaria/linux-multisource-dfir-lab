from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from investigations.common.forensics import (
    load_case,
    load_plaso,
    q,
    root_fs,
    sh,
    sha256_file,
)


TOOLS = (
    "mmls",
    "fls",
    "istat",
    "icat",
    "ifind",
    "fcat",
    "blkls",
    "blkcalc",
    "mactime",
    "ewfverify",
    "ewfmount",
    "debugfs",
    "ext4magic",
    "foremost",
    "log2timeline",
    "psort",
    "pinfo",
    "vol3",
    "ewfinfo",
    "fsstat",
    "ils",
)

DISK_PRODUCTS = (
    "ewfinfo",
    "ewfverify",
    "mmls",
    "allocated.body",
    "unallocated.body",
    "unallocated.dd",
)

RAM_PLUGINS = (
    ("banners", "banners.Banners"),
    ("pslist", "linux.pslist.PsList"),
    ("psaux", "linux.psaux.PsAux"),
    ("pstree", "linux.pstree.PsTree"),
    ("proc.Maps", "linux.proc.Maps"),
    ("lsof", "linux.lsof.Lsof"),
    ("sockstat", "linux.sockstat.Sockstat"),
    ("lsmod", "linux.lsmod.Lsmod"),
    ("kmsg", "linux.kmsg.Kmsg"),
    ("pagecache.Files", "linux.pagecache.Files"),
    ("psscan", "linux.psscan.PsScan"),
)

TIMELINE_PRODUCTS = ("timeline.plaso", "timeline.jsonl", "pinfo")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save(record: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


def tool_inventory() -> dict[str, dict[str, Any]]:
    print("Checking forensic tool availability", flush=True)
    inventory: dict[str, dict[str, Any]] = {}
    bin_dir = Path(sys.executable).parent
    for name in TOOLS:
        found = shutil.which(name)
        if found is None and (bin_dir / name).is_file():
            found = str(bin_dir / name)
        if found is None:
            print(f"MISSING {name}", flush=True)
            inventory[name] = {
                "available": False,
                "path": None,
                "version": None,
                "version_argv": [name, "--version"],
                "version_exit_code": None,
            }
            continue
        argv = [found, "--version"]
        result = sh(" ".join(q(value) for value in argv), show=False)
        if result.returncode:
            fallback_argv = [found, "-V"]
            fallback = sh(" ".join(q(value) for value in fallback_argv), show=False)
            if fallback.returncode == 0:
                argv = fallback_argv
                result = fallback
        version = "\n".join(
            value for value in (result.stdout.strip(), result.stderr.strip()) if value
        )
        print(f"FOUND {name}: {found}", flush=True)
        inventory[name] = {
            "available": True,
            "path": found,
            "version": version,
            "version_argv": argv,
            "version_exit_code": result.returncode,
        }
    return inventory


def initial_record(run_id: str) -> dict[str, Any]:
    products = {
        name: {"stage": "disk", "state": "not_attempted"}
        for name in DISK_PRODUCTS
    }
    products.update(
        {
            f"{name}.json": {"stage": "ram", "state": "not_attempted"}
            for name, _ in RAM_PLUGINS
        }
    )
    products.update(
        {name: {"stage": "timeline", "state": "not_attempted"} for name in TIMELINE_PRODUCTS}
    )
    return {
        "run_id": run_id,
        "created_at": now(),
        "updated_at": now(),
        "evidence": {},
        "tools": {},
        "products": products,
        "stages": {},
    }


def command_product(
    record: dict[str, Any],
    manifest_path: Path,
    run_root: Path,
    name: str,
    stage: str,
    argv: list[str],
    output: Path,
    *,
    binary: bool = False,
    json_output: bool = False,
    require_output: bool = True,
) -> dict[str, Any]:
    started = now()
    command = " ".join(q(value) for value in argv)
    print(f"START {name}", flush=True)
    print(f"  {command}", flush=True)
    result = sh(
        command,
        label=output.name,
        out_dir=output.parent,
        binary=binary,
        show=False,
    )
    size = output.stat().st_size if output.exists() else 0
    state = "ok"
    detail = None
    if result.returncode != 0:
        state = "failed"
        detail = "command returned a non-zero exit code"
    elif require_output and size == 0:
        state = "partial"
        detail = "command succeeded but produced no output"
    elif json_output:
        try:
            json.loads(output.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            state = "partial"
            detail = f"command output is not valid JSON: {error}"

    product = {
        "stage": stage,
        "state": state,
        "path": str(output.relative_to(run_root)),
        "argv": argv,
        "started_at": started,
        "ended_at": now(),
        "exit_code": result.returncode,
        "bytes": size,
    }
    stderr_path = output.parent / f"{output.name}.stderr.txt"
    if stderr_path.exists():
        product["stderr_path"] = str(stderr_path.relative_to(run_root))
    if detail:
        product["detail"] = detail
    record["products"][name] = product
    record["updated_at"] = now()
    save(record, manifest_path)
    print(f"END   {name}: {state} (exit {result.returncode}, {size} bytes)", flush=True)
    return product


def unavailable_product(
    record: dict[str, Any],
    manifest_path: Path,
    name: str,
    stage: str,
    argv: list[str],
    detail: str,
) -> None:
    record["products"][name] = {
        "stage": stage,
        "state": "failed",
        "argv": argv,
        "started_at": now(),
        "ended_at": now(),
        "exit_code": None,
        "bytes": 0,
        "detail": detail,
    }
    record["updated_at"] = now()
    save(record, manifest_path)
    print(f"END   {name}: failed ({detail})", flush=True)


def hash_disk(record: dict[str, Any], manifest_path: Path, case: Any) -> None:
    if "disk" in record["evidence"]:
        print("Disk hashes already recorded", flush=True)
        return
    hashes: list[dict[str, str]] = []
    for segment in case.disk_segments:
        print(f"Hashing disk segment {segment.name}", flush=True)
        hashes.append(
            {
                "path": str(segment.relative_to(case.run_root)),
                "sha256": sha256_file(segment),
            }
        )
    record["evidence"]["disk"] = {
        "hash_scope": "complete bytes of each acquisition-recorded EWF segment",
        "segments": hashes,
    }
    record["updated_at"] = now()
    save(record, manifest_path)


def hash_memory(record: dict[str, Any], manifest_path: Path, case: Any) -> None:
    if "memory" in record["evidence"]:
        print("Memory hash already recorded", flush=True)
        return
    print(f"Hashing memory image {case.memory_image.name}", flush=True)
    record["evidence"]["memory"] = {
        "hash_scope": "complete bytes of the acquisition-recorded memory image",
        "path": str(case.memory_image.relative_to(case.run_root)),
        "sha256": sha256_file(case.memory_image),
    }
    record["updated_at"] = now()
    save(record, manifest_path)


def disk_stage(
    record: dict[str, Any],
    manifest_path: Path,
    case: Any,
    raw_dir: Path,
    with_unallocated: bool,
) -> None:
    record["stages"]["disk"] = {"started_at": now(), "state": "running"}
    save(record, manifest_path)
    hash_disk(record, manifest_path, case)
    tools = record["tools"]
    image = str(case.disk_image)
    first_segment = str(case.disk_segments[0])

    disk_commands = (
        ("ewfinfo", [tools["ewfinfo"]["path"] or "ewfinfo", first_segment]),
        (
            "ewfverify",
            [tools["ewfverify"]["path"] or "ewfverify", "-d", "sha256", first_segment],
        ),
        ("mmls", [tools["mmls"]["path"] or "mmls", image]),
    )
    for name, argv in disk_commands:
        if not tools[name]["available"]:
            unavailable_product(
                record,
                manifest_path,
                name,
                "disk",
                argv,
                f"required tool {name} is unavailable",
            )
            continue
        command_product(
            record,
            manifest_path,
            case.run_root,
            name,
            "disk",
            argv,
            raw_dir / f"{name}.txt",
            require_output=name != "ewfverify",
        )

    offset: int | None = None
    if tools["mmls"]["available"] and tools["fsstat"]["available"]:
        print("Locating the unique Ext4 root filesystem", flush=True)
        try:
            offset, _, fs_type = root_fs(case.disk_image)
            print(f"Root filesystem: {fs_type} at sector {offset}", flush=True)
        except (ValueError, OSError, subprocess.CalledProcessError) as error:
            print(f"Root filesystem lookup failed: {error}", flush=True)

    mmls_path = raw_dir / "mmls.txt"
    if mmls_path.exists() and tools["fsstat"]["available"]:
        for line in mmls_path.read_text().splitlines():
            match = re.match(
                r"^\s*(\d+):\s+(\S+)\s+(\d+)\s+\d+\s+\d+\s+",
                line,
            )
            if match is None or match.group(2) in {"Meta", "-------"}:
                continue
            index = match.group(1)
            partition_offset = match.group(3)
            name = f"fsstat-{index}-offset-{partition_offset}"
            command_product(
                record,
                manifest_path,
                case.run_root,
                name,
                "disk",
                [tools["fsstat"]["path"], "-o", partition_offset, image],
                raw_dir / f"{name}.txt",
            )
            product = record["products"][name]
            if product["state"] == "failed" and product.get("exit_code") not in (None,):
                product["state"] = "not_applicable"
                product["detail"] = "partition contains no filesystem fsstat recognises"
                record["updated_at"] = now()
                save(record, manifest_path)

    if offset is None:
        for name, tool in (
            ("allocated.body", "fls"),
            ("unallocated.body", "ils"),
            ("unallocated.dd", "blkls"),
        ):
            if name == "unallocated.dd" and not with_unallocated:
                continue
            unavailable_product(
                record,
                manifest_path,
                name,
                "disk",
                [tools[tool]["path"] or tool],
                "root filesystem offset was not resolved",
            )
    else:
        extraction_commands = (
            (
                "allocated.body",
                "fls",
                [tools["fls"]["path"] or "fls", "-r", "-m", "/", "-o", str(offset), image],
            ),
            (
                "unallocated.body",
                "ils",
                [tools["ils"]["path"] or "ils", "-m", "-o", str(offset), image],
            ),
        )
        for name, tool, argv in extraction_commands:
            if not tools[tool]["available"]:
                unavailable_product(
                    record,
                    manifest_path,
                    name,
                    "disk",
                    argv,
                    f"required tool {tool} is unavailable",
                )
                continue
            command_product(
                record,
                manifest_path,
                case.run_root,
                name,
                "disk",
                argv,
                raw_dir / name,
                binary=True,
            )

        if with_unallocated:
            argv = [
                tools["blkls"]["path"] or "blkls",
                "-o",
                str(offset),
                image,
            ]
            if tools["blkls"]["available"]:
                command_product(
                    record,
                    manifest_path,
                    case.run_root,
                    "unallocated.dd",
                    "disk",
                    argv,
                    raw_dir / "unallocated.dd",
                    binary=True,
                )
            else:
                unavailable_product(
                    record,
                    manifest_path,
                    "unallocated.dd",
                    "disk",
                    argv,
                    "required tool blkls is unavailable",
                )
        else:
            record["products"]["unallocated.dd"] = {
                "stage": "disk",
                "state": "not_attempted",
                "argv": [
                    tools["blkls"]["path"] or "blkls",
                    "-o",
                    str(offset),
                    image,
                ],
                "exit_code": None,
                "detail": "requires --with-unallocated",
            }
            record["updated_at"] = now()
            save(record, manifest_path)

    states = [
        product["state"]
        for product in record["products"].values()
        if product.get("stage") == "disk"
        and (product.get("state") != "not_attempted" or with_unallocated)
    ]
    stage_state = (
        "ok" if all(state in {"ok", "not_applicable"} for state in states) else "partial"
    )
    if states and all(state == "failed" for state in states):
        stage_state = "failed"
    record["stages"]["disk"] = {
        "started_at": record["stages"]["disk"]["started_at"],
        "ended_at": now(),
        "state": stage_state,
        "with_unallocated": with_unallocated,
    }
    record["updated_at"] = now()
    save(record, manifest_path)


def ram_stage(
    record: dict[str, Any],
    manifest_path: Path,
    case: Any,
    raw_dir: Path,
    isf_dir: Path,
) -> None:
    record["stages"]["ram"] = {
        "started_at": now(),
        "state": "running",
        "isf_dir": str(isf_dir),
    }
    save(record, manifest_path)
    hash_memory(record, manifest_path, case)
    vol = record["tools"]["vol3"]["path"] or "vol3"
    isf_path = isf_dir / case.isf_path.name
    isf_available = isf_path.is_file()
    record["stages"]["ram"]["selected_isf"] = str(isf_path)
    save(record, manifest_path)

    for name, plugin in RAM_PLUGINS:
        product_name = f"{name}.json"
        argv = [
            vol,
            "-f",
            str(case.memory_image),
            "-s",
            str(isf_dir),
            "-r",
            "json",
            plugin,
        ]
        if name != "banners" and not isf_available:
            unavailable_product(
                record,
                manifest_path,
                product_name,
                "ram",
                argv,
                f"selected ISF is absent: {isf_path}",
            )
            continue
        if not record["tools"]["vol3"]["available"]:
            unavailable_product(
                record,
                manifest_path,
                product_name,
                "ram",
                argv,
                "required tool vol3 is unavailable",
            )
            continue
        command_product(
            record,
            manifest_path,
            case.run_root,
            product_name,
            "ram",
            argv,
            raw_dir / product_name,
            binary=True,
            json_output=True,
        )

    states = [record["products"][f"{name}.json"]["state"] for name, _ in RAM_PLUGINS]
    stage_state = "ok" if all(state == "ok" for state in states) else "partial"
    if states and all(state == "failed" for state in states):
        stage_state = "failed"
    record["stages"]["ram"] = {
        **record["stages"]["ram"],
        "ended_at": now(),
        "state": stage_state,
    }
    record["updated_at"] = now()
    save(record, manifest_path)


def plaso_product(
    record: dict[str, Any],
    manifest_path: Path,
    run_root: Path,
    name: str,
    argv: list[str],
    written: Path,
    output: Path,
    transcript: Path,
) -> dict[str, Any]:
    """Run a Plaso CLI that writes its own file; keep its stdout and stderr apart."""
    started = now()
    command = " ".join(q(value) for value in argv)
    print(f"START {name}", flush=True)
    print(f"  {command}", flush=True)
    result = sh(command, label=transcript.name, out_dir=transcript.parent, show=False)
    if written != output and written.exists():
        shutil.move(written, output)
    size = output.stat().st_size if output.exists() else 0
    state = "ok"
    detail = None
    if result.returncode != 0:
        state = "failed"
        detail = "command returned a non-zero exit code"
    elif not output.exists():
        state = "failed"
        detail = "command succeeded but wrote no output file"

    product = {
        "stage": "timeline",
        "state": state,
        "path": str(output.relative_to(run_root)),
        "argv": argv,
        "started_at": started,
        "ended_at": now(),
        "exit_code": result.returncode,
        "bytes": size,
        "stdout_path": str(transcript.relative_to(run_root)),
    }
    stderr_path = transcript.parent / f"{transcript.name}.stderr.txt"
    if stderr_path.exists():
        product["stderr_path"] = str(stderr_path.relative_to(run_root))
    if detail:
        product["detail"] = detail
    record["products"][name] = product
    record["updated_at"] = now()
    save(record, manifest_path)
    print(f"END   {name}: {state} (exit {result.returncode}, {size} bytes)", flush=True)
    return product


def pinfo_counts(text: str) -> tuple[int, dict[str, int], dict[str, int]]:
    """Count sessions, events per parser and stored warnings in `pinfo -v` text."""
    sessions = len(re.findall(r"^\*+ Session: \S+ \*+$", text, re.M))
    table = re.search(
        r"^\*+ Events generated per parser \*+\n[^\n]*\n-+\n(.*?)\n-+$", text, re.M | re.S
    )
    rows = re.findall(r"^\s*(\S+) : (\d+)$", table.group(1), re.M) if table else []
    warnings: dict[str, int] = {}
    for kind in re.findall(r"^\*+ (\w+) warning: \d+ \*+$", text, re.M):
        warnings[kind] = warnings.get(kind, 0) + 1
    return sessions, {parser: int(count) for parser, count in rows}, warnings


def timeline_stage(
    record: dict[str, Any],
    manifest_path: Path,
    case: Any,
    raw_dir: Path,
) -> None:
    log_dir = case.output / "prepare-timeline"
    record["stages"]["timeline"] = {
        "started_at": now(),
        "state": "running",
        "evidence": "disk",
        "log_dir": str(log_dir.relative_to(case.run_root)),
    }
    save(record, manifest_path)
    hash_disk(record, manifest_path, case)
    tools = record["tools"]
    store = raw_dir / "timeline.plaso"
    export = raw_dir / "timeline.jsonl"
    pinfo = raw_dir / "pinfo.txt"

    # log2timeline appends a session to an existing store and psort refuses an
    # existing output file, so this stage's previous products and logs go first.
    for path in (store, export, pinfo, raw_dir / "pinfo.txt.stderr.txt"):
        path.unlink(missing_ok=True)
    shutil.rmtree(log_dir, ignore_errors=True)
    log_dir.mkdir(parents=True)

    # log2timeline keeps its task storage beside --storage_file, so the store is
    # written in scratch outside the case and moved in when extraction ends.
    with tempfile.TemporaryDirectory(prefix="prepare-timeline-") as scratch:
        scratch_store = Path(scratch) / store.name
        argv = [
            tools["log2timeline"]["path"] or "log2timeline",
            "--unattended",
            "--status_view", "none",
            "--logfile", str(log_dir / "log2timeline.log"),
            "--temporary_directory", scratch,
            "--partitions", "all",
            "--parsers", "linux",
            "--storage_file", str(scratch_store),
            str(case.disk_image),
        ]
        if tools["log2timeline"]["available"]:
            plaso_product(
                record,
                manifest_path,
                case.run_root,
                "timeline.plaso",
                argv,
                scratch_store,
                store,
                log_dir / "log2timeline.txt",
            )
        else:
            unavailable_product(
                record,
                manifest_path,
                "timeline.plaso",
                "timeline",
                argv,
                "required tool log2timeline is unavailable",
            )

    # The export keeps every stored event, filestat included. filestat and the
    # TSK bodyfile render the same filesystem metadata, but the bodyfile lacks
    # some Plaso fields, sub-second times and the non-root partitions, so any
    # filtering happens visibly in the notebook, not here.
    psort_argv = [
        tools["psort"]["path"] or "psort",
        "--unattended",
        "--status_view", "none",
        "--logfile", str(log_dir / "psort.log"),
        "-a",
        "-o", "json_line",
        "-w", str(export),
        str(store),
    ]
    pinfo_argv = [
        tools["pinfo"]["path"] or "pinfo",
        "-v",
        "--logfile", str(log_dir / "pinfo.log"),
        str(store),
    ]
    for name, tool, argv in (
        ("timeline.jsonl", "psort", psort_argv),
        ("pinfo", "pinfo", pinfo_argv),
    ):
        if record["products"]["timeline.plaso"]["state"] == "failed":
            unavailable_product(
                record, manifest_path, name, "timeline", argv, "no Plaso store was produced"
            )
        elif not tools[tool]["available"]:
            unavailable_product(
                record,
                manifest_path,
                name,
                "timeline",
                argv,
                f"required tool {tool} is unavailable",
            )
        elif name == "pinfo":
            command_product(
                record, manifest_path, case.run_root, name, "timeline", argv, pinfo
            )
        else:
            plaso_product(
                record,
                manifest_path,
                case.run_root,
                name,
                argv,
                export,
                export,
                log_dir / "psort.txt",
            )

    # Exit zero does not establish complete extraction: check the transcript and
    # what pinfo reports about the store before calling it ok.
    extraction = record["products"]["timeline.plaso"]
    problems = []
    if record["products"]["pinfo"]["state"] == "ok":
        sessions, parsers, warnings = pinfo_counts(pinfo.read_text())
        extraction.update(sessions=sessions, events_by_parser=parsers, warnings=warnings)
        if sessions != 1:
            problems.append(f"store holds {sessions} sessions")
        if warnings:
            problems.append(f"pinfo reports stored warnings {warnings}")
    else:
        problems.append("pinfo did not describe the store")
    if extraction["state"] == "ok":
        transcript = (case.run_root / extraction["stdout_path"]).read_text()
        if "Processing completed.\n" not in transcript:
            problems.append("log2timeline did not report clean completion")
        if problems:
            extraction["state"] = "partial"
            extraction["detail"] = "; ".join(problems)

    jsonl = record["products"]["timeline.jsonl"]
    if jsonl["state"] == "ok":
        try:
            jsonl["events"] = len(load_plaso(export))
        except ValueError as error:
            jsonl["state"] = "failed"
            jsonl["detail"] = f"load_plaso could not read the export: {error}"
    if jsonl["state"] == "ok" and "events_by_parser" in extraction:
        expected = extraction["events_by_parser"].get("Total", 0)
        if jsonl["events"] != expected:
            jsonl["state"] = "partial"
            jsonl["detail"] = f"read {jsonl['events']} events, pinfo implies {expected}"

    states = [record["products"][name]["state"] for name in TIMELINE_PRODUCTS]
    stage_state = "ok" if all(state == "ok" for state in states) else "partial"
    if all(state == "failed" for state in states):
        stage_state = "failed"
    record["stages"]["timeline"] = {
        **record["stages"]["timeline"],
        "ended_at": now(),
        "state": stage_state,
    }
    record["updated_at"] = now()
    save(record, manifest_path)


def stage_exists(
    record: dict[str, Any], stage: str, with_unallocated: bool, run_root: Path
) -> bool:
    if stage == "timeline":
        return all(
            record["products"].get(name, {}).get("state") in {"ok", "partial"}
            and (run_root / record["products"][name]["path"]).is_file()
            for name in TIMELINE_PRODUCTS
        )
    if stage == "disk":
        names = list(DISK_PRODUCTS[:5])
        if with_unallocated:
            names.append("unallocated.dd")
    else:
        names = [f"{name}.json" for name, _ in RAM_PLUGINS]
    return all(record["products"].get(name, {}).get("state", "not_attempted") != "not_attempted"
               for name in names)


def print_summary(record: dict[str, Any], stage: str, manifest_path: Path) -> None:
    print(f"Existing prepared {stage} bundle: {manifest_path}")
    for name, product in record["products"].items():
        if product.get("stage") == stage:
            print(f"  {name}: {product['state']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare bounded disk, RAM and timeline products"
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--stage", required=True, choices=("disk", "ram", "timeline", "all")
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--with-unallocated", action="store_true")
    parser.add_argument("--isf-dir", type=Path)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    case = load_case(project_root, args.run_id)
    raw_dir = case.prepared / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = case.prepared / "prepare.json"
    if manifest_path.exists():
        record = json.loads(manifest_path.read_text())
        if record["run_id"] != args.run_id:
            raise ValueError("existing prepare.json belongs to a different run")
    else:
        record = initial_record(args.run_id)

    record["tools"] = tool_inventory()
    record["updated_at"] = now()
    save(record, manifest_path)

    stages = ("disk", "ram", "timeline") if args.stage == "all" else (args.stage,)
    for stage in stages:
        if not args.force and stage_exists(
            record, stage, args.with_unallocated, case.run_root
        ):
            print_summary(record, stage, manifest_path)
            continue
        if stage == "disk":
            disk_stage(
                record,
                manifest_path,
                case,
                raw_dir,
                args.with_unallocated,
            )
        elif stage == "timeline":
            timeline_stage(record, manifest_path, case, raw_dir)
        else:
            selected_isf_dir = (
                args.isf_dir.expanduser().resolve()
                if args.isf_dir is not None
                else case.isf_path.parent
            )
            ram_stage(record, manifest_path, case, raw_dir, selected_isf_dir)


if __name__ == "__main__":
    main()
