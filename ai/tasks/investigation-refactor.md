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

## Environment

`python` and `pytest` are not on `PATH`; use `.venv/bin/python -m pytest`. The virtualenv is
missing `pandas`, `pytest` and `tabulate` — install them before Stage 2
(`.venv/bin/pip install pandas pytest tabulate`).

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

### Stage 1 outcome (2026-09-19)

Delivered by Codex, then corrected in place. Three defects, all from specifying parsers without
access to real tool output:

- `load_case` read a flat acquisition sidecar; the real one nests `disk.path`, `disk.segments`,
  `memory.path` under `dumps/`, and the timezone sits at `platform.timezone`. Now verified against
  `father-u22-20260913-01`.
- `resolve()` looked for `Symbolic Link:`; `istat` writes a lowercase `symbolic link to` line.
  Symlinks were silently treated as regular files.
- `load_bodyfile` checked for `(realloc)`; TSK writes `(deleted-realloc)`, so reallocated deleted
  entries were classified allocated.

Also fixed: binary outputs no longer get a `.txt` suffix; a bodyfile row is no longer fatal when a
filename contains `|`. `tests/test_father_notebook_command.py` is renamed
`tests/test_forensics_sh.py` and imports `sh` from the new module.

**Rule for later stages: parser code must be verified against real tool output.** When a spec
cannot be verified from the card alone, ask before writing it.

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
- A tool-availability check runs first and is recorded: `mmls fls istat icat ifind fcat blkls
  blkcalc mactime ewfverify ewfmount debugfs ext4magic foremost log2timeline.py psort.py pinfo.py
  vol`. Missing tools are reported, not discovered mid-investigation.
- `prepare.py` prints its own progress: `sh()` captures output rather than streaming it, so a long
  tool shows nothing until it returns.
- `prepared/prepare.json` records: run id, evidence sha256 and hash scope, each tool's
  `--version` string, exact argv per product, start/end times, exit codes, and a per-product
  state of `ok | partial | failed | not_attempted`.

**A failed extraction must never present as an empty dataset.** That field is the control.

**Done when:** both stages complete on `father-u22-20260913-01`; re-running without `--force`
prints the existing `prepare.json` summary instead of recomputing.

**Human check:** `head` each product; confirm `allocated.body` really has 11 pipe-delimited
fields; point `--stage ram` at a deliberately wrong ISF and confirm the product is recorded
`failed`, not an empty success.

### Stage 2 launch prompt

Verification is by execution, not by unit tests: the agent runs the code against the real Father
run and pastes actual output. `blkls` is opt-in (`--with-unallocated`) because the unallocated
extract is multi-gigabyte and carving is a Stage 6 option, not a Stage 2 product.

