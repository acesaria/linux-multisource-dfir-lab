import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from orchestrator.core.orchestrator import ForensicOrchestrator, _validate_claim_refs
from orchestrator.core.paths import ProjectPaths
from orchestrator.core.provenance import command_output
from orchestrator.forensics import dumper as acquisition
from orchestrator.forensics.dumper import Dumper, acquisition_record
from scenarios.command_log import CommandLog, ScenarioClaim


@pytest.fixture
def dumper(tmp_path: Path) -> Dumper:
    return Dumper(
        ProjectPaths(
            repo_root=tmp_path,
            shared_dir=tmp_path / "shared",
            state_dir=tmp_path / "state",
            ssh_key=tmp_path / "ssh_key",
            ssh_pub_key=tmp_path / "ssh_key.pub",
        )
    )


@pytest.fixture
def acquisition_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    state = SimpleNamespace(fail=None, commands=[], empty=False, missing_digest=False)
    monkeypatch.setattr(acquisition, "_RAW_STAGING_DIR", tmp_path)

    def run(command, **_kwargs):
        if command[-1] in ("--version", "-V"):
            return subprocess.CompletedProcess(
                command, 0, f"{command[0]} test-version\n", ""
            )
        if command[1] == "info":
            return subprocess.CompletedProcess(command, 0, '{"virtual-size": 4096}', "")
        state.commands.append(command)
        tool = command[0]
        if tool == "virsh":
            dest = Path(command[3])
            assert dest.exists() and dest.stat().st_mode & 0o777 == 0o600
            if not state.empty:
                dest.write_bytes(b"memory image")
        elif tool == "qemu-img":
            Path(command[-1]).write_bytes(b"raw disk")
        elif tool == "ewfacquire":
            prefix = command[command.index("-t") + 1]
            Path(prefix + ".E01").write_bytes(b"EWF segment one")
            Path(prefix + ".E02").write_bytes(b"EWF segment two")
        code = 3 if state.fail == tool else 0
        output = "tool progress\n"
        if tool == "ewfverify" and not state.missing_digest:
            output += f"SHA256 hash calculated over data:\t{'c' * 64}\n"
        return subprocess.CompletedProcess(command, code, output, "tool diagnostic\n")

    monkeypatch.setattr(acquisition.subprocess, "run", run)
    return state


