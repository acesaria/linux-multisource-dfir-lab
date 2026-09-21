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
5. `investigations/common/forensics.py`.
6. `investigations/father/investigation.ipynb` — Sections 0–3 for style and bound variables, and
   Section 4, which you are replacing.

## Task: replace Section 4 entirely

Three techniques, unchanged: surviving metadata, journal-assisted reconstruction, signature
carving. What changes is that journal reconstruction now goes all the way to content instead of
stopping at a string match. Delete the current Section 4 cells and write the seven blocks below.
Do not touch Sections 0–3 or 5–7.

**KISS is the hard requirement of this task.** The previous Section 4 was rejected for being
elaborate. Plain procedural code. No helper functions, no classes, no candidate-scoring logic, no
DataFrames except the 4.7 table. Every code cell under 25 lines and every line under 100
characters — a cell that needs more is doing two things. Prefer one clear `print` over a
formatted display. Run every tool with `check=False`: a crash, timeout or parse error is recorded
as `tool failure`, never allowed to abort the notebook, never reported as evidence of erasure.

Target: `/tmp/rk.so`, evidence-derived from the journal lines recovered in 2.3.

### 4.1 — do deleted directory entries survive under `/tmp`?

`fls -rd -p` on the `/tmp` inode, showing only regular-file rows. Then `ils -A -Z` once, and print
how many unallocated inode records exist and how many have size 0. That is the whole block: it
establishes that ext4 clears size and the extent tree on unlink, so ordinary undelete stops here.
No candidate selection, no `icat -r` on a directory inode.

### 4.2 — export the journal

`istat` on inode 8 for the length, then `icat` inode 8 into `investigation/data/journal.bin`.
Print the size in bytes and in 4096-byte blocks. Unchanged from the current block; keep it minimal.

### 4.3 — do old directory blocks in the journal name the file?

`timeout -k 5s 120s debugfs -R "logdump -O -a -n <blocks> -f journal.bin"` from the data
directory, stdout and stderr captured separately. **`logdump: short read (read 0, expected 4096)`
is logdump reading one block past the end of the export — an expected terminal condition, not a
failure.** Report stderr as a fact; judge the outcome by whether the traversal completed.

Then `grep -aboF` the target basename in `journal.bin`, and for each hit read the 8 bytes before
the name and unpack `<IHBB` as an `ext4_dir_entry_2` header: inode, `rec_len`, `name_len`,
`file_type`. Print inode, rec_len, name_len, file_type, name and journal block (`offset // 4096`),
plus the entry immediately preceding it in the same block. Validate that `name_len` equals the
name's length. Print whether the recovered inode matches any inode established in Sections 1–2.

### 4.4 — does the journal hold pre-unlink copies of the inode itself?

The journal stores old metadata blocks, so the inode-table block holding the recovered inode is
likely in it several times. Locate it arithmetically from the prepared `fsstat` — do not hardcode:

```
group        = (inode - 1) // inodes_per_group
index        = (inode - 1) %  inodes_per_group
fs_block     = <group's Inode Table start> + (index * inode_size) // block_size
offset_in_bl = (index * inode_size) %  block_size
```

`inodes_per_group`, `Inode Size` and `Block Size` are in the prepared fsstat output; the group's
`Inode Table: START - END` is in that group's section. Find every
`FS block <fs_block> logged at journal block N` in the logdump index, read each of those journal
blocks at `offset_in_bl`, and decode the 256-byte inode: `<HHI` at 0 for mode, uid, size_lo;
`<IIII` at 8 for atime, ctime, mtime, dtime; `<H` at 26 for links_count; `<HHHH` at 40 for the
extent header (magic must be `0xF30A`, depth 0), then `<IHBBI`-style entries at 52 + 12*k as
`<IHHI` giving logical block, length, start_hi, start_lo. An `ee_len` above 32768 marks an
uninitialized extent: subtract 32768 for the true length.

**Print every distinct version**, deduplicated, oldest journal block first: mode, size, links,
mtime, dtime, extent list, and how many copies carry it. The sequence of versions is the point —
do not filter to one. Keep the whole block under 25 lines.

### 4.5 — recover content from the recovered extent map

Take the version from 4.4 that has a non-zero size and a valid extent list. `blkcat` its blocks
from the **image** (not the journal), trim to the recovered size, then `file` and `sha256sum` the
result and compare against the SHA-256 of the object extracted in 1.5. Print both hashes and
whether they match.

State in the block that the blocks may have been reallocated between unlink and imaging, so a
mismatch is `partial content recovered` or `no result in examined scope`, and the name, size,
timestamps and block map from 4.3–4.4 stand either way.

### 4.6 — signature carving from free space

Print `photorec --version` first. Read the partition number from PhotoRec's own listing for the
image; do not guess it and do not substitute the TSK sector offset. Run the scripted free-space
ELF form with **stdout and stderr redirected to a log file** — PhotoRec's progress output floods
the notebook otherwise. Print only: version, exit status, candidate count, total output size, and
whether any candidate matches the 1.5 SHA-256. Never run `blkls`; never convert the image.

### 4.7 — outcomes

One small table, one row per technique: content recovered / partial content recovered / metadata
or name trace only / no result in examined scope / tool failure / not attempted, with the locator
of the raw output. `tool failure` is only for a tool that could not complete.

## Style and endpoint

Interpretation cells stay `**Interpretation.** _(to write)_` — you do not write them. No `Finding`
objects; findings are written by hand in Section 6. Visible commands through `fx.sh`, plain
`print` for derived values. Paths are relative to the case directory; the notebook has `chdir`-ed.

Write scope: `investigations/father/investigation.ipynb` only. Write no tests. Restart the kernel,
run Sections 0–4, and paste the real output of every new block in your reply. Environment:
`.venv/bin/python`. Do not commit. Keep the handoff in `ai/tasks/investigation-refactor.md` to at
most 12 lines.