```text
Repository: /home/anto/linux-multisource-dfir-lab

Read, in this order, and nothing else:
1. AGENTS.md
2. ai/CONTEXT.md — routing. You are in the "Bounded implementation" stage.
3. ai/code/CONTEXT.md — that stage's inputs, process and endpoint.
4. ai/RULES.md, sections "KISS, ownership and handoff" and
   "Investigation implementation and delivery".
5. ai/tasks/investigation-refactor.md, sections "Environment", "Stage 1 outcome"
   and "Stage 2".
6. investigations/common/forensics.py — the helpers you must reuse.

Do not read: investigations/father/investigation.ipynb, ai/forensic/*,
docs/INVESTIGATION_METHOD.md.

Task: Stage 2 only. Create investigations/common/prepare.py exposing

  --run-id <ID> --stage disk|ram|all [--force] [--with-unallocated] [--isf-dir DIR]

Do NOT implement the timeline (Plaso) stage; that is Stage 5.

Reuse sh(), q(), load_case(), root_fs() and sha256_file() from
investigations.common.forensics. Do not reimplement them and do not edit that
file: if you find a defect in it, report it in your reply instead of changing it.

Write scope: investigations/common/prepare.py only.

Environment: python and pytest are not on PATH — use .venv/bin/python. Install
pandas, pytest and tabulate into .venv first if they are missing.

Products go under shared/experiments/<RUN_ID>/investigation/prepared/raw/ :
  disk  — ewfinfo; ewfverify -d sha256; mmls; fsstat per partition;
          fls -r -m / -o OFF  -> allocated.body
          ils -m -o OFF       -> unallocated.body
          blkls -o OFF        -> unallocated.dd   (only with --with-unallocated)
  ram   — banners.Banners, then pslist, psaux, pstree, proc.Maps, lsof, sockstat,
          lsmod, kmsg, each as `vol -r json` into its own file

prepared/prepare.json records: run id, evidence sha256 and hash scope, each
tool's --version string, exact argv per product, start/end times, exit codes, and
a per-product state of ok | partial | failed | not_attempted. A failed extraction
must never be recorded as an empty success.

Before anything else the run records tool availability for: mmls fls istat icat
ifind fcat blkls blkcalc mactime ewfverify ewfmount debugfs ext4magic photorec
log2timeline psort pinfo vol3. Missing tools are reported, not discovered
later. prepare.py prints its own progress — sh() captures rather than streams, so
a long tool otherwise shows nothing until it returns.

Write no unit tests. Instead EXECUTE the code against run
father-u22-20260913-01 and paste the real output of these seven checks in your
reply. A claim without pasted output is not accepted.

1. --stage disk : paste the last 20 lines of output and the whole prepare.json.
2. head -2 prepared/raw/allocated.body and wc -l on it. Every line must have
   exactly 11 pipe-separated fields — show that it does.
3. --stage ram : paste the banners result and `ls -l prepared/raw/*.json`.
4. Loader round-trip, paste what it prints:
     from investigations.common.forensics import load_bodyfile, load_vol
     b = load_bodyfile(<allocated.body>)
     print(len(b), b.name_state.value_counts().to_dict())
     v = load_vol(<pslist.json>); print(len(v), list(v.columns)[:8])
5. Symlink resolution against real evidence (read-only, writes nothing):
     from investigations.common.forensics import load_case, root_fs, resolve
     resolve(disk_image, offset, "/lib/selinux.so.3")
   Paste the returned inode and the full chain. If it fails, say so plainly and
   do not patch forensics.py — this check exists to find out.
6. Failure is not emptiness: re-run --stage ram with --isf-dir pointing at an
   empty directory and paste the prepare.json entry showing state "failed".
7. Idempotency: re-run --stage disk without --force and paste the output showing
   it reported the existing bundle instead of recomputing.

Do not commit. Leave the working tree dirty and stop.

Keep the handoff in ai/tasks/investigation-refactor.md to at most 12 lines: what
you actually ran, where the evidence is, and anything not done. The pasted output
belongs in your reply, not in the card.
```

## Father notebook blueprint

Narrative model: Hal Pomeranz, *Linux Investigation* parts 1–4 (righteousit.com, 2026-05-04/07) —
the same rootkit family and broadly the same case. Discovery-driven: each block is one question, one
or two visible commands, bounded output, one short interpretation. Roughly six blocks per section.

**Entry premise (agreed 2026-09-19).** The analyst opens from a plausible trigger that does not name
the mechanism: monitoring reported an unexplained `sshd` restart and an unrecognised session on the
host; the system was powered off and disk and memory acquired. `/etc/ld.so.preload` must *surface*
from a persistence sweep, never be assumed. Scenario knowledge is disclosed in Section 0 and again in
Section 7; it does not steer the questions.

**Timeline placement.** Targeted time correlation early (istat times, `last`, scoped log greps, as in
part 1); the full `mactime` + Plaso synthesis late, in Section 5, as in part 3. No full timeline in
Sections 1–2.

**Clock reconciliation (established 2026-09-19).** Guest and runner clocks agree within ~0.4 s:
implant crtime 20:45:24.328 vs `timestomp_implant` 20:45:24.705; implant atime 20:46:00.416 vs
`restart_ssh` 20:46:00.809. **Open anomaly:** `/etc/ld.so.preload` carries crtime = mtime = ctime =
20:46:32.880, i.e. 44 s after `write_preload` (20:45:48.768) and 27 ms after RAM capture ended
(20:46:32.853). Test it (later rewrite / inode reuse / acquisition-path touch) rather than assuming
compatibility with the scenario window; the previous Section 1 interpretation asserted compatibility
and is wrong as written.

Working hypothesis (ac, 2026-09-19): acquisition order is RAM capture → shutdown → disk imaging, and
the implant is loaded into every dynamically linked process, so it may rewrite its own preload entry
during shutdown. If so the disk image records post-shutdown implant activity that the memory image
predates, and the two sources legitimately disagree. Test it: look for a deleted older
`/etc/ld.so.preload` inode, and for other files sharing the ~20:46:32.88 stamp. Several files sharing
it supports a shutdown-time rewrite. Report what the evidence shows; do not assert a cause.

Follow-up for `prepare.py`: its tool inventory still names `foremost`, `log2timeline.py`, `psort.py`,
`pinfo.py` and `vol`. On this host the binaries are `photorec`, `log2timeline`, `psort`, `pinfo` and
`vol3`. Portability of tool discovery is deferred to the end of the project.

### Section 0 — Evidence, scope, premise

| Block | Question | Technique |
|---|---|---|
| 0.1 | What triggered this examination and what is in scope? | Premise and scope statement |
| 0.2 | What evidence is this, and when was it acquired? | `load_case`; case and evidence tables; acquisition intervals |
| 0.3 | Is the evidence internally consistent? | `ewfverify` result from `prepare.json` (recorded, not re-run) |
| 0.4 | What are the limits? | Acquisition gap RAM→disk, vanilla logging, scenario-informed disclosure |
| 0.5 | How are timestamps to be read? | Guest `/etc/timezone` and `/etc/localtime` vs examiner; everything displayed UTC |

### Section 1 — Disk: what persists, and what is unusual? (Pomeranz part 1)

| Block | Question | Technique | Claims |
|---|---|---|---|
| 1.1 | Which partition holds the root filesystem? | `mmls`, `fsstat` from prepared products; `root_fs()` | — |
| 1.2 | Which persistence-relevant paths exist, and which are unexpected on a vanilla cloud image? | Bodyfile query over `/etc/ld.so.preload`, `/etc/ld.so.conf.d`, `/etc/cron*`, `/etc/systemd/system`, `/etc/rc*.d`, `/etc/profile.d`, `~/.bashrc`, `~/.profile` | preload_persistence |
| 1.3 | What does the preload configuration contain? | `resolve()` → `istat` → `icat` | preload_persistence |
| 1.4 | What is the referenced object? | `resolve()` through the `/lib` symlink; `istat`; `icat`; `file`, `sha256sum`, `strings`, `readelf` | preload_persistence |
| 1.5 | Do the implant's timestamps hold together? | `istat` vs a reference libc; mtime/ctime/crtime relations | implant_timestomp |
| 1.6 | Do the preload file's timestamps fit the rest? | Compare against 1.5 and the acquisition interval; investigate the 44 s anomaly | preload_persistence |

Review gate.

### Section 2 — Surrounding activity: who, when, what else changed? (part 1 tail)

| Block | Question | Technique | Claims |
|---|---|---|---|
| 2.1 | Which login sessions exist? | `fcat` wtmp/btmp → `TZ=UTC last -F -i` / `lastb` | runtime_loading_backdoor |
| 2.2 | What local accounts and privileges existed? | passwd, shadow, group, sudoers extraction | — |
| 2.3 | What do the authentication and service logs record? | Scoped `grep` on auth.log, syslog, journal: session open, sudo, sshd restart | runtime_loading_backdoor |
| 2.4 | Is there shell history? | History-file lookup and content; absence is not erasure | shell_history_cleanup |
| 2.5 | What is staged in `/tmp` and `/dev/shm`? | Unbiased `fls` inventory first, then content of what is there | credential_staging, recon_staged |
| 2.6 | Is the staged file byte-identical to `/etc/shadow`? | `icat` both, compare SHA-256 of bytes, not decoded text | credential_staging |

Review gate.

### Section 3 — Memory: what was running? (parts 2–3)

| Block | Question | Technique | Claims |
|---|---|---|---|
| 3.1 | Does the image match the symbols? | `banners.Banners` from prepared products | — |
| 3.2 | What processes existed and how are they related? | `PsTree`, `PsAux` | — |
| 3.3 | Which processes map the implant? | `proc.Maps` + `LibraryList` filtered by path; count PID + path | preload_persistence |
| 3.4 | Is `LD_PRELOAD` present in any environment? | `Envars` — a deliberate negative: `/etc/ld.so.preload` sets no variable | preload_persistence |
| 3.5 | Which endpoints were open at capture? | `Sockstat` + `Lsof`; enumerate first, attribute after — do not search for the scenario-supplied port | runtime_loading_backdoor |
| 3.6 | Does memory retain shell history the disk no longer has? | `linux.bash` | shell_history_cleanup |
| 3.7 | Can the implant be recovered from memory and compared to the disk copy? | `linux.elfs --dump`; SHA-256 against the `icat` copy | preload_persistence |
| 3.8 | Are kernel-level mechanisms clean? | `check_syscall`, `modxview`, `Lsmod`, `EBPF`, `Kmsg` — valid zero rows, the baseline the kernel scenarios will contrast with | — |

Review gate.

### Section 4 — Deletion recovery

| Block | Question | Technique | Claims |
|---|---|---|---|
| 4.1 | Which deleted entries survive? | `fls -rdp` on `/tmp`, `/dev/shm`; bodyfile `name_state` filter | deleted_staging_artifact |
| 4.2 | Can content be recovered from a candidate inode? | `istat`, `icat -r`, `file`, `sha256sum` | deleted_staging_artifact |
| 4.3 | Does the journal recover the path in a bounded window? | `debugfs -R 'dump <8>'`; `ext4magic -j -a -b -f /tmp/rk.so -r` on a read-only `noload` mount | deleted_staging_artifact |
| 4.4 | Does carving unallocated space recover it? | `blkls` (`--with-unallocated`) → `photorec` scoped to ELF → `blkcalc` back to blocks; validate against the implant hash | deleted_staging_artifact |
| 4.5 | What is the outcome, precisely? | Classify: content / partial / metadata-or-name-only / bounded negative / tool failure / not attempted | deleted_staging_artifact |

Review gate.

### Section 5 — Chronology (part 3)

| Block | Question | Technique |
|---|---|---|
| 5.1 | What does the filesystem say happened, in order? | `mactime -b allocated.body` scoped to the window; `unallocated.body` kept separate |
| 5.2 | What do the log-derived records add? | Plaso filtered to the window, tagged by parser; `filestat` rows marked disk-origin |
| 5.3 | What is the reconstructed chronology? | One table: time \| observation \| locator/origin \| interpretation \| limitation |
| 5.4 | What does the acquisition itself contribute? | RAM 20:46:30.99–20:46:32.85 vs disk from 20:46:38; examiner-induced atimes; the preload anomaly |

### Section 6 — Result tables

Validate `FINDINGS`, render the four tables and the permitted counts. Code counts; the human judges.

### Section 7 — Ground-truth validation (part 4)

Compare the reconstruction with `command_log.jsonl` and the seven claims: agreements, discrepancies,
what forensics could not see, and prior knowledge disclosed. Ground truth is an experimental
reference, not a fourth evidence source.

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
8. Snapshot mechanism, one command at acceptance time — no hooks, no jupytext:
   `jupyter nbconvert --to html investigations/father/investigation.ipynb --output-dir
   shared/experiments/$RUN_ID/investigation --output executed`. The template keeps whatever
   outputs it has; what must stay run-neutral is the code.

**Done when:** fresh kernel → Run All over Sections 0–1 → same conclusions as today, with no
hardcoded inode, offset or path, and no run facts in any markdown cell.

**Human check:** this IS the acceptance of Section 1. Do it once, here.

### Stage 3 launch prompt

```text
Repository: /home/anto/linux-multisource-dfir-lab

Read, in this order, and nothing else:
1. AGENTS.md
2. ai/CONTEXT.md — routing. You are in the supervised "Forensics" stage.
3. ai/forensic/CONTEXT.md — that stage's inputs, process and endpoint.
4. ai/RULES.md, sections "Findings and manual assessment",
   "Investigation implementation and delivery", and "KISS, ownership and handoff".
5. ai/tasks/investigation-refactor.md, sections "Environment",
   "Father notebook blueprint" and "Stage 3".
6. investigations/common/forensics.py and investigations/common/prepare.py.
7. The prepared bundle for father-u22-20260913-01:
   investigation/prepared/prepare.json and the raw/ product list.

Do not read: ai/forensic/TOOLBOX.md, docs/INVESTIGATION_METHOD.md, the other task
cards, shared/experiments/*/command_log.jsonl. The blueprint is the spec.

