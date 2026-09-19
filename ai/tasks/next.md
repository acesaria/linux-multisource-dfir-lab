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
6. `investigations/common/forensics.py` — the helpers you must reuse.
7. `investigations/father/investigation.ipynb` — Sections 0–2, for style and for the variables
   already bound.

## Task: build Section 3 of the notebook, replacing its placeholder markdown

The RAM baseline is already prepared: `investigation/prepared/raw/*.json` holds banners, pslist,
psaux, pstree, proc.Maps, lsof, sockstat, lsmod and kmsg. Load those with `fx.load_vol` instead of
re-running vol3. Only plugins absent from that set are run inline with `fx.sh`.

Useful pivots already established by the evidence, with their sources — use these, do not invent
others and do not take anything from the scenario definition:

- the object path and its inode, from Section 1 (`PRELOAD_OBJECT_PATH`, `object_inode`)
- the SHA-256 of the object extracted from disk, from 1.5
- strings inside the object, from `investigation/output/s1-05-object-strings.txt`:
  `AUTHENTICATE:`, `lobster`, `Enjoy the shell!`, `/proc/net/tcp`, `/tmp/silly.txt`
- the session account and window, from 2.1; the sshd restart time, from 2.3

Blocks:

- **3.1** Does the image match the symbols? Show the prepared banners result.
- **3.2** What processes existed, and how are they related? `pstree` and `psaux` from the prepared
  JSON; bounded view.
- **3.3** Which processes map the object found in Section 1? Filter `proc.Maps` by the object path
  observed there, never a path you typed. Count distinct PID + path pairs, not mapping rows.
- **3.4** Is `LD_PRELOAD` present in any process environment? Run `linux.envars` inline. A negative
  is the expected result for a file-based preload and must be reported as a result, not a failure.
- **3.5** Which endpoints were open at capture? Show `sockstat` and `lsof` from the prepared JSON in
  full first, then attribute the ones belonging to the processes from 3.3. The object reads
  `/proc/net/tcp`, so state explicitly that a connection hidden from the live host may still appear
  in memory structures.
- **3.6** Does memory hold shell history the disk does not? Run `linux.bash` inline for the relevant
  PIDs. Section 2.4 found no history file on disk, so this is the cross-source test.
- **3.7** Can the object be recovered from memory? Run `linux.elfs` with `--dump` for a mapping PID,
  then `sha256sum` the result and compare it with the disk copy from 1.5. Equality and inequality
  are both meaningful — a memory-reconstructed ELF need not match the on-disk file byte for byte.
- **3.8** Are kernel-level mechanisms clean? Run `linux.malware.check_syscall`,
  `linux.malware.modxview` and `linux.ebpf` inline, plus the prepared `lsmod` and `kmsg`. Valid zero
  rows are a result; these negatives are the baseline the kernel scenarios are compared against.

## Style, non-negotiable, matching Sections 0–2

- One block = one markdown question, one short code cell, one empty markdown cell reading
  `**Interpretation.** _(to write)_`. You do **not** write interpretations; the analyst does.
- Visible commands through `fx.sh`; bounded display via `tail=` or `fx.show`. Paths are relative to
  the case directory — the notebook has already `chdir`-ed.
- Do **not** create `Finding` objects anywhere. Findings are written by hand in Section 6.
- Enumerate before selecting. Never grep for a name, port or path taken from the scenario
  definition; find it in the evidence and say where it came from.
- No `raise` on an expected result. Print what was found, including zero.
- Keep each code cell under about 25 lines and each line under 100 characters. If a cell needs
  more, it is doing two things.

## Scope and endpoint

Write scope: `investigations/father/investigation.ipynb` only. Do not touch `forensics.py`,
`prepare.py`, the ICM, or the other sections.

Write no tests. Verify by execution: restart the kernel, run Sections 0 through 3, and paste the
real output of each new block in your reply. If a block fails, paste the failure rather than
working around it.

Environment: `.venv/bin/python`; volatility is `vol3`. Expect 15–20 minutes for the inline plugins.
Do not commit. Keep the handoff in `ai/tasks/investigation-refactor.md` to at most 12 lines.
