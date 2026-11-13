# Offline ext4 recovery: a bounded shortlist

Research checked **2026-09-21**. No forensic tools were executed, packages built or installed, or evidence examined for this document. The case facts below are supplied constraints, not new findings. Commands are proposed forms for the separate experimental task.

**Recommend three techniques: surviving-metadata examination, journal-assisted reconstruction, and unallocated-space ELF carving.** They inspect current metadata, historical metadata, and content signatures respectively. Do not count multiple readers of the same journal as separate techniques or independent corroboration. Exclude bulk filesystem export as a separate recovery method, and do not spend another trial on abandoned journal-recovery programs.

## Case and interpretation limits

The supplied case is an offline E01 acquisition of a 10 GB logical disk containing Ubuntu 22.04/ext4, with 4,096-byte blocks and an internal journal at inode 8. `/tmp/rk.so`, approximately 32 KB, was written at 20:45:24 UTC and unlinked at 20:46:30 UTC. Memory capture followed about eight seconds later; disk imaging began 68 seconds after unlink. Examination has already found no surviving deleted directory entries under `/tmp`, approximately 33 unallocated inode records all with size zero, and 2,065,546 free blocks. A byte-identical copy remains allocated elsewhere.

The free-block count represents **8,460,476,416 bytes = 8.46 GB = 7.88 GiB**. Reading that space and exporting that space are different costs. A small target does not make a whole-volume scan small.