Task: Stage 3. Rebuild Sections 0 and 1 of
investigations/father/investigation.ipynb exactly as the blueprint's Section 0
(blocks 0.1-0.5) and Section 1 (blocks 1.1-1.6) describe. Do not touch
Sections 2-7; leave their placeholder Markdown in place.

Also add to investigations/common/forensics.py, and nothing else there: a
`Finding` dataclass with fields claim_id, source, status, locator, observation,
limitation; a module-level convention that the notebook keeps `FINDINGS = []`;
and `dump_findings(findings, path)` writing JSON. Statuses are the six in
ai/RULES.md. No validation logic, no table rendering — that is Stage 4.

Then delete investigations/father/investigation_utils.py and update
investigations/father/README.md.

Rules for the notebook:
- Every cell uses investigations.common.forensics. RUN_ID is the only run-specific
  literal in the whole notebook. No hardcoded inode, offset, or path discovered in
  a previous run.
- Any value taken from the evidence is quoted with q() before entering a command.
- Markdown cells carry the question and the technique only. No run-specific
  observation, inode number, filename, or timestamp in Markdown. Per-run
  observations go in Finding(...) calls next to the evidence.
- Read prepared products where they exist (mmls, fsstat, bodyfiles, ewfverify)
  instead of re-running those tools; show the recorded invocation. Do not re-run
  ewfverify or fls -r.
