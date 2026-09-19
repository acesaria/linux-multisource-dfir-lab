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
6. `investigations/common/forensics.py` and `investigations/common/prepare.py`.
7. `investigations/father/investigation.ipynb` — Sections 0–3, for style and bound variables.

## Task: build Section 4 of the notebook, replacing its placeholder markdown

Deletion recovery. What the evidence already establishes, with its source — use these, and take
nothing from the scenario definition:

- The journal lines recovered in 2.3 name a path that was written and is no longer present:
  `/tmp/rk.so`, installed to the object path at 20:45:24. That is the recovery target, and it is
  evidence-derived, not assumed.
- 2.5 inventoried `/tmp` and `/dev/shm`: zero deleted entries were listed.
- The prepared `unallocated.body` holds ~33 unallocated inode records, and **every one has size 0** —
  ext4 clears block pointers and size on unlink. Inode-level content recovery is therefore expected
  to fail. Demonstrate that expected negative; do not skip it.
- The SHA-256 of the object extracted from disk in 1.5 is the validation reference for any
  recovered candidate.
- The session window from 2.1 and the command times from 2.3 bound every time range used below.

First, report tool availability on this host for `photorec`, `ext4magic`, `debugfs`, `blkls` and
`blkcalc`. `foremost` is known absent. If `photorec` is missing, say so and record block 4.4 as
`not attempted — tool unavailable`; do not install anything and do not substitute a carver.

Blocks:

- **4.1** Which deleted entries survive? Run `fls -rdp` over the directories of interest, and show
  the non-allocated rows of the prepared bodyfile. Cross-reference the unallocated inode records
  against the session window from 2.1 — an inode whose times fall inside that window is a candidate
  worth naming, even without a surviving filename.
- **4.2** Can content be recovered from a candidate inode? `istat`, then `icat -r`, then `file` and
  `sha256sum` on whatever comes out. Show the empty result when it is empty, with the byte count.
- **4.3** Does the ext4 journal recover the target path in a bounded window? Dump the journal with
  `debugfs`, then run `ext4magic` for `/tmp/rk.so` over a window justified by Sections 1–2. This
  needs a read-only mount with `noload`: mount, use, unmount in the same cell, and print the mount
  options used. If mounting requires a privilege you do not have, stop and report it.
- **4.4** Does carving recover it? Run `prepare.py --stage disk --with-unallocated` to produce the
  unallocated extract, carve it with `photorec` restricted to ELF, and map candidates back to
  blocks with `blkcalc`. Validate every candidate against the 1.5 SHA-256. Note the extract is
  multi-gigabyte; report its size before carving.
- **4.5** State the outcome of each attempt as exactly one of: content recovered, partial content
  recovered, metadata or name trace only, no result in examined scope, tool failure, not attempted.
  Present them in one small table, one row per attempt, with the locator of the raw output.

## Style, non-negotiable, matching Sections 0–3

- One block = one markdown question, one short code cell, one empty markdown cell reading
  `**Interpretation.** _(to write)_`. You do **not** write interpretations; the analyst does.
- Visible commands through `fx.sh`; bounded display via `tail=` or `fx.show`. Paths are relative to
  the case directory — the notebook has already `chdir`-ed.
- Do **not** create `Finding` objects anywhere. Findings are written by hand in Section 6.
- A negative result is a result. Never let an empty or failed recovery read as a bug, and never
  present absence of a trace as proof of erasure.
- No `raise` on an expected result. Print what was found, including zero.
- Keep each code cell under about 25 lines and each line under 100 characters.

## Scope and endpoint

Write scope: `investigations/father/investigation.ipynb` only. Do not touch `forensics.py`,
`prepare.py`, the ICM, or the other sections.

Write no tests. Verify by execution: restart the kernel, run Sections 0 through 4, and paste the
real output of each new block in your reply. If a block fails, paste the failure rather than
working around it.

Environment: `.venv/bin/python`; volatility is `vol3`. Do not commit. Keep the handoff in
`ai/tasks/investigation-refactor.md` to at most 12 lines.
