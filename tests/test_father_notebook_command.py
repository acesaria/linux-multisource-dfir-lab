"""Draft reruns replace output; tool failures remain visible and inspectable."""

import shlex
import subprocess
import sys
from functools import partial

import pytest

from investigations.father.investigation_utils import get_rootfs_offset, run_command


@pytest.fixture
def examination(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "recovered").mkdir()
    return tmp_path


def test_text_rerun_replaces_complete_output(examination):
    run = partial(run_command, out_dir=examination / "data")
    # A quoted command string must preserve paths containing spaces.
    argument = examination / "path with spaces"
    script = "import os, sys; print(sys.argv[1]); print(os.environ['TZ']); print('x' * 5000); sys.stderr.write('warning')"
    command = shlex.join([sys.executable, "-c", script, str(argument)])
    first = run(command, "text.txt")
    assert str(argument) in first.stdout and "\nUTC\n" in first.stdout
    assert (examination / "data/text.txt").read_text() == first.stdout
    assert (examination / "data/text.txt.stderr.txt").read_text() == "warning"

    run([sys.executable, "-c", "print('latest')"], "text.txt")
    assert (examination / "data/text.txt").read_text() == "latest\n"
    assert not (examination / "data/text.txt.stderr.txt").exists()


def test_failure_retains_output_and_allows_retry(examination):
    run = partial(run_command, out_dir=examination / "data")
    with pytest.raises(subprocess.CalledProcessError) as failure:
        run([sys.executable, "-c",
             "import sys; print('partial'); sys.stderr.write('failure'); sys.exit(7)"],
            "failed.txt")
    assert failure.value.returncode == 7
    assert failure.value.stdout == "partial\n"
    assert failure.value.stderr == "failure"
    assert (examination / "data/failed.txt").read_text() == "partial\n"
    assert (examination / "data/failed.txt.stderr.txt").read_text() == "failure"

    run([sys.executable, "-c", "pass"], "failed.txt")
    assert (examination / "data/failed.txt").read_bytes() == b""
    assert not (examination / "data/failed.txt.stderr.txt").exists()


def test_binary_rerun_replaces_extracted_bytes(examination):
    run = partial(run_command, out_dir=examination / "data")
    for content in (b"\x00\xff\x01", b"\x02"):
        result = run([sys.executable, "-c",
                      f"import sys; sys.stdout.buffer.write({content!r})"],
                     "inode.bin", out_dir=examination / "recovered")
        assert result.stdout == content.decode(errors="replace")
        assert (examination / "recovered/inode.bin").read_bytes() == content
        assert not (examination / "recovered/inode.bin.stderr.txt").exists()

    # An override applies to that invocation; subsequent calls still default to data/.
    run([sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'\\x00\\xff')"], "default.bin")
    assert (examination / "data/default.bin").read_bytes() == b"\x00\xff"
    assert not (examination / "recovered/default.bin").exists()


def test_launch_error_does_not_leave_stale_success(examination):
    run = partial(run_command, out_dir=examination / "data")
    run([sys.executable, "-c", "print('previous success')"], "launch.txt")
    with pytest.raises(FileNotFoundError):
        run([str(examination / "missing-executable")], "launch.txt")
    assert (examination / "data/launch.txt").read_bytes() == b""
    assert not (examination / "data/launch.txt.stderr.txt").exists()