- Bounded display via show() or tail=; full output stays on disk.
- Delete the debris: !who, `!ewfverify -V {help}`, the VERIFY switch, the
  duplicate .txt/no-extension artifacts, and the mount/UAC cells.
- Block 1.2 must enumerate persistence locations from the bodyfile and let
  /etc/ld.so.preload surface as a result. It must not assume LD_PRELOAD.
- Block 1.6 follows the blueprint's working hypothesis. Report what the evidence
  shows; do not assert a cause.

Write scope: investigations/father/investigation.ipynb,
investigations/father/README.md, the Finding addition in
investigations/common/forensics.py, and the deletion of investigation_utils.py.
Nothing else.

Write no tests. Verify by execution: restart the kernel and run Sections 0-1 only
— do not execute the Section 2-7 placeholder cells, which reference variables that
no longer exist. Paste in your reply the real output of blocks 1.2, 1.3, 1.4, 1.5
and 1.6, plus the contents of the dumped findings JSON. If a block fails, paste
the failure rather than working around it.

Environment: use .venv/bin/python. The notebook file is currently dirty; work from
its present state.

Do not commit. Keep the handoff in ai/tasks/investigation-refactor.md to at most
12 lines; pasted output belongs in your reply.
```

## Stage 4 — findings schema and the four tables

Owner: Claude.

Write scope: `investigations/common/results.py`, notebook result cells, and a first
`shared/experiments/father-u22-20260913-01/investigation/findings/findings.py`.

Findings are built inline in the notebook, next to the evidence that motivates them: a small
`Finding` dataclass, `FINDINGS = []` near the top, and `FINDINGS.append(Finding(...))` after the
relevant cell. Locator, inode, command and paths come from live variables, so they are expressions
rather than run facts; only `status`, `observation` and `limitation` are per-run prose. At each
section's end the notebook writes `FINDINGS` to
`shared/experiments/<RUN_ID>/investigation/findings/findings.json` as the durable record. Same
shape for `COMBINED` (human conclusion, corroboration classification, missing element, argument),
`CHRONOLOGY` and `OBJECTS`. No separate findings module and no loader.

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

Measured on `father-u22-20260913-01` (2026-09-19): default parsers, **8 min 34 s**, 310,319
events — `filestat` 302,902, `syslog_traditional` 4,156, `systemd_journal` 3,156, `dpkg` 81,
`utmp` 22, `apt_history` 2; 2 extraction warnings (gzip consolefonts), 3 timelining warnings on
`auth.log`, `kern.log`, `syslog`.

So: keep the default parser set, record `pinfo.py` counters and warnings per run, keep
`timeline.plaso` beside `plaso.jsonl`, and tag events by parser. `filestat` is 97.6% of the
timeline and renders the same ext4 metadata TSK reads, so those rows count as disk-origin under
the independence rule — genuine independent timeline evidence is the 2.4% log and utmp records.
Confirm what the three `auth.log`/`kern.log`/`syslog` timelining warnings are before relying on
the login-session correlation.

## Stage 6+ — investigation work

Father Sections 2–5 (surrounding activity, RAM, deletion recovery, chronology), then the four
tables for real, then ptrace / Diamorphine / BadBPF on the same skeleton, then the distro
replicas. This is forensic analysis under the existing per-section human gates, not code work.

## Section prompts (queue)

Paste in order. Each ends leaving the tree dirty; ac reviews the pasted output and commits.

### Section 2 — surrounding activity

```text
Repository: /home/anto/linux-multisource-dfir-lab

