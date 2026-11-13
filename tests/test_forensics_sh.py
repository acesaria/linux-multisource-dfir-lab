"""Focused checks for the shared command helper."""

import subprocess

import pytest

from investigations.common.forensics import sh as run_command


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


def test_findings_validation_rejects_duplicate_cell_and_unknown_status():
    """Allowlist 5: a repeated cell or a mistyped status must not reach the counts."""
    from investigations.common import forensics as fx

    rows = [{"claim_id": "c", "source": source, "status": "supported"} for source in fx.SOURCES]
    with pytest.raises(ValueError, match="duplicate"):
        fx.check_findings(rows + rows[:1], ["c"])
    with pytest.raises(ValueError, match="unknown status"):
        fx.check_findings([{**rows[0], "status": "likely"}, *rows[1:]], ["c"])


def test_support_rate_zero_denominator_is_not_calculable():
    """Allowlist 6: a source with no investigated claim has no rate, not a zero rate."""
    import pandas as pd

    from investigations.common import forensics as fx

    grid = pd.DataFrame({"disk": ["supported", "partial"],
                         "timeline": ["unsupported", "unsupported"],
                         "ram": ["not_examined", "not_examined"]})
    rates = fx.support_rates(grid)
    assert rates.loc["disk", "support_rate"] == "1/2"
    assert rates.loc["timeline", "support_rate"] == "0/2"
    assert rates.loc["ram", "support_rate"] == "not calculable"
