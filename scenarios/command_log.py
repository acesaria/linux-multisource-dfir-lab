"""Scenario claims and append-only command records with stable, run-local IDs."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypedDict

from paramiko import SSHException

from orchestrator.core.provenance import utc_now
from orchestrator.core.ssh_client import SSHTerminal, TerminalCommandResult


class ScenarioClaim(TypedDict):
    id: str
    statement: str
    basis: list[str]
    basis_type: Literal[
        "successful_command",
        "successful_commands",
        "successful_execution_and_scenario_fact",
    ]
    validation_limit: str


@dataclass
class CommandLog:
    terminal: SSHTerminal
    path: Path
    _ids: set[str] = field(default_factory=set, init=False, repr=False)

    def run(
        self,
        record_id: str,
        command: str,
        *,
        timeout: int | None = 180,
        expect_failure: bool = False,
    ) -> TerminalCommandResult:
        """Execute one command; retain its outcome without embedding output."""
        self._reserve_id(record_id)
        try:
            result = self.terminal.run(command, timeout=timeout)
        except (OSError, RuntimeError, ValueError, SSHException) as exc:
            self._append(
                record_id,
                {
                    "status": "failure",
                    "command": command,
                    "error": str(exc),
                },
            )
            raise

        if expect_failure:
            status = "tolerated_failure" if result.exit_code != 0 else "failure"
        else:
            status = "success" if result.exit_code == 0 else "failure"
        self._append(
            record_id,
            {
                "status": status,
                "command": command,
                "exit_code": result.exit_code,
            },
        )
        if status == "failure":
            raise RuntimeError(
                f"unexpected command result ({result.exit_code}): {command}"
            )
        return result

    def note(self, record_id: str, *, error: str | None = None) -> None:
        """Record a host operation or the outcome of a scenario validation."""
        self._reserve_id(record_id)
        row: dict[str, object] = {
            "status": "failure" if error is not None else "success",
        }
        if error is not None:
            row["error"] = error
        self._append(record_id, row)

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        self.note(f"phase_{name}_start")
        try:
            yield
        finally:
            self.note(f"phase_{name}_end")

    def _reserve_id(self, record_id: str) -> None:
        if not record_id or record_id in self._ids:
            raise ValueError(f"empty or duplicate command-log ID: {record_id!r}")
        self._ids.add(record_id)

    def _append(self, record_id: str, row: dict[str, object]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "id": record_id,
                        "recorded_at": utc_now(),
                        **row,
                    }
                )
                + "\n"
            )