def test_ram_timestamps_bracket_capture_not_version_probe_or_hash(
    tmp_path: Path,
    dumper: Dumper,
    monkeypatch: pytest.MonkeyPatch,
):
    dest = tmp_path / "dumps" / "memory" / "mem.raw"
    record = acquisition_record(dest, "virsh dump --memory-only")
    events = []
    stamps = iter(("2026-09-12T00:00:00.123456Z", "2026-09-12T00:00:01.654321Z"))
    clock = iter((10.0, 11.5))

    def timestamp():
        stamp = next(stamps)
        events.append(stamp)
        return stamp

    def run(command, **_kwargs):
        if command == ["virsh", "--version"]:
            events.append("version")
            return subprocess.CompletedProcess(command, 0, "10.0.0\n", "")
        events.append("capture")
        assert dest.exists() and dest.stat().st_mode & 0o777 == 0o600
        dest.write_bytes(b"memory image")
        return subprocess.CompletedProcess(command, 0, "progress", "diagnostic")

    def digest(path):
        events.append("hash")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    monkeypatch.setattr(acquisition, "utc_now", timestamp)
    monkeypatch.setattr(acquisition.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(acquisition.subprocess, "run", run)
    monkeypatch.setattr(acquisition, "file_sha256", digest)
    log = io.StringIO()
    dumper.acquire_memory("lab-vm", dest, record, log)
    assert events == [
        "version",
        record["started_at"],
        "capture",
        record["ended_at"],
        "hash",
    ]
    assert record["duration_seconds"] == 1.5
    assert record["sha256"] == hashlib.sha256(b"memory image").hexdigest()
    assert record["tool_version"] == {"virsh": "10.0.0"}
    assert record["exit_status"] == 0
    assert "progress" in log.getvalue() and "diagnostic" in log.getvalue()
    assert not (dest.parent / "hashes.txt").exists()
    assert not list(dest.parent.glob("*_status.json"))
    assert not {"stdout", "stderr", "verified"} & record.keys()


@pytest.mark.parametrize("failure", ["exit", "empty", "hash", "launch"])
def test_memory_failure_retains_capture_bounds(
    tmp_path: Path,
    dumper: Dumper,
    acquisition_tools,
    monkeypatch,
    failure: str,
):
    dest = tmp_path / "dumps" / "memory" / "mem.raw"
    record = acquisition_record(dest, "virsh dump --memory-only")
    if failure == "exit":
        acquisition_tools.fail = "virsh"
    elif failure == "empty":
        acquisition_tools.empty = True
    elif failure == "hash":

        def unreadable(_path):
            raise PermissionError("cannot read captured file")

        monkeypatch.setattr(acquisition, "file_sha256", unreadable)
    else:

        def missing(command, **_kwargs):
            raise FileNotFoundError(command[0])

        monkeypatch.setattr(acquisition.subprocess, "run", missing)
    with pytest.raises((RuntimeError, OSError)):
        dumper.acquire_memory("lab-vm", dest, record, io.StringIO())
    assert record["started_at"] and record["ended_at"]
    assert record["duration_seconds"] >= 0
    assert record["sha256"] is None
    assert record["exit_status"] == (
        None if failure == "launch" else 3 if failure == "exit" else 0
    )


def test_existing_memory_is_not_replaced(
    tmp_path: Path, dumper: Dumper, acquisition_tools
):
    dest = tmp_path / "dumps" / "memory" / "mem.raw"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"accepted evidence")
    with pytest.raises(FileExistsError):
        dumper.acquire_memory(
            "lab-vm", dest, acquisition_record(dest, "virsh"), io.StringIO()
        )
    assert dest.read_bytes() == b"accepted evidence"
    assert not acquisition_tools.commands


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "qemu-img",
        "ewfacquire",
        "ewfverify",
        "missing_digest",
        "shutdown",
        "cleanup",
        "virsh",
    ],
)
def test_acquisition_preserves_partial_records_and_lifecycle(
    tmp_path: Path,
    dumper: Dumper,
    acquisition_tools,
    failure: str | None,
):
    acquisition_tools.fail = failure
    acquisition_tools.missing_digest = failure == "missing_digest"
    events = []

    def cleanup():
        events.append("cleanup")
        assert [cmd[0] for cmd in acquisition_tools.commands] == ["virsh"]
        if failure == "cleanup":
            raise RuntimeError("cleanup failed")

    def shutdown(_vm):
        events.append("shutdown")
        assert events == ["cleanup", "shutdown"]
        if failure == "shutdown":
            raise RuntimeError("shutdown failed")

    orchestrator = object.__new__(ForensicOrchestrator)
    orchestrator.dumper = dumper
    orchestrator.vm_manager = SimpleNamespace(
        get_disk_path=lambda _vm: tmp_path / "source.qcow2",
        shutdown_vm=shutdown,
    )
    if failure:
        with pytest.raises(RuntimeError):
            orchestrator._run_acquisition("lab-vm", "test-run", before_shutdown=cleanup)
    else:
        manifest_path, memory_path, disk_path = orchestrator._run_acquisition(
            "lab-vm",
            "test-run",
            before_shutdown=cleanup,
        )
        assert Path(manifest_path).is_file()
        assert memory_path.is_file() and disk_path.is_file()
        assert disk_path.is_absolute()

    root = dumper.run_dir("test-run")
    serialized = (root / "acquisition.json").read_text()
    metadata = json.loads(serialized)
    memory, disk = metadata["memory"], metadata["disk"]
    assert set(metadata) == {"memory", "disk"}
    assert serialized.startswith('{\n  "memory": {') and serialized.endswith("\n")
    assert memory["started_at"] <= memory["ended_at"]
    assert re.fullmatch(r".*\.\d{6}Z", memory["started_at"])
    assert memory["sha256"] == (
        None if failure == "virsh" else hashlib.sha256(b"memory image").hexdigest()
    )
    if failure in ("virsh", "cleanup", "shutdown"):
        assert disk is None
    else:
        assert events == ["cleanup", "shutdown"]
        assert disk["hash_scope"] == "logical_disk"
        assert disk["size_bytes"] == 4096
        assert disk["duration_seconds"] >= 0
        if failure is None:
            assert disk["sha256"] == "c" * 64
            assert disk["segments"] == [
                "disk/evidence_disk.E01",
                "disk/evidence_disk.E02",
            ]
            assert (
                disk["sha256"]
                != hashlib.sha256((root / disk["path"]).read_bytes()).hexdigest()
            )
            assert disk["exit_status"] == 0
            assert "error" not in disk
        else:
            assert disk["sha256"] is None and disk["error"]
            assert disk["exit_status"] == (0 if failure == "missing_digest" else 3)
    for forbidden in (
        "stdout",
        "stderr",
        "commands",
        "segment_metadata",
        "calculated_sha256",
        "verification",
        "timestamp",
        "acquisition_seconds",
        "md5",
    ):
        assert f'"{forbidden}"' not in serialized
    assert "tool progress" not in serialized
    assert "tool progress" in (root / "acquisition.log").read_text()
    assert not list(root.rglob("hashes.txt"))
    assert not list(root.rglob("*_status.json"))
    assert not list(tmp_path.glob("dfir-disk-*"))