Read, in this order, and nothing else:
1. AGENTS.md
2. ai/CONTEXT.md — routing. You are in the supervised "Forensics" stage.
3. ai/forensic/CONTEXT.md
4. ai/RULES.md, sections "Findings and manual assessment" and
   "Investigation implementation and delivery".
5. ai/tasks/investigation-refactor.md, sections "Environment" and
   "Father notebook blueprint" (the section you are building).
6. investigations/common/forensics.py — the helpers you must reuse.
7. investigations/father/investigation.ipynb — Sections 0-1, for style and for
   the variables already bound.

Style, non-negotiable, matching Sections 0-1:
- One block = one markdown question, one short code cell, one empty markdown
  cell reading "**Interpretation.** _(to write)_". You do NOT write
  interpretations; the analyst does.
- Visible commands through fx.sh, bounded display via tail= or fx.show.
  Paths are relative to the case directory (the notebook has already chdir-ed).
- Do NOT create Finding objects anywhere. Findings are written by hand in
  Section 6.
- Enumerate before selecting. Never grep for a name, port or path taken from
  the scenario; find it in the evidence and say where it came from.
- No raise on an expected result. Print what was found, including zero.
- Keep each code cell under about 25 lines. If it needs more, it is doing too
  much.

Write scope: investigations/father/investigation.ipynb only. Do not touch
forensics.py, prepare.py, the ICM, or the other sections.

