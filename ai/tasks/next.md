# Next task

The single active prompt. Follow it exactly and stop at its endpoint. This file is replaced
between tasks; ignore any memory of earlier versions.

---

Read, in this order, and nothing else:

1. `AGENTS.md`
2. `ai/CONTEXT.md` — routing. You are in the supervised "Forensics" stage.
3. `ai/forensic/CONTEXT.md`
4. `ai/RULES.md`, sections "Findings and manual assessment" and
   "Investigation implementation and delivery".
5. `ai/tasks/investigation-refactor.md`, sections "Environment" and "Father notebook blueprint".
6. `investigations/common/forensics.py`.
7. `investigations/father/investigation.ipynb` — Sections 0–3, for style and bound variables.

## Task: build Section 4 of the notebook, replacing its placeholder markdown

Deletion recovery, deliberately scoped to **name and metadata traces**. Content carving is
excluded for a stated reason, not skipped — block 4.4 makes that argument explicitly.

What the evidence already establishes, with its source. Take nothing from the scenario definition:

- The journal lines recovered in 2.3 name a path that was written and is no longer present:
  `/tmp/rk.so`, installed to the object path at 20:45:24. Evidence-derived, not assumed.
- 2.5 inventoried `/tmp` and `/dev/shm`: zero deleted entries listed.
- The prepared `unallocated.body` holds ~33 unallocated inode records and **every one has size 0** —
  ext4 clears block pointers and size on unlink.
- The prepared `fsstat` reports 2,065,546 free blocks at 4096 bytes: roughly 8.5 GB unallocated.
- The object still allocated at the path from Section 1 is byte-identical in content to whatever
  `/tmp/rk.so` held, and its SHA-256 from 1.5 is on record.
- The session window from 2.1 and the command times from 2.3 bound every time range used below.

Report tool availability on this host for `debugfs` and `ext4magic` before starting. Do not install
anything.

Blocks:

- **4.1** Which deleted names survive? `fls -rdp` over the directories named in the logs, plus the
  non-allocated rows of the prepared bodyfile. State the scope searched. Zero surviving names is a
  bounded negative about those directories, never proof of erasure.
- **4.2** What do the unallocated inode records carry? Cross-reference their times against the
  session window from 2.1 and list any whose times fall inside it — a candidate worth naming even
  with no surviving filename. Run `istat` on one such candidate and then `icat -r` on it, and show
  the resulting byte count, so the size-0 consequence is demonstrated rather than asserted.
- **4.3** Does the ext4 journal retain a name or inode for the target path? Dump the journal
  (inode 8) with `debugfs`, report its size, then run `ext4magic` for `/tmp` over a window justified
  by Sections 1–2. Report the **names and inodes** recovered, not file content. This needs a
  read-only mount with `noload`: mount, use and unmount in the same cell, print the mount options,
  and if mounting needs a privilege you do not have, stop and report that.
- **4.4** Why content carving is not attempted. One short cell that prints, from the prepared
  products, the free-block count and its size in bytes, and the 1.5 SHA-256 of the still-allocated
  object. Then a markdown cell — which you DO write, because it is a methodological argument and not
  an interpretation of evidence — stating: carving ~8.5 GB of unallocated space for bytes identical
  to a file that remains allocated cannot distinguish the deleted instance from the surviving one,
  so a matching carve could not establish the deleted path; the attempt is recorded as
  `not attempted` with this reason. Do not run `blkls`, `photorec` or any carver.
- **4.5** One small table, one row per attempt, each outcome exactly one of: content recovered,
  partial content recovered, metadata or name trace only, no result in examined scope, tool failure,
  not attempted — with the locator of the raw output for each.

## Style, non-negotiable, matching Sections 0–3

- One block = one markdown question, one short code cell, one empty markdown cell reading
  `**Interpretation.** _(to write)_`. The only exception is the argument cell in 4.4.
- Visible commands through `fx.sh`; bounded display via `tail=` or `fx.show`. Paths are relative to
  the case directory — the notebook has already `chdir`-ed.
- Do **not** create `Finding` objects anywhere. Findings are written by hand in Section 6.
- A negative result is a result. Never let an empty recovery read as a bug, and never present
  absence of a trace as proof of erasure.
- No `raise` on an expected result. Print what was found, including zero.
- Keep each code cell under about 25 lines and each line under 100 characters.

## Scope and endpoint

Write scope: `investigations/father/investigation.ipynb` only. Do not touch `forensics.py`,
`prepare.py`, the ICM, or the other sections.

Write no tests. Verify by execution: restart the kernel, run Sections 0 through 4, and paste the
real output of each new block in your reply. If a block fails, paste the failure rather than
working around it.

Environment: `.venv/bin/python`. Do not commit. Keep the handoff in
`ai/tasks/investigation-refactor.md` to at most 12 lines.