def test_command_ids_are_unique_before_execution(tmp_path: Path):
    terminal = MagicMock()
    terminal.run.return_value = SimpleNamespace(exit_code=0)
    log = CommandLog(terminal, tmp_path / "commands.jsonl")
    log.run("first", "echo ok")
    with pytest.raises(ValueError, match="duplicate"):
        log.run("first", "must not execute")
    terminal.run.assert_called_once()


@pytest.mark.parametrize(
    "failure",
    [
        "duplicate", "missing", "missing_command", "failed", "no_refs",
        "missing_fact", "null_fact",
    ],
)
def test_invalid_claims_are_rejected(tmp_path: Path, failure: str):
    (tmp_path / "command_log.jsonl").write_text(
        json.dumps(
            {
                "id": "action",
                "status": "failure" if failure == "failed" else "success",
            }
        )
        + "\n"
    )
    claim: ScenarioClaim = {
        "id": "claim",
        "statement": "Action completed",
        "basis": ["command_log.jsonl#action"],
        "basis_type": "successful_command",
        "validation_limit": "Command completion does not establish the final state.",
    }
    facts: dict[str, object] = {}
    if failure == "missing":
        claim["basis"] = ["inputs/missing"]
    elif failure == "missing_command":
        claim["basis"] = ["command_log.jsonl#missing"]
    elif failure == "no_refs":
        claim["basis"] = []
    elif failure in ("missing_fact", "null_fact"):
        claim["basis"] = ["manifest.json#scenario_facts.backdoor_connection"]
        claim["basis_type"] = "successful_execution_and_scenario_fact"
        if failure == "null_fact":
            facts["backdoor_connection"] = None
    with pytest.raises(ValueError):
        _validate_claim_refs(
            [claim, claim] if failure == "duplicate" else [claim], tmp_path, facts
        )


def test_provenance_output_failures_remain_distinguishable(monkeypatch):
    monkeypatch.setattr(
        "orchestrator.core.provenance.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            ["probe"], 2, "version stdout", "version stderr"
        ),
    )
    assert (
        command_output(["probe"], allow_nonzero=True)
        == "version stdout\nversion stderr"
    )


def test_qemu_virtual_size_requires_positive_integer(monkeypatch):
    monkeypatch.setattr(
        acquisition.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(
            command, 0, '{"format": "qcow2"}', "qemu diagnostic"
        ),
    )
    with pytest.raises(RuntimeError, match="positive integer virtual-size") as exc:
        Dumper._qemu_virtual_size(Path("evidence.qcow2"))
    assert "qemu diagnostic" in str(exc.value)