Write no tests. Verify by execution: restart the kernel, run Sections 0 through
the one you built, and paste the real output of each new block in your reply.
If a block fails, paste the failure.

Environment: .venv/bin/python; volatility is vol3; do not commit; keep the
handoff in ai/tasks/investigation-refactor.md to at most 12 lines.

Task: build Section 2 of the notebook, replacing its placeholder markdown.

Start by reading, and reporting in your reply, what the evidence already gives
you to pivot on:
  investigation/output/s1-05-object-strings.txt   (strings from the object)
  investigation/output/s1-02-recent-changes.csv   (what changed before imaging)
Pick the paths, filenames, user names and constants worth following. Say which
you chose and why. Those choices drive the blocks below.

Blocks:
2.1 Which login sessions exist? Extract wtmp and btmp with fcat, read them with
    `last -F -i -f` and `lastb -F -i -f` under TZ=UTC.
2.2 What local accounts and privileges existed? Extract passwd, group, shadow
    metadata and sudoers; show them.
2.3 What do the authentication and service logs record? Extract auth.log,
    syslog and the journal; search them for the account names and times from
    2.1 and the strings from 1.5. Show the matching lines with line numbers.
2.4 Is there shell history for any account? Look for history files in the
    bodyfile; extract and show any that exist. Absence is a bounded negative,
    not erasure - state the scope you searched.
2.5 What exists in /tmp and /dev/shm? Enumerate both allocated and deleted
    entries with fls; show the inventory before selecting anything.
