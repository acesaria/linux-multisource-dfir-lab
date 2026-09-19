# Investigation layer refactor — staged work order

## Context

Scenario: none (shared investigation infrastructure); stage: bounded code, then forensics.
Checkout: `/home/anto/linux-multisource-dfir-lab`; branch at planning time: `main`, dirty.
Architecture decisions behind this card were taken 2026-09-19 and are summarised in §"Decisions"
below. Read [global context](../CONTEXT.md), [rules](../RULES.md), [code](../code/CONTEXT.md).

This card is the single writer contract for Stages 1–4. One writer per stage. Do not start a
stage before the previous stage's human check is recorded in `Last handoff`.

## Decisions (frozen)

1. CLI tools only — TSK, Plaso, Volatility 3 through their documented command-line interfaces.
   No pytsk3, no dfVFS, no plaso-as-library, no volatility3-as-library. Structured output comes
   from `psort.py -o json_line` and `vol -r json`; pandas is a reader and table renderer only.
2. ForensicArtifacts / "LinuxForensics" definitions are cited in the thesis, not integrated.
3. Precompute in `prepare.py` only what is slow AND question-independent. Every targeted command
   stays visible in a notebook cell.
4. The notebook in `investigations/<scenario>/` is a TEMPLATE: generic markdown, no run facts,
   outputs stripped. Executing it against a RUN_ID produces an accepted snapshot stored beside
   that run's evidence. No notebook ever carries another run's narrative.
5. Run-specific findings live in `shared/experiments/<RUN_ID>/investigation/findings/findings.py`
   as plain Python literals, imported by the notebook. Never inside the template.
6. The human supplies every judgment; Python only counts, validates and renders. Python may warn,
   never decide.
7. No `MODE` flag for reference-vs-replica. The difference is how much the human writes.

## Stage 0 — clean start (ac, ~15 min)

- Working tree is dirty on `main`: modified `README.md`, `ai/README.md`, `ai/RULES.md`,
  `ai/tasks/father.md`, `ai/tasks/ptrace.md`, `investigations/father/investigation.ipynb`,
  `investigations/father/investigation_utils.py`, `tests/test_father_notebook_command.py`;
  deleted `docs/investigations/**/runme_*_investigation.md`; untracked `ai/research/output/`.
- Commit the ICM/docs changes separately from the notebook work so the refactor diff stays
  readable. Done 2026-09-19 in three commits (superseded notes, ICM rules + this card,
  notebook work in progress).
- Branch: `main` is the only branch; `public-surface-cleanup` no longer exists. All stages work
  on `main` in the primary checkout.
- **Do not accept Father Section 1 yet.** Its acceptance happens once, on the refactored code
  (Stage 3). Accepting now and rewriting after costs a second review of the same section.

## Stage 1 — `investigations/common/forensics.py`

Owner: Codex. No evidence access needed. ~250 lines, one file, one review pass.

Inputs to read: this card only. Do not load `RULES.md`, the toolbox, or the notebook — the
function contracts below are the complete specification.

Write scope: `investigations/common/forensics.py`, `investigations/common/__init__.py`.

