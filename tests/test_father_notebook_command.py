"""Focused checks for the Father notebook command wrapper."""

import subprocess

import pytest

from investigations.father.investigation_utils import run_command


def test_inline_shell_command_and_optional_output(tmp_path, monkeypatch, capfd):
    monkeypatch.setenv("DISK_IMAGE", "/evidence/path with spaces.E01")
    result = run_command(
        'printf "%s\\n%s\\n" "$DISK_IMAGE" "$(( $(printf 4) - 2 ))"',
        label="command.txt",
        out_dir=tmp_path / "new-output-dir",
    )

    assert result.stdout == "/evidence/path with spaces.E01\n2\n"
    assert (tmp_path / "new-output-dir/command.txt").read_text() == result.stdout
    assert not (tmp_path / "new-output-dir/command.txt.stderr.txt").exists()
    assert capfd.readouterr().out.endswith(result.stdout)


def test_live_output_is_printed_and_returned(tmp_path, capfd):
    result = run_command(
        "printf output; printf error >&2",
        label="output.txt",
        out_dir=tmp_path,
    )
    captured = capfd.readouterr()

    assert captured.out.endswith("output")
    assert captured.err == "error"
    assert result.stdout == "output"
    assert result.stderr == "error"
    assert (tmp_path / "output.txt").read_text() == "output"
    assert (tmp_path / "output.txt.stderr.txt").read_text() == "error"


def test_nonzero_exit_is_returned_unless_check_is_requested(tmp_path):
    result = run_command("printf failure >&2; exit 7", label="failed.txt", out_dir=tmp_path)
    assert result.returncode == 7
    assert result.stderr == "failure"

    with pytest.raises(subprocess.CalledProcessError):
        run_command("exit 7", label="failed.txt", out_dir=tmp_path, check=True)
