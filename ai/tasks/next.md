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
5. `ai/research/output/ext4-recovery-tools.md` — **the specification for this task.** Its command
   forms, exclusions and caveats are binding.
6. `investigations/common/forensics.py`.
7. `investigations/father/investigation.ipynb` — Sections 0–3, for style and bound variables.

## Task: build Section 4 of the notebook, replacing its placeholder markdown

Three mechanically distinct recovery techniques, attempted in the order A → B → C from the research
document, against the deleted target `/tmp/rk.so` (evidence-derived: named in the journal lines
recovered in 2.3, installed to the object path at 20:45:24 and absent from the filesystem).

**Every technique must complete or fail gracefully.** Use `check=False`. A crash, timeout or parse
error is recorded as `tool failure`, never allowed to abort the notebook, and never reported as
evidence of erasure. That tolerance is the point of this section.

Parameter bindings for this run — do not invent others:
`FMT=ewf`, `SECTOR=512`, `OFF=227328` (already bound as `ROOT_OFFSET`), image already bound as
`IMG`, outputs to `OUT` and `DATA`. Resolve the `/tmp` inode from the evidence.

### Blocks

- **4.1 — A, surviving metadata.** `fls -rd -p` under `/tmp`, then `ils -A -Z` over the filesystem.
  Note in the block that `fls -r` does not descend into deleted directories, so the negative is
  bounded to that traversal. Then pick one unallocated inode whose times fall inside the session
  window from 2.1, run `istat` on it, and run `icat -r` on it, printing the byte count returned.
  That demonstrates the cleared-extent limit instead of asserting it.
- **4.2 — B, export the journal.** `istat` on inode 8 to establish the journal length, print it in
  bytes and in 4096-byte blocks (this is `JOURNAL_BLOCKS`), then `icat` inode 8 into
  `DATA/journal.bin`. Print the exported size. Do **not** export unallocated space.
- **4.3 — B, read the journal with debugfs.** From the output directory, run
  `timeout -k 5s 120s debugfs -R "logdump -O -a -n $JOURNAL_BLOCKS -f journal.bin"`, capturing
  stdout and stderr separately. The installed 1.47.0 predates the 1.47.1 logdump loop fix, so the
  timeout is required; report the exit status and inspect stderr even on exit 0. Do not add `-S`,
  `-b` or `-i` to this standalone form. Then search the index and the exported journal bytes for
  the target basename and report every hit with its offset — `grep -abo` over `journal.bin` is
  enough. A bare string hit is **not** a recovered directory record; say so in the block.
- **4.4 — B, cross-check with the TSK journal readers.** `jls` on inode 8, and `jcat` for one
  journal block also seen by debugfs. Compare what the two readers report for the same block.
  TSK's journal code walks fixed legacy descriptor structures and may mis-decode modern JBD2 tags,
  so agreement, disagreement and outright failure are all reportable outcomes. Print the comparison
  plainly.
- **4.5 — C, ELF carving from free space.** First report whether `photorec` exists on this host; if
  it does not, record the technique `not attempted — tool unavailable` and skip the rest of the
  block without installing anything. If it exists, run the scripted free-space ELF form from the
  research document against the image directly. **Do not run `blkls`** — the export is 8.46 GB and
  the research recommends against it. Report the candidate count and total output size, and compare
  every candidate against the SHA-256 of the object extracted in 1.5. State that a content match
  cannot identify the deleted path, because an identical copy remains allocated.
- **4.6 — outcomes.** One small table, one row per technique, each outcome exactly one of: content
  recovered, partial content recovered, metadata or name trace only, no result in examined scope,
  tool failure, not attempted — plus the locator of the raw output for each.

### Explicitly excluded — do not run, even though some are installed

`ext4magic` (upstream discontinued; crashes reported even in targeted listing mode),
`extundelete` (documented failures with 64bit/metadata_csum), `tsk_recover` (traverses filesystem
objects and skips zero-size metadata — not a distinct mechanism here), `scalpel`,
`bulk_extractor`, `foremost`. Do not install any package. Do not mount anything: none of the three
techniques needs a mount.

## Style, non-negotiable, matching Sections 0–3

- One block = one markdown question, one short code cell, one empty markdown cell reading
  `**Interpretation.** _(to write)_`. You do **not** write interpretations.
- **Forensic output first, presentation last.** Show the tool's own output through `fx.sh` with
  `tail=`, and use plain `print` for anything derived. Do **not** build DataFrames to display text,
  status, sizes or scope statements. The only DataFrame in this section is the 4.6 outcomes table.
- Paths are relative to the case directory — the notebook has already `chdir`-ed.
- Do **not** create `Finding` objects. Findings are written by hand in Section 6.
- No `raise` on an expected result. Print what was found, including zero and including failure.
- Keep each code cell under about 25 lines and each line under 100 characters.

## Scope and endpoint

Write scope: `investigations/father/investigation.ipynb` only.

Write no tests. Verify by execution: restart the kernel, run Sections 0 through 4, and paste the
real output of each new block in your reply, including any failure text. Environment:
`.venv/bin/python`. Do not commit. Keep the handoff in `ai/tasks/investigation-refactor.md` to at
most 12 lines.
