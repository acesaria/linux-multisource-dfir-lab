# Next task

The single active prompt. Follow it exactly and stop at its endpoint. This file is replaced
between tasks; ignore any memory of earlier versions.

---

This is a **research** task under `ai/research/CONTEXT.md`. You produce one document. You do not
touch the notebook, you do not run forensic tools, and you do not modify any code.

Read, in this order, and nothing else:

1. `AGENTS.md`
2. `ai/CONTEXT.md` — routing. You are in the Research stage.
3. `ai/research/CONTEXT.md`
4. `ai/RULES.md`, section "Investigation implementation and delivery".

## Question

Which file-recovery techniques are worth attempting on **ext4**, in an offline post-mortem
examination of an acquired disk image, for a thesis that must show both successes and honest
failures?

## The concrete case these techniques must be judged against

- Filesystem: ext4 on Ubuntu 22.04 (cloud image), 4096-byte blocks, journal present at inode 8.
- Evidence: an EWF (E01) acquisition of a 10 GB logical disk, examined offline. The examiner host
  has The Sleuth Kit 4.15.0, libewf 20240506, `debugfs` 1.47.0, `ext4magic` 0.3.2, `mactime`,
  Python 3.12. `foremost` is not installed. Mounting is possible but needs root.
- Target: `/tmp/rk.so`, a ~32 KB shared object written at 20:45:24 UTC and unlinked at 20:46:30 UTC,
  about 8 seconds before memory capture and 68 seconds before disk imaging began.
- Already established by examination, and these are the hard constraints:
  - `fls -rd` over `/tmp` lists **zero** surviving deleted directory entries.
  - The filesystem has ~33 unallocated inode records and **every one has size 0** — ext4 clears
    block pointers and size on unlink.
  - There are 2,065,546 free blocks, about **8.5 GB** of unallocated space.
  - A byte-identical copy of the deleted file's content **remains allocated** elsewhere on the same
    filesystem, so any content-only recovery cannot by itself establish the deleted path.

## What to produce

A shortlist of **three to four techniques**, each mechanically distinct — not three tools that do
the same thing. Consider at least these families, and say for each whether it earns a place:

- directory-entry and inode enumeration (`fls -rd`, `ils`, the bodyfile)
- whole-filesystem recovery of unallocated content (`tsk_recover -e`, and what it actually does)
- journal-assisted recovery (`ext4magic`, `jls`/`jcat`, `debugfs logdump`, `extundelete`)
- carving from unallocated space (`photorec`, `scalpel`, `bulk_extractor`)
- anything else genuinely used in current Linux DFIR practice that we have missed

For **each** technique in your shortlist, give:

| Field | What it must say |
|---|---|
| Mechanism | What it reads and what it reconstructs — metadata, name, content, or block ranges |
| Invocation | The exact command form against an E01 or a raw image, with the arguments that matter |
| Requirements | Raw image or E01-aware? Mount needed? Root? How much scratch space does it write? |
| Expected behaviour here | Given zeroed inodes, a 68-second gap, and 8.5 GB unallocated — what should happen, and why |
| What success proves | And, precisely, what it does **not** prove |
| What failure demonstrates | A negative result must still be worth reporting in a thesis |
| Maintenance status | Last release or commit, whether it builds on a current Debian/Ubuntu, known breakage |

## Rules for this research

- **Verify the maintenance status of every tool** and cite where you checked. Earlier attempts in
  this project were wasted on tools that are no longer maintained and crashed. If you cannot browse
  to confirm, mark the status `unverified` explicitly rather than guessing — an unverified claim
  here costs the project a day.
- Prefer techniques that need no mount, or state plainly when a read-only `noload` mount is
  unavoidable.
- Flag anything that would require exporting or writing multiple gigabytes, with the figure.
- Rank the shortlist by what is most worth showing in a thesis chapter, and say why. A technique
  that fails for an instructive, explainable reason may rank above one that succeeds trivially.
- Cite a source for each factual claim about tool behaviour: man page, upstream documentation, or
  repository.

## Output

Write `ai/research/output/ext4-recovery-tools.md`: the comparison table above, a short paragraph per
technique, and a final recommendation of which three or four to attempt and in what order. Nothing
else is created or modified.

Then stop. The experimental trial is a separate task.
