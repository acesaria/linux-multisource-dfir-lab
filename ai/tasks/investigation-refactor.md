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

## State of play

Father is the reference run, `father-u22-20260913-01`, Ubuntu 22.04.

| | Status |
|---|---|
| `investigations/common/forensics.py` | Done. Frozen — no further refactoring until Father is complete. |
| `investigations/common/prepare.py` | Done: disk and ram stages. Timeline (Plaso) stage not written. |
| Notebook Sections 0–3 | Built and executed. |
| Section 4 | In progress, per the blueprint below. |
| Sections 5–7 | Not started. Section 5 needs the Plaso stage first. |
| Claim predicates | **Not written. Blocks Section 6.** Per claim, per source: what observation would establish it, and which sources are not applicable by nature. |
| Distro replicas, other scenarios | Not started. |

Deferred until Father is complete, deliberately: `sh()` has no timeout; `prepare.json` duplicates
evidence hashes already in `acquisition.json`; `prepare.py`'s tool inventory uses the wrong binary
names (`foremost`, `log2timeline.py`, `psort.py`, `vol` instead of `photorec`, `log2timeline`,
`psort`, `vol3`); the notebook's readability pass.

Dispatch: `ai/tasks/next.md` holds the one active prompt. It is replaced between tasks.

## Stages

Stages 0–3 are complete; their launch prompts are spent and live in git history. Stage 5's
remaining work is the Plaso timeline stage of `prepare.py`, which Section 5 depends on.

| Stage | State |
|---|---|
| 0 — clean start | Done. `main` is the only branch. |
| 1 — `forensics.py` | Done. Three parser defects found and corrected against real tool output. |
| 2 — `prepare.py` disk + ram | Done. Failure and emptiness are distinguished in `prepare.json`. |
| 3 — notebook Sections 0–1 | Done, then thinned from 643 to ~170 code lines. |
| 4 — findings and the four tables | Not started. Findings are written by hand in Section 6, from the observations in Sections 1–5, where those variables are still bound. Code counts, validates and renders; it never decides. |
| 5 — `prepare.py --stage timeline` | Not started. Measured on this run: default parsers, 8 min 34 s, 310,319 events — `filestat` 302,902, `syslog_traditional` 4,156, `systemd_journal` 3,156, `dpkg` 81, `utmp` 22, `apt_history` 2. `filestat` is 97.6% of the timeline and renders the same ext4 metadata TSK reads, so those rows are disk-origin under the independence rule. Three timelining warnings on `auth.log`, `kern.log`, `syslog` still need checking with `pinfo -v`. |
| 6+ — investigation | Sections 0–3 done, 4 in progress. |

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

Specification: [ext4-recovery-tools.md](../research/output/ext4-recovery-tools.md), 2026-09-21.
Three mechanically distinct techniques, attempted A → B → C. Target `/tmp/rk.so`, evidence-derived
from the journal lines recovered in 2.3. Every technique runs with `check=False`; a crash, timeout
or parse error is recorded as `tool failure`, never as evidence of erasure.

| Block | Technique | Question |
|---|---|---|
| 4.1 | **A — surviving metadata** | `fls -rd -p`, `ils -A -Z`, then `istat` and `icat -r` on one candidate inode. `fls -r` does not descend into deleted directories: the negative is bounded to that traversal. Demonstrates the cleared-extent limit rather than asserting it. |
| 4.2 | **B — journal export** | `istat` inode 8 for the journal length, `icat` inode 8 into `journal.bin`. No mount, no root. |
| 4.3 | **B — journal read** | `timeout -k 5s 120s debugfs -R "logdump -O -a -n <J> -f journal.bin"`, stdout and stderr separate. The installed 1.47.0 predates the 1.47.1 logdump loop fix, so the bound is required. Then `grep -abo` the exported journal for the target basename. A string hit is not a recovered directory record. |
| 4.4 | **B — reader cross-check** | `jls` on inode 8, `jcat` for one block debugfs also saw. TSK walks fixed legacy descriptor structures and may mis-decode modern JBD2 tags, so agreement, disagreement and failure are all reportable. |
| 4.5 | **C — ELF carving** | `photorec` scripted free-space ELF pass against the image directly. **Never `blkls`** — that export is 8.46 GB. A content match cannot identify the deleted path while an identical copy remains allocated. |
| 4.6 | **Outcomes** | One table: content recovered / partial / metadata or name trace only / no result in examined scope / tool failure / not attempted, with the locator of each raw output. |

**Excluded, do not run even where installed:** `ext4magic` (upstream discontinued 2024-09-30;
crashes reported in targeted listing mode), `extundelete` (fails with 64bit/metadata_csum),
`tsk_recover` (traverses filesystem objects, skips zero-size metadata — not a distinct mechanism),
`scalpel`, `bulk_extractor`, `foremost`. No mount is needed by any of the three techniques.

**Lesson for the remaining scenarios.** Make the deleted artifact something that does *not* survive
elsewhere on the filesystem — a unique script or payload, not a copy of an installed file —
otherwise recovery is unfalsifiable by construction and the recovery column stays empty.

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
