# Investigation layer refactor — staged work order

## Context


Scenario: none (shared investigation infrastructure); stage: bounded code, then forensics.
Checkout: `/home/anto/linux-multisource-dfir-lab`; branch at planning time: `main`, dirty.
Architecture decisions behind this card were taken 2026-09-19 and are summarised in §"Decisions"
below. Read [global context](../CONTEXT.md), [rules](../RULES.md), [code](../code/CONTEXT.md).

This card is the staged investigation contract. One writer per stage. Follow the dependency
order authorised in `Last handoff`, not numerical order. On 2026-09-23 ac authorised Stage 5
before Stage 4 findings/tables. On 2026-09-24 ac selected notebook Section 5 and authorised
refreshing the full Plaso export as its prerequisite. Notebook interpretations remain deferred
until final review. This is preparation and examination work, not forensic acceptance.

## Decisions (frozen)


1. CLI tools only — TSK, Plaso, Volatility 3 through their documented command-line interfaces.
   No pytsk3, no dfVFS, no plaso-as-library, no volatility3-as-library. Structured output comes
   from `psort -o json_line` and `vol3 -r json`; pandas is a reader and table renderer only.
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


Use `.venv/bin/python`; `pandas`, `pytest` and `tabulate` are installed (checked 2026-09-23).
The installed Plaso CLIs are `log2timeline`, `psort` and `pinfo`, all version 20260512,
under `/home/anto/.local/bin/`. Produce Plaso products through `prepare.py --stage timeline`;
do not maintain a separate extraction workflow.

## Working split

Decided 2026-09-23 (ac); replaces the split in which Claude supervised and Codex implemented.

- **ac** is the analyst. Interpretations, claim predicates, status assignments and every conclusion
  drawn from evidence belong to ac alone.
- **Astra** (GPT Astra 6, high effort, its own Codex session) supervises: keeps this card and
  `ai/RULES.md` consistent, writes the single active prompt in `ai/tasks/next.md`, and reviews what
  comes back. It verifies by running read-only commands against the real files and evidence, never
  by reasoning from the documents, and never edits `investigations/**`.
- **Claude Code** (its own session) implements: one bounded task per prompt, verified against
  real evidence. Notebook changes require a fresh-kernel replay through the authorised section;
  a preparation-only task runs the selected CLI stage in a fresh process. Paste the relevant
  real output in the reply, replace `Last handoff`, and make no commits unless ac asks.
- ac relays between the two sessions; neither session launches the other.

One writer per file at a time. When a decision changes, the document changes in the same turn.

## State of play

Father is the reference run, `father-u22-20260913-01`, Ubuntu 22.04.