| Function | Contract |
|---|---|
| `sh(cmd, *, label=None, out_dir=None, binary=False, check=False, show=True, tail=None)` | Print `$ cmd`; run via bash; keep stdout and stderr SEPARATE; write full stdout to `<out_dir>/<label>` and stderr to `<out_dir>/<label>.stderr.txt` (stderr file only when stderr is non-empty); display at most `tail` lines; return `CompletedProcess` with both `.stdout` and `.stderr` populated; raise `CalledProcessError` only when `check=True`. Normalise the label extension exactly once so no artifact is written both with and without `.txt`. |
| `q(value)` | `shlex.quote` wrapper for any value derived from evidence before it enters a command string. |
| `load_case(project_root, run_id)` | Read `manifest.json` + `dumps/acquisition.json`; return an object exposing `run_root`, `disk_image`, `disk_segments`, `memory_image`, `claims`, `platform`, `timezone`, `isf_path` (selected from `shared/isf/` by the manifest's recorded kernel), and the `data/ output/ recovered/ findings/ prepared/` dirs. Raise if `manifest["run_id"] != run_id`. This is the single RUN_ID parameterisation point. |
| `root_fs(image)` | Parse `mmls` including its real `Units are in N-byte sectors` line — never assume 512. Run `fsstat` on each numbered partition. Return `(offset_sector, sector_size, fs_type)` for the unique Ext4 candidate; raise listing all candidates when more than one matches. |
| `resolve(image, offset, guest_path)` | `ifind` with evidence-rooted symlink-hop resolution supporting relative, absolute and nested targets, each hop verified with `istat`. Return `(inode, chain)` or an explicit unresolved result carrying the observed chain. Never resolve a guest path against the examiner host filesystem. Cap hops and report a cycle rather than looping. |
| `load_bodyfile(path)` | 11 pipe-delimited fields → DataFrame. Preserve the raw name string and its name state. Epoch seconds → UTC columns alongside raw values; `0` becomes NaT, never a 1970 event. `locator = "<basename>#L<n>"`. Report malformed rows; never drop them silently. |
| `load_vol(path)` | Volatility 3 `-r json` → DataFrame, flattening `__children` while keeping the parent link. Addresses stay `str`/`Int64`, never float. Add a JSON-pointer locator. |
| `load_plaso(path)` | JSONL, chunked read → DataFrame. Microsecond `timestamp` → UTC column alongside the raw value. Keep `pathspec` and record offset where present. `locator = "plaso.jsonl#L<n>"`. |
| `sha256_file(path)` | Streaming `hashlib.file_digest`. |
| `show(df, cols=None, n=25, caption=None)` | Bounded display with caption and "showing N of M rows". |

Nothing else. No registry, no pipeline, no object model, no stale-input rejection engine.

**Done when:** the module imports; `sh()` satisfies the three assertions already present in
`tests/test_father_notebook_command.py`. Note that file asserts `result.stderr` and a
`<label>.stderr.txt` sidecar, while the current `investigation_utils.run_command` merges stderr
into stdout and returns `stdout=` only — so those tests fail today. **Make the code match the
test, not the reverse.**

**Human check:** read the file once end to end; run those three tests; run one real command
(`mmls` on the Father disk image) through `sh()` and confirm the artifact naming.

### Stage 1 launch prompt

Paste as the task message for whichever model executes Stage 1. It carries no methodology of its
own: everything it needs is reachable through the ICM.

```text
Repository: /home/anto/linux-multisource-dfir-lab

Read, in this order, and nothing else:
1. AGENTS.md
2. ai/CONTEXT.md — routing. You are in the "Bounded implementation" stage.
3. ai/code/CONTEXT.md — that stage's inputs, process and endpoint.
4. ai/RULES.md, sections "KISS, ownership and handoff" and
   "Investigation implementation and delivery".
5. ai/tasks/investigation-refactor.md, section "Stage 1" — your objective and the
   complete function specification.
6. tests/test_father_notebook_command.py — the acceptance criterion.

Do not read: investigations/father/investigation.ipynb, investigation_utils.py,
ai/forensic/*, docs/INVESTIGATION_METHOD.md, anything under shared/experiments/.
The Stage 1 table is the whole spec; do not go looking for more context.

Task: Stage 1 only. Create investigations/common/__init__.py and
investigations/common/forensics.py implementing exactly the ten functions in the
Stage 1 table, and nothing beyond them.

Write scope: those two files. Do not touch the notebook, investigation_utils.py,
the tests, the ICM, or any other file.

Checks: `python -c "import investigations.common.forensics"` and
`pytest tests/test_father_notebook_command.py`. Make the code satisfy that test
file as written — it fails today because the old helper merged stderr into
stdout. Do not modify the test.

Tests: write none. See ai/RULES.md, "Investigation implementation and delivery".

Do not commit. Leave the working tree dirty and stop.

Finish with the handoff defined in ai/RULES.md (at most 12 lines), replacing
"Last handoff" in ai/tasks/investigation-refactor.md.
```

## Stage 2 — `investigations/common/prepare.py`, stages `disk` and `ram`

Owner: Codex. Needs evidence access — runs on ac's machine.

Write scope: `investigations/common/prepare.py`.

CLI: `python -m investigations.common.prepare --run-id <ID> --stage disk|timeline|ram|all [--force]`.
Products under `shared/experiments/<RUN_ID>/investigation/prepared/raw/`.

- `disk`: `ewfinfo`; `ewfverify -d sha256`; `mmls`; `fsstat` per partition;
  `fls -r -m / -o OFF` → `allocated.body`; `ils -m -o OFF` → `unallocated.body`;
  `blkls -o OFF` → `unallocated.dd`.
- `ram`: `banners.Banners` against the selected ISF, then `pslist`, `psaux`, `pstree`,
  `proc.Maps`, `lsof`, `sockstat`, `lsmod`, `kmsg` as `-r json` files.
- `prepared/prepare.json` records: run id, evidence sha256 and hash scope, each tool's
  `--version` string, exact argv per product, start/end times, exit codes, and a per-product
  state of `ok | partial | failed | not_attempted`.

**A failed extraction must never present as an empty dataset.** That field is the control.

**Done when:** both stages complete on `father-u22-20260913-01`; re-running without `--force`
prints the existing `prepare.json` summary instead of recomputing.

**Human check:** `head` each product; confirm `allocated.body` really has 11 pipe-delimited
fields; point `--stage ram` at a deliberately wrong ISF and confirm the product is recorded
`failed`, not an empty success.

## Stage 3 — Father notebook port (Sections 0–1)

Owner: Claude. This is the delicate stage: it decides what counts as run-specific prose.

Write scope: `investigations/father/investigation.ipynb`,
`investigations/father/investigation_utils.py` (delete once callers move to `common/forensics.py`),
`investigations/father/README.md`.

Work:

1. Repoint cells at `investigations.common.forensics`; delete `investigation_utils.py`.
2. Remove debris: `!who`, `!ewfverify -V {help}` (interpolates the `help` builtin), the
   `VERIFY = False` switch, duplicate label artifacts written with and without `.txt`.
3. Remove hardcoded inodes (258049, 1550) and every other value carried from a previous run.
4. Replace the ad-hoc `/lib → usr/lib` string patch with `resolve()`.
5. Quote every evidence-derived value entering a command string with `q()` — `ld_preload_lib`
   comes from `icat` output and currently reaches a shell unquoted.
6. Regenerate the bodyfile correctly (`fls -r -m /`, from Stage 2's product) — the current
   `bodyfile.txt` is plain `fls -r` output and cannot become a timestamped table.
7. Move every run-specific observation out of markdown cells (`inode is 74252`,
   `/lib/selinux.so.3`, the `labuser pts/0 …` session line) into the run's findings record,
   displayed by a cell. Markdown keeps only the question and the technique.
8. Strip outputs from the template; keep the executed copy as the run's snapshot.

**Done when:** fresh kernel → Run All over Sections 0–1 → same conclusions as today, with no
hardcoded inode, offset or path, and no run facts in any markdown cell.

**Human check:** this IS the acceptance of Section 1. Do it once, here.

## Stage 4 — findings schema and the four tables

Owner: Claude.

Write scope: `investigations/common/results.py`, notebook result cells, and a first
`shared/experiments/father-u22-20260913-01/investigation/findings/findings.py`.

Run-local module exposes `FINDINGS` (the six RULES fields per claim/source), `COMBINED`
(human-written conclusion, corroboration classification, missing element, argument),
`CHRONOLOGY`, `OBJECTS`.

Python does: uniqueness check on `(claim_id, source)`; status vocabulary check against the six
statuses; locator presence check; the Table 2 pivot; Table 3 and Table 4 counts with explicit
dedup keys; support rate as `supported / (supported + partial + unsupported)` per source with
numerator and denominator both shown, `not_applicable` / `not_examined` / `tool_failure` excluded
and reported separately, zero denominator rendered "not calculable"; markdown rendering.

Python warns but never decides — e.g. `COMBINED` claiming `corroborated` while fewer than two
sources are `supported` prints a consistency warning for the human to resolve.

**Done when:** the four tables render from a hand-written findings record covering Section 1 only,
with the unexamined sections showing explicit pending states rather than zeros.

## Stage 5 — `prepare.py --stage timeline` (Plaso)

Owner: Claude for the parser-scope decision, Codex for the code.

Deliberately after Stage 4: the tables must exist before spending 15–45 min per run on Plaso.
Pin an explicit parser preset, record `pinfo.py` counters and warnings per run, and keep
`timeline.plaso` alongside `plaso.jsonl`.

## Stage 6+ — investigation work

Father Sections 2–5 (surrounding activity, RAM, deletion recovery, chronology), then the four
tables for real, then ptrace / Diamorphine / BadBPF on the same skeleton, then the distro
replicas. This is forensic analysis under the existing per-section human gates, not code work.

## Test policy (applies from Stage 1 onward)

**Boundary.** Runner, orchestrator and claim/manifest code is ac's own code and produces the
ground-truth reference: tests there are legitimate, and `tests/test_forensic_contracts.py` and
`tests/test_scenario_runtime.py` stay as they are. The investigation layer wraps documented
third-party tools: a test of `icat` extraction tests TSK, not this repository.

**For the investigation layer, no tests are written except this closed allowlist:**

1. `sh()` — stdout/stderr separation, artifact naming, non-zero exit handling.
   *(Already exists: `tests/test_father_notebook_command.py`, 3 tests. Keep.)*
2. `root_fs()` — a non-512-byte sector size is honoured; ambiguous candidates raise.
3. `load_bodyfile()` — 11 fields parsed; a zero timestamp becomes NaT, not a 1970 event.
4. `resolve()` — one relative and one absolute symlink hop resolve correctly.
5. findings validation — duplicate `(claim_id, source)` raises; an unknown status raises.
6. support rate — zero denominator renders "not calculable", never 0%.

Each entry names a defect that has already occurred or would silently corrupt a result table.
Total budget: roughly 60 lines. Fixtures are a few literal lines copied from real tool output in
this repository — **never a synthetic disk or memory image, and never fabricated forensic output.**

**Rules for agents:**

- Do not create a test unless this card names it and the defect it prevents.
- Do not create a new test file without explicit authorization. An unrequested test file is a
  review failure, not a bonus.
- Do not add a test to "cover" a function you just wrote.
- Delete a test that enforces obsolete complexity rather than updating it.
- Verification of forensic behaviour is executing the section against real evidence under human
  review, recorded in the notebook — not pytest.

This is also a thesis position, and a coherent one: correctness of the analysis rests on
documented tool interfaces, preserved raw outputs and human review, not on a test suite over
re-implemented logic. It follows directly from the CLI-over-library decision.

## Token discipline

- Never let an agent read `investigation.ipynb` as JSON. Extract cell sources with a script.
- Keep `.claudeignore` blocking raw evidence from file-reading tools; use filtered bash access.
- One stage per session. End every stage with a handoff of at most 12 lines appended below.
- Never two agents in the same file. Stages 1–2 (Codex) and Stage 3 (Claude) are sequential.

## Last handoff

- 2026-09-19: card created. Stage 0 pending: commit split, branch decision, and the standing
  instruction not to accept Father Section 1 until Stage 3.
