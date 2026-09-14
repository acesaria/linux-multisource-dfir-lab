"""Explicit scenario runner for one interactive SSH terminal."""

from __future__ import annotations

from pathlib import Path

from orchestrator.core.ssh_client import SSHClient, TerminalCommandResult
from scenarios.command_log import CommandLog, ScenarioClaim


SCENARIO_ID = "interactive_shell"
SCENARIO_DIR = "/tmp/forensic-lab/interactive_shell"
ARTIFACT_FILE = f"{SCENARIO_DIR}/artifact.txt"
EXPECTED_FAILURE = "interactive_shell_command_that_does_not_exist"
COMMANDS = (
    'echo "Bash PID: $BASHPID"',
    'echo "Normal terminal output"',
    EXPECTED_FAILURE,
    'echo "Bash PID after failure: $BASHPID"',
    f"mkdir -p {SCENARIO_DIR}",
    f'echo "Interactive shell artifact" > {ARTIFACT_FILE}',
    f"cat {ARTIFACT_FILE}",
)


def get_scenario_claims() -> list[ScenarioClaim]:
    """Declare expected effects from successful scenario execution."""
    return [
        {
            "id": "shell_continued_after_failure",
            "statement": "The shell executed a subsequent command after the expected command failure.",
            "basis": [
                "command_log.jsonl#expected_failure",
                "command_log.jsonl#continued_shell_pid",
            ],
            "basis_type": "successful_commands",
            "validation_limit": "The expected failure is intentional, not a failed scenario.",
        },
        {
            "id": "artifact_written",
            "statement": "The interactive shell wrote its artifact file.",
            "basis": ["command_log.jsonl#write_artifact"],
            "basis_type": "successful_command",
            "validation_limit": "Successful writing does not establish persistence until acquisition.",
        },
        {
            "id": "artifact_readback_validated",
            "statement": "Artifact readback returned the expected text.",
            "basis": [
                "command_log.jsonl#read_artifact",
                "command_log.jsonl#validate_artifact",
            ],
            "basis_type": "successful_commands",
            "validation_limit": "The existing readback checks content at that moment, not its later state.",
        },
    ]


def run_interactive_shell(
    ssh: SSHClient,
    transcript_path: Path,
    *,
    command_log_path: Path,
) -> list[TerminalCommandResult]:
    results: list[TerminalCommandResult] = []
    terminal = ssh.open_terminal()
    log = CommandLog(terminal, command_log_path)
    try:
        with terminal:
            for record_id, command in zip(
                (
                    "initial_shell_pid",
                    "normal_output",
                    "expected_failure",
                    "continued_shell_pid",
                    "create_directory",
                    "write_artifact",
                    "read_artifact",
                ),
                COMMANDS,
                strict=True,
            ):
                result = log.run(
                    record_id,
                    command,
                    expect_failure=command == EXPECTED_FAILURE,
                )
                results.append(result)
            if results[-1].combined_output.strip() != "Interactive shell artifact":
                raise RuntimeError("Interactive shell artifact readback failed")
            log.note("validate_artifact")
    finally:
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        transcript_path.write_text(terminal.transcript, encoding="utf-8")
    return results
