# AGENTS.md

This repository is a master's thesis lab. It provisions VMs, runs four attack scenarios on three
distributions, acquires RAM then disk, and supports an analyst-led forensic examination of each run.
One researcher maintains it. Small and boring beats clever. The method is in `docs/METHOD.md`.

## Layout
- `cli.py`, `orchestrator/`, `infra/`, `scenarios/`: executor. Produces `shared/experiments/<run_id>/`.
- `examination/`: Bash scripts that examine one run. `lib.sh` defines `step`; every command goes through it.
- `shared/experiments/<run_id>/dumps/`: evidence. Not in git.
- `shared/experiments/<run_id>/investigation/`: `run.env`, `outputs/`, `scores.tsv`, `notes.md`.

Scenario keys for `cli.py run --scenario`: `user_ldpreload_father`, `user_procinj_ptracefa`,
`kernel_lkm_diamorphine`, `kernel_ebpf_badbpf`, and `interactive_shell` (benign session, used as the control run).

## Rules
1. Never write to, move, or delete anything under any `dumps/` directory.
2. Never edit `scores.tsv` or `notes.md`. Scoring and interpretation belong to the analyst.
3. Never type an offset, inode, PID, address or run_id into a script. Derive it from the evidence or the manifest.
4. Do not delete or move files unless the task names them.
5. No new dependency, framework, notebook, config layer or abstraction. No JSON conversion of tool output.
6. Change only what the task names. If something else looks wrong, report it at the end; do not fix it.
7. A command that fails is information. Show its real output. Do not hide, retry around, or stub a failure.
8. One task, one commit, with a message that says what changed and why.

## How to check your work
- Scripts: `bash -n <file>`, then run on the run directory named in the task and show the printed step lines.
- Examination: `python3 examination/metrics.py shared/experiments` must not report PROBLEMS caused by your change.
- Executor: `.venv/bin/python -m pytest tests -q`, then run the scenario named in the task through `cli.py`
  (2 to 3 minutes) and show the manifest `status`.

## Report format
End every task with: what changed (files), what you ran and its result, what you did not do, open questions.
