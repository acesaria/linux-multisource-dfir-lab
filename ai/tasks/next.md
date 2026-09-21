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
5. `ai/research/output/ext4-recovery-tools.md` — binding specification.
6. `investigations/common/forensics.py`.
7. `investigations/father/investigation.ipynb` — Sections 0–4.

## Task: correct Section 4. Four defects, no restructuring

Section 4 runs and its techniques are right. Four blocks are wrong. Change only those, keep every
other cell as it is, and do not touch Sections 0–3 or 5–7.

### 4.1 — the candidate inode selection is wrong

It selected `258116`, `258117`, `258122`, `258123`: all `drwx------` snap-private-tmp
**directories**, and ran `icat -r` on one. That is meaningless for content recovery.

Fix two things:
- Select only **regular-file** inodes from the `ils` output (mode `644`/`755`, not `700`/`1777`).
- Widen the window from the end of the session to **the start of disk acquisition**. The current
  window ends at 20:46:30 and so excludes inode `74309`, whose crtime is `1789332348` = 20:45:48 —
  the moment `write_preload` ran in the 2.3 journal lines. That inode is the interesting candidate.

Run `istat` and `icat -r` on the regular-file candidate and print the byte count, as now.

### 4.2 — unchanged

### 4.3 — the classification is wrong and the block stops one step too early

`debugfs` exited 0, traversed the whole journal and reached `tag TAIL`. The message
`logdump: short read (read 0, expected 4096) while reading journal` is logdump reading one block
past the end of the 64 MiB export: an expected terminal condition, **not** a tool failure. Treat a
non-empty stderr as a fact to report, never as the outcome by itself.

The `grep -aboF` already returns five hits for the target basename in `journal.bin`. A string hit
is not evidence. Add a short decode step: for each hit, read the 8 bytes **before** the name and
unpack them as an `ext4_dir_entry_2` header — `<IHBB` giving inode, `rec_len`, `name_len`,
`file_type` — then print inode, rec_len, name_len, file_type, name and the journal block number
(`offset // 4096`). Also decode the entry immediately preceding it in the same block, so the
containing directory is visible. Validate: `name_len` must equal the name's length and
`file_type` 1 means a regular file. Print the table plainly; no DataFrame.

Then compare the recovered inode number against the inodes already established in Sections 1 and 2
and print whether it matches any of them. Do not write what that means — that is the analyst's.

### 4.4 — the cross-check is vacuous

It compared journal **block 0**, the journal superblock, so the matching hashes prove nothing.
Select instead a block that the debugfs output names as a **descriptor block** — parse
`at block N` from lines beginning `Dumping descriptor block` in the saved index, and take the first
one. Compare `jcat` against `blkcat` for that block, and report agreement, disagreement or failure.

### 4.5 — re-run PhotoRec

The previous run used PhotoRec 7.1 without libewf support, hence
`Unable to open file or device`. A newer build is now installed: print `photorec --version` first.
The partition number `1` was guessed — run PhotoRec's listing for the image and take the number it
displays for the ext4 partition; do not assume, and do not substitute the TSK sector offset. If it
still cannot open the E01, record `tool failure` with the exact message and stop; do not convert
the image and do not run `blkls`.

### 4.6 — re-derive the outcomes table

From the corrected blocks. The six values are unchanged. A completed examination that found no
usable result is `no result in examined scope`; `tool failure` is reserved for a tool that could
not complete.

## Style

Unchanged from Sections 0–3: visible commands through `fx.sh`, plain `print` for derived values,
the 4.6 table the only DataFrame, interpretation cells left as
`**Interpretation.** _(to write)_`, no `Finding` objects, cells under 25 lines, lines under 100
characters.

## Scope and endpoint

Write scope: `investigations/father/investigation.ipynb` only. Write no tests. Restart the kernel,
run Sections 0–4, and paste the real output of 4.1, 4.3, 4.4, 4.5 and 4.6 in your reply.
Environment: `.venv/bin/python`. Do not commit. Keep the handoff in
`ai/tasks/investigation-refactor.md` to at most 12 lines.