2.6 For each staged file worth examining, extract the bytes with icat and
    characterise it: file, sha256sum, and where the content looks like a copy
    of a system file, compare SHA-256 of the extracted bytes against the
    SHA-256 of the extracted original. Compare bytes, never decoded text.
```

### Section 3 — memory

```text
Repository: /home/anto/linux-multisource-dfir-lab

Read, in this order, and nothing else:
1. AGENTS.md
2. ai/CONTEXT.md — routing. You are in the supervised "Forensics" stage.
3. ai/forensic/CONTEXT.md
4. ai/RULES.md, sections "Findings and manual assessment" and
   "Investigation implementation and delivery".
5. ai/tasks/investigation-refactor.md, sections "Environment" and
   "Father notebook blueprint" (the section you are building).
6. investigations/common/forensics.py — the helpers you must reuse.
7. investigations/father/investigation.ipynb — Sections 0-1, for style and for
   the variables already bound.

Style, non-negotiable, matching Sections 0-1:
- One block = one markdown question, one short code cell, one empty markdown
  cell reading "**Interpretation.** _(to write)_". You do NOT write
  interpretations; the analyst does.
- Visible commands through fx.sh, bounded display via tail= or fx.show.
  Paths are relative to the case directory (the notebook has already chdir-ed).
- Do NOT create Finding objects anywhere. Findings are written by hand in
  Section 6.
- Enumerate before selecting. Never grep for a name, port or path taken from
  the scenario; find it in the evidence and say where it came from.
- No raise on an expected result. Print what was found, including zero.
- Keep each code cell under about 25 lines. If it needs more, it is doing too
  much.

Write scope: investigations/father/investigation.ipynb only. Do not touch
forensics.py, prepare.py, the ICM, or the other sections.

Write no tests. Verify by execution: restart the kernel, run Sections 0 through
the one you built, and paste the real output of each new block in your reply.
If a block fails, paste the failure.

Environment: .venv/bin/python; volatility is vol3; do not commit; keep the
handoff in ai/tasks/investigation-refactor.md to at most 12 lines.

Task: build Section 3 of the notebook, replacing its placeholder markdown.

