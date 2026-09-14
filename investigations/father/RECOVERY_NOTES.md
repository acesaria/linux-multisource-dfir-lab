# Deletion recovery — active investigation plan

Updated 2026-09-10. Recovery, journal reconstruction and targeted carving are
fully in scope. This implements the immutable RESULTS_PREVIEW.md tables;
no new methodology or metric selection is required. Brief source review and
installed-tool version checks are complete; fresh recovery tests are pending.

## Two complementary disk techniques, with an optional RAM complement

1. **Journal-assisted inode/directory reconstruction.** Inspect ext4 features,
   journal availability and historical inode/extent/directory records with
   read-only debugfs and ext4magic. Test an evidence-justified path/time window.
   Deleted-entry listing is preliminary; its empty output does not end recovery.
2. **Targeted carving of unallocated space.** Use PhotoRec against the extracted
   filesystem or a documented unallocated-space derivative, selecting relevant
   file families. Preserve candidate offsets and the allocation map. Validate
   structure, size and hashes; distinguish raw overlong candidates from bounded
   derivatives. Do not perform unrelated whole-disk carving for its own sake.
3. **Optional retained RAM content.** Examine justified mapped ELF or page-cache
   content using Volatility 3. Attribute this to RAM, never to disk recovery;
   it may supply complementary content or identity evidence.

Run standard commands through the notebook's existing output helper. Use only
small Python cells for identity checks, records and the locked table counts.
No custom carver, generic pipeline or bespoke recovery framework.

## What the current evidence already provides

Run: `father-u22-20260820-01`. Orientation output `data/06-fsstat.txt` records
Ext4, 4096-byte blocks, extents, 64-bit support and journal inode 8. Test actual
compatibility rather than assuming every historical recovery tool supports it.
Installed versions checked on 2026-09-10: ext4magic 0.3.2 / libext2fs 1.47.0;
PhotoRec 7.1; debugfs 1.47.0. Documentation version is not installed version.

Preserved material under `shared/investigations/father-u22-20260820-01/derived/disk/raw/`:

| Locator | Existing record, not a newly executed test |
|---|---|
| `13-fls-deleted-tmp.txt` | Prior deleted-entry examination; re-evaluate its scope |
| `19-extundelete.txt` | Actual double-free/corruption failure, exit 134 |
| `20-photorec-stdout.txt`, `21-recovery-candidates.json` | Prior ELF-only freespace attempt; one retained 10 MiB candidate, recorded matching 32,784-byte prefix |
| `22-recovered-rk.so.bin` | Preserved known-length derivative for independent validation |

A prior matching prefix is a concrete lead, not yet acceptance of a full file or
its original path. Recheck offsets, boundaries, raw candidate and hashes. The
known input size/hash is assisted validation and must be disclosed. Identical
installed-library bytes do not uniquely establish the deleted file instance.
Do not rerun the crashing method without a specific compatibility fix.

## Bounded practical test sequence

- Reuse the original images read-only. For filesystem-only tools, expose or
  extract the root filesystem at the recorded partition offset; do not write to
  evidence or replay its journal. Save recovery output on another filesystem.
- Inspect journal/feature compatibility and attempt the bounded journal method.
  Preserve an unavailable journal, unsupported feature or crash as such.
- Attempt targeted unallocated carving and inspect plausible candidates. Ensure
  an allocated surviving copy cannot silently be counted as the deleted instance.
- Compare optional RAM content only if it addresses a still-open claim.
- Stop each method after a documented bounded attempt; retain successful,
  partial, metadata-only, negative and failed results without forcing recovery.

## Representation in the locked tables

Table 1 receives only supported timestamps/events, with their semantics.
Table 2 receives S/P/U/N/A against each exact GT claim and notes on missing
content, identity, examined scope and failures. Proving deletion is different
from recovering content; assess those propositions explicitly.
Table 3 counts reviewed source/combined support and independent record origins.
Table 4 counts only validated relevant objects, deduplicating recovered copies.
A tool failure is not proof that nothing is recoverable; metadata is not content.

## Primary sources checked on 2026-09-10

- [ext4magic manual](https://ext4magic.sourceforge.net/manpage_en.html): journal-based recovery depends on retained metadata; supports path/inode and time-window selection.
- [PhotoRec documentation](https://www.cgsecurity.org/testdisk_doc/photorec.html): signature carving, unallocated-space mode, loss of original names and possible overlarge output.
- [Volatility 3 Linux plugins](https://volatility3.readthedocs.io/en/stable/volatility3.plugins.linux.html): existing toolbox reference for the optional RAM examination; verify local plugin syntax before testing.

These sources establish techniques, not guaranteed success on this acquired run.