| | Status |
|---|---|
| `investigations/common/forensics.py` | Done. Frozen — no further refactoring until Father is complete. |
| `investigations/common/prepare.py` | Disk, RAM and timeline run on Father. The canonical JSONL includes `filestat`; reuse it for this run. |
| Notebook Sections 0–3 | Built and executed. |
| Section 4 | Done 2026-09-23; ac approved proceeding. Interpretation cells still to write. |
| Sections 5–7 | Section 5 executed as a draft. On 2026-10-01 ac chose a simplified, manual investigation style (option 2) pending Astra's review; the semi-automated Sections 0–6 are archived in `investigations/archived/father_semi_automated_2026_10_01/`. |
| Claim predicates | Strict element rule chosen by ac 2026-10-01; the element checklist is in [father.md](father.md#claim-predicates). ac judges each cell by hand against it. |
| Distro replicas, other scenarios | Not started. |

Deferred until Father is complete, deliberately: `sh()` has no timeout; `prepare.json` duplicates
evidence hashes already in `acquisition.json`; unrelated tool-inventory cleanup (`foremost`
instead of `photorec`) and general portability. Stage 5 corrected the three Plaso inventory
names to `log2timeline`, `psort` and `pinfo`; the inventory already used `vol3`.
Also deferred: the full-notebook design review at the end of Father — clean code and
understandable output (e.g. 4.7's right-aligned locator column, 2.1 printing the empty btmp's
extraction time as "btmp begins").

Divergences from the frozen decisions, accepted until Father is complete (ac, 2026-09-22):

- `investigations/father/investigation.ipynb` is committed **with executed outputs** (34 cells,
  run-specific paths, inodes and hashes), against Decision 4. Strip before the template is reused
  for another scenario or another run.
- Findings for this run exist as `investigation/findings/findings.json`, not the `findings.py`
  Decision 5 requires. Section 6 has to reconcile this.
- `.claudeignore` ends with three shell commands accidentally appended as ignore patterns
  (`find ai -maxdepth 3 -type f | sort`, `git diff --check`, `git status --short`).

Dispatch: `ai/tasks/next.md` holds the one active prompt. It is replaced between tasks.

## Stages

Stages 0–3 are complete; their launch prompts are spent and live in git history. Stage 5's
full Plaso export and notebook Section 5 exist. For this Father run, do not regenerate Plaso.

| Stage | State |
|---|---|
| 0 — clean start | Done. `main` is the only branch. |
| 1 — `forensics.py` | Done. Three parser defects found and corrected against real tool output. |
| 2 — `prepare.py` disk + ram | Done. Failure and emptiness are distinguished in `prepare.json`. |
| 3 — notebook Sections 0–1 | Done, then thinned from 643 to ~170 code lines. |
| 4 — findings and the four tables | Active in two checkpoints: first a source-located draft proposal and four-table preview for ac's judgment; after review, materialize human-approved findings and Section 6 rendering. Sparse observation notes are sufficient, but every claim/source status must be explicit: omission cannot mean `unsupported`. Code counts, validates and renders; it never decides. |
| 5 — `prepare.py --stage timeline` | Implemented and run on Father. The canonical JSONL has 310,364 events, including 302,947 `filestat` (97.6%); the store is `partial` for two GZIP extraction and three syslog year-inference warnings. Reuse these products; filtering remains visible in the notebook. TSK and Plaso filesystem metadata share an origin. |
| 6+ — investigation | Section 5 draft executed; Sections 6–7 wait. After draft results and review, first simplify the whole notebook cell by cell, including Section 5 and incremental timestamp observations; freeze reviewed sections, then separately audit deeper structural duplication, bugs and boilerplate. Keep these as separate selected tasks. |

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
`restart_ssh` 20:46:00.809. The `/etc/ld.so.preload` stamp of 20:46:32.880 — 44 s after
`write_preload` (20:45:48.768) — was recorded here as an open anomaly. The previous Section 1
interpretation asserted compatibility with the scenario window and is wrong as written.

**The mechanism is inode reuse (verified 2026-09-22, supervising session, against the image).**
`ifind -n /etc/ld.so.preload` returns **inode 74252** — the same inode the journal shows as
`/tmp/rk.so` in 4.3. `istat` on it: allocated, mode 0644, size 17, block 296191, crtime = mtime =
ctime 20:46:32.880; `icat` returns `/lib/selinux.so.3`. Block 4.4's own version list already
records the whole life of that inode: 32,784 B at block 338469 (mtime 20:45:12), then size 0 with
dtime 20:46:30, then 17 B at block 296191 with mtime 20:46:32. `remove_staged_implant`
(`rm -f -- /tmp/rk.so`) freed 74252, and the file created 2 s later took it. RAM capture
(`virsh dump`) ran 20:46:30.996–20:46:32.853, so the re-creation is 27 ms after the guest resumed.
This supports ac's 2026-09-19 hypothesis that the preload entry is rewritten late, and it means the
disk copy of `/etc/ld.so.preload` is not the one `write_preload` created. Remaining for the
analyst: locate the older, now-deleted preload inode, and check whether other files carry the
~20:46:32.88 stamp. Report what the evidence shows; do not assert a cause.

Consequence for block 4.3: its "matches Sections 1–2: True" line is printing this reuse, not
continuity of the recovered object. Do not read it as corroboration.

Follow-up for `prepare.py`: the unrelated `foremost` inventory entry and general tool-discovery
portability remain deferred.

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

Specification: [ext4-recovery-tools.md](../research/output/ext4-recovery-tools.md), 2026-09-21.
Three mechanically distinct techniques, attempted A → B → C. Target `/tmp/rk.so`, evidence-derived
from the journal lines recovered in 2.3. Every technique runs with `check=False`; a crash, timeout
or parse error is recorded as `tool failure`, never as evidence of erasure.

| Block | Technique | Question |
|---|---|---|
| 4.1 | **A — surviving metadata** | `fls -rd -p` on `/tmp`, regular-file rows only; `ils -A -Z` counts of unallocated inodes and zero sizes. Shows ext4 cleared size and extents on unlink; the negative is bounded to that traversal. |
| 4.2 | **B — journal export** | `istat` inode 8 for the length, `icat` inode 8 into `data/journal.bin`. No mount, no root. |
| 4.3 | **B — names in the journal** | `timeout -k 5s 120s debugfs -R "logdump -O -a …"` over the export — 1.47.0 predates the 1.47.1 loop fix; the final short read is the expected end. `grep -aboF` the basename; decode each hit as `ext4_dir_entry_2` with its preceding entry. |
| 4.4 | **B — inode versions in the journal** | Inode-table block computed from `fsstat`; every logged copy of the recovered inode decoded (mode, size, links, mtime, dtime, extents), deduplicated, oldest journal block first. |
| 4.5 | **B — content from the old extent map** | `blkcat` the logged extent from the image, trim to the logged size, `file` and SHA-256 against Section 1.5. |
| 4.6 | **C — free-space ELF carving** | PhotoRec scripted `freespace` ELF pass, scratch outside the case. A candidate matches when it begins with the complete 1.5 reference; its disk-relative sector range from PhotoRec's log gives filesystem blocks, and `blkstat` their allocation. ELF header length printed. **Never `blkls`** — that export is 8.46 GB. |
| 4.7 | **Outcomes** | One table, one row per technique, with the locator of each raw output. |

**Outcome rule (ac, 2026-09-23).** A technique reports `content recovered` only when the object's
bytes come from blocks wholly unallocated at acquisition. A carve over the still-allocated `/lib`
copy is not recovery of the deleted file. On this run both B and C recover it from blocks
338469–338477. The earlier `jls`/`jcat` reader cross-check was dropped in the 2026-09-21 rebuild.

**Excluded, do not run even where installed:** `ext4magic` (upstream discontinued 2024-09-30;
crashes reported in targeted listing mode), `extundelete` (fails with 64bit/metadata_csum),
`tsk_recover` (traverses filesystem objects, skips zero-size metadata — not a distinct mechanism),
`scalpel`, `bulk_extractor`, `foremost`. No mount is needed by any of the three techniques.

**Lesson for the remaining scenarios.** Make the deleted artifact something that does *not* survive
elsewhere on the filesystem — a unique script or payload, not a copy of an installed file. An
identical allocated copy makes a content match ambiguous; Father resolved it only by block location
(4.5's extent map, 4.6's sector index and `blkstat`), and a unique artifact avoids needing to.

### Section 5 — Chronology (part 3)

| Block | Question | Technique |
|---|---|---|
| 5.1 | What did Plaso collect, and with what limits? | `pinfo` parser inventory, product states and warnings; full `timeline.jsonl` row count and fields; no judgment from counts |
| 5.2 | What appears around the incident before filtering? | Evidence-derived UTC window over the **full** JSONL; show bounded chronological rows with `filestat` present and report type counts. On this run `filestat` is 302,947/310,364 (97.6%). Never dump the full timeline into notebook output. |
| 5.3 | What do non-`filestat` events add? | Visible in-notebook `data_type != 'fs:stat'` filter on the same frame; bounded log/journal/session events, parser, origin, raw line locator; pivot from earlier observations, not scenario answers. Filtering changes the view, not the preserved export. |
| 5.4 | What does the filesystem timeline show? | Visible `TZ=UTC mactime -b allocated.body` command, bounded to the observed window; keep unallocated bodyfile separate. Inspect multiline `mactime` rendering before filtering rows. TSK and Plaso `filestat` metadata share an origin but not all fields or precision. |
| 5.5 | How do the times fit together? | Juxtapose selected source-located events with RAM/disk acquisition intervals, the preload timestamp anomaly and Plaso year warnings. Leave the chronology interpretation and human-selected rows blank for ac after final review. |

### Section 6 — Result tables

Validate `FINDINGS`, render the four tables and the permitted counts. Code counts; the human judges.

### Section 7 — Ground-truth validation (part 4)

Compare the reconstruction with `command_log.jsonl` and the seven claims: agreements, discrepancies,
what forensics could not see, and prior knowledge disclosed. Ground truth is an experimental
reference, not a fourth evidence source.

## Test policy

The full policy is [RULES.md § Investigation implementation and delivery](../RULES.md#investigation-implementation-and-delivery).
In short: runner and orchestrator code keeps its tests; the investigation layer gets none beyond
the closed allowlist below, and verification is execution against real evidence under human review.

1. `sh()` — stdout/stderr separation, artifact naming, non-zero exit. *(Exists: `tests/test_forensics_sh.py`.)*
2. `root_fs()` — non-512-byte sector size honoured; ambiguous candidates raise.
3. `load_bodyfile()` — 11 fields parsed; a zero timestamp becomes NaT, not a 1970 event.
4. `resolve()` — one relative and one absolute symlink hop.
5. Findings validation — duplicate `(claim_id, source)` raises; unknown status raises.
6. Support rate — zero denominator renders "not calculable".

Fixtures are literal lines copied from real tool output in this repository. Never a synthetic disk
or memory image.

## Token discipline


- Never let an agent read `investigation.ipynb` as JSON. Extract cell sources with a script.
- Keep `.claudeignore` blocking raw evidence from file-reading tools; use filtered bash access.
- One stage per session. End every stage by replacing `Last handoff` below, at most 12 lines.
- Never two agents in the same file; supervisor and implementer work in turn, never at once.

## Last handoff

- 2026-11-06: primary checkout `main`, base `8fde9d4`, existing dirty work preserved; no commit.
- ac authorized presentation changes to FS01 in the Father run-local `investigation/investigation.md`.
- FS01 reduced from 108 to 64 lines: four named subsections, selected OS-release fields, one closing interpretation; duplicate root listing and repeated observations removed.
- Quoted the mount path and added the return to the investigation directory before later relative output paths; fixed the timezone code fence.
- Preserved recorded output values, supporting files and all report content outside FS01 byte-for-byte, including FS02 onward and the result tables.
- Checked Bash syntax, Markdown fence balance, scoped whitespace and excerpt provenance. No forensic commands or notebook replay; existing observations were reformatted, not reacquired.
- Output policy remains: short relevant output inline; long evidential output saved once; no separate routine setup transcripts.
- Next: ac reviews FS01's presentation. The approved FS03 access/activity and FS04 persistence/staging reorder remains a separate task; findings remain draft.