The 68-second interval is not a retention guarantee, an overwrite measurement, or the time every sector was acquired. Ext4 normally journals metadata rather than file payload; journal transactions eventually give way to newer transactions. A short interval therefore justifies examining the journal, but does not establish that a useful pre-unlink inode version survives. The journal mode, feature flags, retained transactions, block reuse and discard effects remain unverified for this research. [Kernel journal documentation](https://www.kernel.org/doc/html/latest/filesystems/ext4/journal.html)

## Comparison, ranked by thesis value

The invocation cells refer to the complete command forms immediately below. Expected outcomes are **case-specific inferences**, not predicted verdicts.

| Field | Rank 1: journal-assisted reconstruction | Rank 2: surviving directory/inode metadata | Rank 3: unallocated-space ELF carving |
|---|---|---|---|
| Mechanism | Read historical directory and inode-table blocks in JBD2; establish a name-to-inode relationship, recover old extent mappings, then extract surviving payload blocks. Journal inspection alone may yield only metadata. [Journal format](https://www.kernel.org/doc/html/latest/filesystems/ext4/journal.html), [extent format](https://www.kernel.org/doc/html/latest/filesystems/ext4/ifork.html) | Enumerate present directory records and unallocated inode metadata; inspect any remaining size and extent addresses. A bodyfile renders these records for a timeline; it does not reconstruct missing bytes. [fls](https://www.sleuthkit.org/sleuthkit/man/fls.html), [ils](https://www.sleuthkit.org/sleuthkit/man/ils.html), [mactime](https://www.sleuthkit.org/sleuthkit/man/mactime.html) | Use ext4 allocation information to select free space, then recognize ELF headers independently of deleted inode pointers. Output is a candidate byte sequence and location, without the original pathname. [PhotoRec](https://www.cgsecurity.org/testdisk_doc/photorec.html) |
| Invocation | B: `icat … 8`, then `debugfs -R 'logdump … -f …'`; extract selected journal and filesystem blocks with `blkcat`. `jls`/`jcat` are qualified alternate readers. | A: `fls -rd …`, `ils -A -Z …`, `ils -m …`, and targeted `istat`/`icat -r` only if a useful inode is identified. | C: `photorec /log /d … /cmd … '…,elf,enable,freespace,search'`. |
| Requirements | TSK reads E01 when built with EWF support; debugfs reads an exported raw journal, or a raw filesystem image. Preferred journal-file route needs **no mount and no root**. Writes journal size **J**, an index and selected 4 KiB blocks; J is unknown until inode 8 is inspected. | E01-aware TSK or raw image; **no mount/root** for readable image files. Small text outputs for the supplied scope; optional block extracts are 4 KiB each. | E01 support is build-dependent; raw images also work. **No mount/root** for image files. Reads about **8.46 GB** of free blocks plus metadata. No mandatory free-space export, but recovered output can still occupy **multiple GB**; provision roughly **8.5 GB plus overhead** for a complete pass, not 32 KB. |
| Expected behaviour here | Potentially the only shortlisted route to connect recovered content to the deleted path. Zeroed current inodes do not rule out older journal copies. Expect uncertainty: neither pre-unlink mappings nor untouched payload are guaranteed. | The given enumeration already has an instructive negative outcome: no deleted `/tmp` entry and no usable size/block mapping in the reported records. More timeline formatting cannot restore them. | Zeroed inode pointers do not prevent signature detection. A complete contiguous remnant might be recovered, but fragmentation, overwrite, discard or over-carving can prevent an exact file. The allocated duplicate must be excluded by the free-space selection. |
| What success proves | A validated historical directory record can support a historical name/inode association. Adding a coherent old extent mapping and matching bytes can support recovery of that file version. It does **not** alone prove execution, an exact unlink time, or authenticity of every recovered byte. | A valid deleted entry establishes a surviving name/inode trace; a mapped extraction can establish content at that inode. An inode timestamp without a name does **not** establish `/tmp/rk.so`; a bodyfile is not independent evidence. | A validated match located in free blocks establishes that matching content survives there in this acquisition. It does **not** identify `/tmp/rk.so`, its deletion time, or execution. Even a full hash match cannot distinguish historical copies with identical content. |
| What failure demonstrates | A completed, compatible examination can report no usable historical mapping within specified journal blocks/transactions. Missing mapping, missing payload and parser failure are different outcomes. A crash or timeout is **tool failure/incomplete examination**, not evidence of erasure. | Documents the limit of ordinary metadata-based undelete under the observed zeroed-inode conditions. It does not establish that the payload blocks were overwritten or that no historical directory record exists elsewhere. | A completed free-space pass with a stated ELF configuration found no validated target candidate. This does not prove secure deletion or exclude fragments, allocated/slack remnants, or recoverability by another method. |
| Maintenance status | e2fsprogs is maintained; latest verified release **1.47.4, 2026-03-06**. Installed **1.47.0** predates a documented logdump loop fix in **1.47.1**. Use the timeout below; prefer a fixed build for the trial. ext4magic/extundelete are excluded for the reasons in the maintenance table. [Release notes](https://e2fsprogs.sourceforge.net/e2fsprogs-release.html) | TSK **4.15.0, 2026-04-15**, is the latest verified release and matches the supplied host version. Current Debian builds exist; the journal reader has a separate compatibility limitation below. [Release](https://github.com/sleuthkit/sleuthkit/releases/tag/sleuthkit-4.15.0), [Debian](https://packages.debian.org/trixie/sleuthkit) | PhotoRec/TestDisk **7.2, 2024-02-22**, remains the stable release; **7.3** is development/beta. Current Linux binaries and Debian packages exist. ELF boundary limitations are documented below. [Downloads](https://www.cgsecurity.org/wiki/TestDisk_Download), [Debian](https://packages.debian.org/trixie/testdisk) |

## Command parameters and image access

These are parameterized commands, not ready-to-run case commands. The brief does not supply the image pathname, partition offset, sector size, `/tmp` inode, acquisition date, or PhotoRec partition number. Do not invent them or use today's date for the historical event.

| Parameter | Binding required before a trial |
|---|---|
| `IMAGE`, `FMT` | Absolute first E01 segment and `ewf`, or absolute raw disk image and `raw`. All EWF segments must be available. TSK's EWF support must exist in the selected build. |
| `SECTOR`, `OFF` | Actual device-sector size in bytes and ext4 start offset **in those sectors**; these are not the 4,096-byte filesystem block size. For a filesystem-only raw image, `OFF=0`. |
| `OUT` | Existing, writable, run-local derived-output directory, separate from evidence. Use fresh output names and retain command, version, stdout, stderr and exit status. |
| `TMP_INODE`, `INODE` | Examined `/tmp` inode and, only if established, a candidate deleted-file inode. |
| `JOURNAL_BLOCKS`, `JBLOCK` | Journal byte length divided by 4,096, and a selected **journal-relative** block number. |
| `FS_BLOCK`, `BLOCK_COUNT` | A validated filesystem block address and contiguous block count; journal block numbers are not interchangeable with filesystem block numbers. |
| `PC_PART`, `PC_IMAGE` | PhotoRec's displayed partition number matching the examined ext4 offset, and its E01/raw input. Do not substitute the TSK sector offset for a partition number. |

TSK documents image formats, sector offsets and sector-size arguments in its [fls manual](https://www.sleuthkit.org/sleuthkit/man/fls.html). PhotoRec documents raw/E01 input and that image examination needs no administrator rights; EWF handling is conditional on libewf in its build. [Starting PhotoRec](https://www.cgsecurity.org/testdisk_doc/running.html), [7.2 EWF source](https://raw.githubusercontent.com/cgsecurity/testdisk/v7.2/src/ewf.c)

If PhotoRec lacks direct EWF support, this alternative exposes a raw view without writing a 10 GB conversion:

```sh
ewfmount -f raw "$IMAGE" "$EWF_VIEW"
```

Here `IMAGE` is the E01, `EWF_VIEW` is an existing empty directory, and PhotoRec's input becomes `"$EWF_VIEW/ewf1"`. This is a FUSE container view, **not an ext4 filesystem mount**. It requires working FUSE permissions; root is not intrinsically required for a user-readable image, but host policy can require setup. If FUSE is unavailable, an actual raw-disk export costs approximately **10 GB additional scratch space**; it is not a prerequisite of the preferred direct-E01 route. [ewfmount manual](https://raw.githubusercontent.com/libyal/libewf/main/manuals/ewfmount.1)

None of the three techniques requires mounting ext4. If a later task separately needs one, `ro` alone is insufficient to prohibit journal replay: require `ro,noload` and a read-only backing device. Such a mount is unnecessary here. [ext4 mount semantics](https://man7.org/linux/man-pages/man5/ext4.5.html)

## A. Surviving metadata: attempt first, thesis rank 2

This establishes why ordinary undelete stops. Reuse the already recorded enumeration if it has adequate provenance; repeating it is not a new experiment. The inode list and bodyfile below intentionally select used, unallocated records. Their denominator must not be silently expanded to include never-used inode slots. TSK 4.15.0 starts with that selection; the explicit flags preserve it. [ils implementation](https://raw.githubusercontent.com/sleuthkit/sleuthkit/sleuthkit-4.15.0/tools/fstools/ils.cpp)

```sh
fls -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" -rd -p \
  "$IMAGE" "$TMP_INODE"
ils -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" -A -Z "$IMAGE"
ils -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" -A -Z -m \
  "$IMAGE" > "$OUT/unallocated.body"
TZ=UTC mactime -b "$OUT/unallocated.body" -z UTC
```

`fls -r` does not descend into deleted directories. Keep that traversal limit in the negative finding. `ils` preserves deletion-time information in its native listing; keep that listing alongside the timeline instead of treating a MAC timeline as a full deletion record. [fls](https://www.sleuthkit.org/sleuthkit/man/fls.html), [ils](https://www.sleuthkit.org/sleuthkit/man/ils.html), [mactime](https://www.sleuthkit.org/sleuthkit/man/mactime.html)

Only if an evidence-derived candidate has usable mapping information:

```sh
istat -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" "$IMAGE" "$INODE"
icat -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" -r \
  "$IMAGE" "$INODE" > "$OUT/inode-candidate.bin"
```

The `-r` flag does not recreate cleared extents. The supplied zeroed records therefore offer no sound content-recovery route through this command. Likewise, debugfs `lsdel` is explicitly documented as unsuitable for ext3/ext4 undelete once the inode's blocks have been released. [icat](https://www.sleuthkit.org/sleuthkit/man/icat.html), [debugfs](https://manpages.debian.org/trixie/e2fsprogs/debugfs.8.en.html)

A bounded manual examination of `/tmp` directory blocks/slack is a useful extension if byte-level name remnants remain in question: obtain its block addresses with `istat`, then inspect selected blocks with `blkcat -h` as in B. Validate directory-record structure and the containing directory; a bare `rk.so` string is not a recovered path. This is still metadata examination, not a fourth technique. [Directory format](https://www.kernel.org/doc/html/latest/filesystems/ext4/directory.html)

## B. Journal-assisted reconstruction: attempt second, thesis rank 1

This ranks highest because it tests whether historical metadata can bridge the missing pathname and cleared extents. In ordinary ordered journaling, the useful journal object is usually an old metadata block, not a saved 32 KB ELF file. A successful journal read or a name string alone is insufficient: the examiner must connect directory block, inode version, extent map and acquired payload, retaining transaction/block locators. [Journal format](https://www.kernel.org/doc/html/latest/filesystems/ext4/journal.html), [directory format](https://www.kernel.org/doc/html/latest/filesystems/ext4/directory.html), [extent format](https://www.kernel.org/doc/html/latest/filesystems/ext4/ifork.html)

First determine **J** from inode 8 and export that inode only:

```sh
istat -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" "$IMAGE" 8
icat -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" \
  "$IMAGE" 8 > "$OUT/journal.bin"
```

These commands inspect metadata and copy the selected inode's content. J is not supplied; for illustration only, a 128 MiB journal would require a 128 MiB export, not an 8.46 GB one. Check J before export. [istat](https://www.sleuthkit.org/sleuthkit/man/istat.html), [icat](https://www.sleuthkit.org/sleuthkit/man/icat.html)

Run from `OUT` so the debugfs command uses a fixed examiner-controlled filename. `JOURNAL_BLOCKS` is the verified integer count defined above:

```sh
cd "$OUT"
timeout -k 5s 120s debugfs \
  -R "logdump -O -a -n $JOURNAL_BLOCKS -f journal.bin" \
  > journal-index.txt 2> journal-index.stderr
```

`-O` includes old checkpointed entries; `-a` displays descriptors; `-n` permits continuing across missing magic values, subject to its transaction limit. There is deliberately no `-c` whole-journal hex dump. **With `-f` and without filesystem-dependent selectors, logdump can read the exported journal without opening a filesystem.** For the installed 1.47.0, do not add `-S`, `-b` or `-i` to this standalone form: those paths access filesystem state. This is verified from the versioned source, not a claim of local execution. [debugfs manual](https://manpages.debian.org/trixie/e2fsprogs/debugfs.8.en.html), [1.47.0 logdump source](https://raw.githubusercontent.com/tytso/e2fsprogs/v1.47.0/debugfs/logdump.c)

The **120-second limit is a proposed feasibility bound**, not a journal-retention or performance claim. Version 1.47.1 fixed a potential logdump infinite loop. Prefer a fixed build before the trial; retain the bound if using 1.47.0. A timeout, parse error, or incomplete traversal cannot support a whole-journal negative. Inspect stderr even after exit zero. [e2fsprogs release notes](https://e2fsprogs.sourceforge.net/e2fsprogs-release.html), [timeout](https://manpages.debian.org/trixie/coreutils/timeout.1.en.html)

Extract and inspect a selected journal block without relying on TSK to decode JBD2 descriptors:

```sh
blkcat -i raw -f raw -u 4096 "$OUT/journal.bin" "$JBLOCK" 1 \
  > "$OUT/journal-block.bin"
blkcat -i raw -f raw -u 4096 -h "$OUT/journal.bin" "$JBLOCK" 1
```

After manual validation establishes an old physical extent, extract its blocks from the acquired filesystem:

```sh
blkcat -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" \
  "$IMAGE" "$FS_BLOCK" "$BLOCK_COUNT" > "$OUT/extent.bin"
```

`blkcat` emits consecutive units, not a reconstructed fragmented file. Preserve logical extent order, account for holes/unwritten extents, and trim only a separately derived candidate to an evidenced length. Roughly eight 4 KiB blocks fit a 32 KiB file, but neither exact length nor contiguity is supplied. [blkcat](https://www.sleuthkit.org/sleuthkit/man/blkcat.html), [extent layout](https://www.kernel.org/doc/html/latest/filesystems/ext4/ifork.html)

For comparison, the documented TSK journal forms are:

```sh
jls -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" "$IMAGE" 8
jcat -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" \
  "$IMAGE" 8 "$JBLOCK" > "$OUT/jcat-block.bin"
```

`jls` lists journal records and `jcat` exports a journal block; neither reconstructs an old pathname automatically. TSK 4.15.0's journal code advances through fixed legacy descriptor structures, unlike debugfs's feature-dependent tag sizes. **Source-based compatibility concern:** do not assume its filesystem-level ext4 support guarantees correct decoding of modern JBD2 checksum/64-bit tags. Check actual journal features and validate descriptor-to-block mappings before relying on these readers. Do not claim that this image has such features merely because it is ext4. [jls](https://www.sleuthkit.org/sleuthkit/man/jls.html), [jcat](https://www.sleuthkit.org/sleuthkit/man/jcat.html), [TSK 4.15.0 journal source](https://raw.githubusercontent.com/sleuthkit/sleuthkit/sleuthkit-4.15.0/tsk/fs/ext2fs_journal.c), [debugfs tag handling](https://raw.githubusercontent.com/tytso/e2fsprogs/v1.47.0/debugfs/logdump.c)

## C. Unallocated-space ELF carving: attempt third, thesis rank 3

This tests content survival independently of the lost inode mappings. PhotoRec can select ext4 free space directly, avoiding a separate multi-gigabyte export. Use an EWF-enabled build or the raw view described above, and verify the selected partition and free-space mode in its log. [PhotoRec input](https://www.cgsecurity.org/testdisk_doc/running.html), [free-space selection](https://www.cgsecurity.org/testdisk_doc/photorec.html)

```sh
photorec /log /logname "$OUT/photorec.log" /d "$OUT/photorec" \
  /cmd "$PC_IMAGE" \
  "$PC_PART,options,mode_ext2,fileopt,everything,disable,elf,enable,freespace,search"
```

For an **already available filesystem-only raw image**, the explicit no-partition-table form is:

```sh
photorec /log /logname "$OUT/photorec.log" /d "$OUT/photorec" \
  /cmd "$FS_RAW" \
  "partition_none,options,mode_ext2,fileopt,everything,disable,elf,enable,freespace,search"
```

The scripted command vocabulary and `elf` identifier are documented in the [scripted-run manual](https://www.cgsecurity.org/testdisk_doc/scripted_run.html) and [7.2 ELF handler](https://raw.githubusercontent.com/cgsecurity/testdisk/v7.2/src/file_elf.c). PhotoRec creates numbered output directories; retain its log and locations rather than renaming a hit `/tmp/rk.so`.

**ELF-specific limitation:** the 7.2 handler recognizes 32/64-bit ELF, sets a minimum size from header offsets, and has a **10 MiB maximum candidate size**; it does not calculate exact EOF with an ELF-specific file-size checker. Thus a 32 KB object may arrive with unrelated trailing bytes. Restricting recognized types also removes other headers that could terminate an overlarge carve. Preserve each original candidate, and distinguish complete, partial and over-carved output. [ELF source](https://raw.githubusercontent.com/cgsecurity/testdisk/v7.2/src/file_elf.c), [PhotoRec boundary warning](https://www.cgsecurity.org/testdisk_doc/photorec.html)

The allocated duplicate can supply an explicitly disclosed **known-content comparison**, not a deleted-path identification. Compare original candidate length/hash first. If a candidate contains a matching prefix, make a separate extraction of the reference's exact byte length and record that reference-assisted boundary choice; do not silently trim until a hash matches. Validate ELF structure and map the candidate's block locations back to the original image. An executable-looking header alone is not complete recovery. The 10 MiB per-candidate limit does not bound the total output to 10 MiB; enough candidates can still consume multiple GB.

The export-first alternative, **not recommended by default**, is:

```sh
blkls -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" \
  "$IMAGE" > "$OUT/unallocated.raw"
```

This writes **8,460,476,416 bytes** before any carving output. It concatenates free blocks, removing allocated gaps and original offsets. Consequently, it can introduce artificial adjacency; do not feed it to PhotoRec as if it were an intact ext4 filesystem. TSK can map an exported block index back with `blkcalc -u`, but that extra provenance work is avoidable with direct free-space carving. [blkls](https://www.sleuthkit.org/sleuthkit/man/blkls.html), [blkcalc](https://www.sleuthkit.org/sleuthkit/man/blkcalc.html)

## Families that do not earn another slot

| Family/tool | Decision and case-specific reason |
|---|---|
| Whole-filesystem `tsk_recover` | **Exclude as a separate technique.** Default exports unallocated files; `-e` includes allocated files too. It traverses filesystem objects rather than signature-carving 8.46 GB of free blocks. In 4.15.0, `processFile` explicitly skips zero-sized or missing metadata, matching this case's key limitation. An allocated duplicate exported by `-e` is an allocated-file extraction, not recovery of `/tmp/rk.so`. [Manual](https://www.sleuthkit.org/sleuthkit/man/tsk_recover.html), [versioned source](https://raw.githubusercontent.com/sleuthkit/sleuthkit/sleuthkit-4.15.0/tools/autotools/tsk_recover.cpp) |
| `ext4magic` / `extundelete` | Their historical journal-reconstruction mechanism earns a place through B; **these implementations do not**. ext4magic's maintainer explicitly discontinues maintenance and warns that distribution builds can still be incompatible. extundelete has documented failures with `64bit`/`metadata_csum`. Do not treat either failure as a negative about recoverability. [Maintainer statement](https://sourceforge.net/p/ext4magic/tickets/17/), [Debian bug and ext4 maintainer response](https://bugs.debian.org/969495) |
| `scalpel` | A viable alternative signature carver, not a mechanically distinct fourth method. Its header/footer rules do not restore deleted extents or pathnames. Distinguish the abandoned Sleuth Kit branch from the still-updated 1.60 lineage below. Prefer PhotoRec's documented ext4 free-space and ELF support for this bounded trial. [Scalpel package/mechanism](https://packages.debian.org/trixie/scalpel) |
| `bulk_extractor` | Maintained, but primarily filesystem-independent feature extraction, recursive decoding and selected carving. It does not use ext4's allocation map to confine a whole-image scan to deleted content, nor reconstruct the deleted path. A target-related feature could equally belong to the allocated duplicate. **No separate slot** for this question. [Upstream purpose and build support](https://github.com/simsong/bulk_extractor) |
| `foremost` | Not installed in the supplied environment. Another header/footer/content carver; no additional mechanism justifies installing it here. Upstream maintenance verification is incomplete, as recorded below. [Upstream](https://foremost.sourceforge.net/) |
| TestDisk undelete / filesystem repair | TestDisk supports reading ext4, but its documented undelete menu covers FAT, exFAT, ext2 and NTFS, not ext4. Repairing a filesystem or partition is not the requested post-mortem recovery experiment. [Documented undelete menu](https://www.cgsecurity.org/testdisk_doc/scripted_run.html) |

For clarity, the exact bulk-export forms would be:

```sh
tsk_recover -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" \
  "$IMAGE" "$OUT/tsk-unallocated"
tsk_recover -i "$FMT" -b "$SECTOR" -f ext4 -o "$OFF" -e \
  "$IMAGE" "$OUT/tsk-all"
```

Neither needs a mount/root for readable images. The first should not recover the target from the supplied zeroed records; the second adds exported allocated content and can write **multiple GB**. Exact total depends on logical file sizes and recovered objects, and is not the free-block count. There is no reason to pay that cost just to reproduce the known allocated duplicate. [tsk_recover](https://www.sleuthkit.org/sleuthkit/man/tsk_recover.html)

Known-content block matching or manual carving is a useful refinement of C if ELF carving fails: it may locate fragments without a valid header, but is reference-assisted and still cannot establish the deleted path. It does not warrant inventing a fourth mechanism or a new custom recovery program for this task. Allocated-but-unlinked inode examination belongs within A; live `/proc/<pid>/fd` or process-mapping recovery requires volatile state and cannot be recreated by mounting this disk image. A separate RAM examination may complement the disk findings but is outside this shortlist. [Inode-selection semantics](https://www.sleuthkit.org/sleuthkit/man/ils.html), [Linux proc filesystem](https://www.kernel.org/doc/html/latest/filesystems/proc.html)

## Maintenance and compatibility checks

“Build available” below means a current distribution publishes a binary, or upstream documents current CI. It is **not** a claim that this research compiled the exact release or tested the target image. A distribution patch/rebuild does not establish upstream recovery compatibility. No installation or upgrade is authorized by this document.

| Tool/project | Last release/commit verified | Debian/Ubuntu build evidence and known limits |
|---|---|---|
| TSK: `fls`, `ils`, `istat`, `icat`, `blkcat`, `blkls`, `blkcalc`, `jls`, `jcat`, `tsk_recover`, `mactime` | **4.15.0, 2026-04-15**, latest upstream release. [Release](https://github.com/sleuthkit/sleuthkit/releases/tag/sleuthkit-4.15.0) | Debian 13 publishes **4.12.1+dfsg-3**, showing current distribution buildability, not a 4.15.0 build test. The supplied host already has 4.15.0. JBD2 descriptor compatibility requires the qualification in B; no general ext4 recovery guarantee follows from maintenance. [Debian](https://packages.debian.org/trixie/sleuthkit) |
| e2fsprogs / `debugfs` | **1.47.4, 2026-03-06**; installed 1.47.0 dates to **2023-02-05**. [Release history](https://e2fsprogs.sourceforge.net/e2fsprogs-release.html) | Debian 13 publishes **1.47.2-3** and architecture rebuilds. The **1.47.1 logdump loop fix** is directly relevant; a crash/timeout is a tool problem. [Debian](https://packages.debian.org/trixie/e2fsprogs) |
| libewf / `ewfmount` | Latest tag checked: **20240506**. Main-tree commit **51bcc4e**, **2026-09-18** demonstrates ongoing work. [Tag](https://github.com/libyal/libewf/tree/20240506), [commit](https://github.com/libyal/libewf/commit/51bcc4e285b606a9705cd818a4b2d8c85df54cb3) | Debian 13 publishes older **20140816**-based `ewf-tools` builds with FUSE. The case supplies 20240506. Exact local FUSE setup is **unverified**; package age must not be mistaken for upstream abandonment. [Debian](https://packages.debian.org/trixie/ewf-tools) |
| `ext4magic` | **0.3.2, 2014-09-12**; upstream marked abandoned. Maintainer confirmed discontinued support **2024-09-30**. [Files](https://sourceforge.net/projects/ext4magic/files/), [statement](https://sourceforge.net/p/ext4magic/tickets/17/) | Debian 13 builds **0.3.2-15**, but the maintainer explicitly warns that compilability does not imply current compatibility. The cited ticket reports a crash even in targeted `-f … -l` listing. **Exclude**, including the installed 0.3.2; do not merely avoid its broad magic-scan mode and assume the rest safe. [Debian](https://packages.debian.org/trixie/ext4magic) |
| `extundelete` | **0.2.4, 2013-01-03**, still the latest listed upstream release. [Upstream](https://extundelete.sourceforge.net/), [release directory](https://sourceforge.net/projects/extundelete/files/extundelete/) | Debian 13 builds **0.2.4-3** and rebuilds. A reproducible report documents failure with `64bit` plus `metadata_csum`; the ext4 maintainer explains that newer features can break this recovery approach. These flags are not established for this image. **Exclude**; no current-feature compatibility guarantee. [Debian](https://packages.debian.org/trixie/extundelete), [bug 969495](https://bugs.debian.org/969495) |
| PhotoRec / TestDisk | Stable **7.2, 2024-02-22**; **7.3** development/beta listed on the current download page. [Upstream](https://www.cgsecurity.org/wiki/TestDisk_Download) | Current Debian `testdisk` binaries and upstream Linux binaries are available. Verify **both libext2fs and libewf** support in the chosen build; the displayed Debian dependencies include libext2fs but do not establish EWF support. ELF-specific size/boundary limitations remain even in a working build. [Debian dependencies](https://packages.debian.org/trixie/testdisk), [build instructions](https://www.cgsecurity.org/testdisk_doc/building_from_source.html) |
| Scalpel, Sleuth Kit branch | Latest checked commit **35e1367, 2021-03-26**; README explicitly says it is not actively maintained. [Commit](https://github.com/sleuthkit/scalpel/commit/35e1367ef2232c0f4883c92ec2839273c821dd39), [README](https://raw.githubusercontent.com/sleuthkit/scalpel/master/README) | Do not conflate this branch with Debian's current source lineage. Exact present buildability of this branch is **unverified**. |
| Scalpel, `nolaforensix/scalpel-1.60` lineage | Latest checked commit **fc2a8a8, 2026-04-19**, fixes Linux warnings. [Commit](https://github.com/nolaforensix/scalpel-1.60/commit/fc2a8a8f1909b09946cd179b3b932f92ceb4ea95) | Debian 13 builds **1.60+git20240110.6960eb2-1** and rebuilds from this lineage. This is evidence against calling *all* Scalpel variants abandoned. No target-specific runtime test was performed; it remains an alternative within C. [Debian](https://packages.debian.org/trixie/scalpel) |
| `bulk_extractor` | **2.2.0, 2026-08-18**, latest release. [Release](https://github.com/simsong/bulk_extractor/releases/tag/v2.2.0) | Upstream reports **Ubuntu 22.04 CI**, requires C++17, and explicitly excludes native Debian 10 builds. Maintained and buildable in a relevant environment; excluded for mechanism/scope, not age. [Upstream](https://github.com/simsong/bulk_extractor) |
| `foremost` | **1.5.7** package version verified; exact latest upstream release date and ongoing maintenance **unverified**. Upstream download browsing could not be completed. [Homepage](https://foremost.sourceforge.net/), [Debian](https://packages.debian.org/trixie/foremost) | Debian 13 publishes **1.5.7-11** and architecture builds. That establishes distribution availability only. No case-relevant runtime claim is made. |
| GNU coreutils / `timeout` | **9.11, 2026-04-20**. [Release announcement](https://lists.gnu.org/archive/html/coreutils-announce/2026-04/msg00000.html) | Debian 13 publishes **9.7-3**. `timeout` provides the proposed execution bound; timeout status is not a forensic result. Exact host version was not inspected. [Debian](https://packages.debian.org/trixie/coreutils), [manual](https://manpages.debian.org/trixie/coreutils/timeout.1.en.html) |

## Final recommendation and endpoint

Attempt **A → B → C**: preserve the existing metadata negative first, examine historical journal metadata second, and perform one ELF-focused free-space pass third. Journal reconstruction has the highest thesis value because it can recover the missing association; the metadata negative ranks above a trivial extraction of the allocated copy because it explains a genuine methodological limit. Carving adds a distinct test of content survival but requires strict location and identity limits.

For the later trial, settle image parameters and the debugfs build before scanning; use a fixed logdump version where feasible and the explicit time bound otherwise. Retain full output and stderr. Classify results separately as **complete content, partial content, metadata/name only, bounded no-result, tool failure, or not attempted**. Stop on incompatibility rather than treating an empty export as evidence. Successes and failures are observations for human interpretation, not automatic claim acceptance.

Do not add `tsk_recover -e`, a second signature carver, or an abandoned journal undelete tool merely to increase the tool count. The experimental trial is a separate task; this document is the endpoint.