The RAM baseline is already prepared: investigation/prepared/raw/*.json holds
banners, pslist, psaux, pstree, proc.Maps, lsof, sockstat, lsmod and kmsg.
Load those with fx.load_vol instead of re-running vol3. Only the plugins not in
that set are run inline with fx.sh.

Blocks:
3.1 Does the image match the symbols? Show the prepared banners result.
3.2 What processes existed, and how are they related? pstree and psaux from the
    prepared JSON; show a bounded view.
3.3 Which processes map the object found in Section 1? Filter proc.Maps by the
    object path observed there - not by a path you typed. Count distinct
    PID + path pairs, not mapping rows.
3.4 Is LD_PRELOAD present in any process environment? Run linux.envars inline.
    A negative here is the expected result for a file-based preload and must be
    reported as such, not as a failure.
3.5 Which endpoints were open at capture? Show sockstat and lsof from the
    prepared JSON, enumerated in full first; then attribute the ones belonging
    to the processes from 3.3.
3.6 Does memory hold shell history the disk does not? Run linux.bash inline for
    the relevant PIDs.
3.7 Can the object be recovered from memory? Run linux.elfs with --dump for a
    mapping PID, then sha256sum the result and compare it with the disk copy
    extracted in 1.5.
3.8 Are kernel-level mechanisms clean? Run linux.malware.check_syscall,
    linux.malware.modxview and linux.ebpf inline, plus the prepared lsmod and
    kmsg. Valid zero rows are a result, not an error - these negatives are the
    baseline the kernel scenarios will be compared against.
```

### Section 4 — deletion recovery

```text
Repository: /home/anto/linux-multisource-dfir-lab

Read, in this order, and nothing else:
1. AGENTS.md
2. ai/CONTEXT.md — routing. You are in the supervised "Forensics" stage.
3. ai/forensic/CONTEXT.md
4. ai/RULES.md, sections "Findings and manual assessment" and
   "Investigation implementation and delivery".
5. ai/tasks/investigation-refactor.md, sections "Environment" and
   "Father notebook blueprint" (the section you are building).
6. investigations/common/forensics.py — the helpers you must reuse.
7. investigations/father/investigation.ipynb — Sections 0-1, for style and for
   the variables already bound.

Style, non-negotiable, matching Sections 0-1:
- One block = one markdown question, one short code cell, one empty markdown
  cell reading "**Interpretation.** _(to write)_". You do NOT write
  interpretations; the analyst does.
- Visible commands through fx.sh, bounded display via tail= or fx.show.
  Paths are relative to the case directory (the notebook has already chdir-ed).
- Do NOT create Finding objects anywhere. Findings are written by hand in
  Section 6.
- Enumerate before selecting. Never grep for a name, port or path taken from
  the scenario; find it in the evidence and say where it came from.
- No raise on an expected result. Print what was found, including zero.
- Keep each code cell under about 25 lines. If it needs more, it is doing too
  much.

Write scope: investigations/father/investigation.ipynb only. Do not touch
forensics.py, prepare.py, the ICM, or the other sections.

Write no tests. Verify by execution: restart the kernel, run Sections 0 through
the one you built, and paste the real output of each new block in your reply.
If a block fails, paste the failure.

Environment: .venv/bin/python; volatility is vol3; do not commit; keep the
handoff in ai/tasks/investigation-refactor.md to at most 12 lines.

Task: build Section 4 of the notebook, replacing its placeholder markdown.

Before starting, check that photorec is installed (testdisk package) and report
it if not. ext4magic and debugfs are present.

Known before you start, from the prepared bodyfiles: every unallocated inode
record in this image has size 0, so inode-level content recovery is expected to
fail. That expected negative must be demonstrated and recorded, not skipped.

Blocks:
4.1 Which deleted entries survive? fls -rdp over the directories of interest,
    plus the non-allocated rows of the prepared bodyfile.
4.2 Can content be recovered from a candidate inode? istat, then icat -r, then
    file and sha256sum on whatever comes out. Show the empty result if empty.
4.3 Does the ext4 journal recover a known path in a bounded window? Dump the
    journal with debugfs, then run ext4magic for the target path over a time
    window justified by Sections 1 and 2. This step needs a read-only mount
    with noload; mount it, use it, unmount it in the same cell.
4.4 Does carving recover it? Run prepare.py --stage disk --with-unallocated to
    produce the unallocated extract, carve it with photorec restricted to ELF,
    and map candidates back to blocks with blkcalc. Validate any candidate
    against the SHA-256 of the object extracted in 1.5.
4.5 State the outcome for each attempt as exactly one of: content recovered,
    partial content recovered, metadata or name trace only, no result in
    examined scope, tool failure, not attempted.
```

## Test policy (applies from Stage 1 onward)

**Boundary.** Runner, orchestrator and claim/manifest code is ac's own code and produces the
ground-truth reference: tests there are legitimate, and `tests/test_forensic_contracts.py` and
`tests/test_scenario_runtime.py` stay as they are. The investigation layer wraps documented
third-party tools: a test of `icat` extraction tests TSK, not this repository.

**For the investigation layer, no tests are written except this closed allowlist:**

1. `sh()` — stdout/stderr separation, artifact naming, non-zero exit handling.
   *(Already exists: `tests/test_forensics_sh.py`, 3 tests. Keep.)*
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

- 2026-09-19: Stage 3 completed in the primary checkout; no commit; existing dirty work preserved.
- Rebuilt Father notebook Sections 0–1 as blocks 0.1–0.5 and 1.1–1.6.
- Sections 2–7 placeholders remain unexecuted; the mount/UAC debris block was removed.
- Added `Finding`, the notebook `FINDINGS` convention and JSON dumping to shared forensics helpers.
- Deleted the Father-only helper and updated the Father README.
- Fresh kernel executed only Sections 0–1 twice against `father-u22-20260913-01`; all blocks passed.
- Prepared `mmls`, `fsstat`, bodyfile and `ewfverify` products were read, not regenerated.
- Draft JSON has one disk assessment per examined claim; all statuses remain `partial` pending review.
- Limit: same-second peers and no deleted preload-path row do not establish the timestamp anomaly's cause.
- Next: human reviews the displayed evidence and accepts or rejects Section 1; stop before Stage 4.
