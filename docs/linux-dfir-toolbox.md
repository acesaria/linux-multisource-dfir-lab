# Linux DFIR Toolbox

> **WIP operational cheat sheet.** Designed for simple Linux proof-of-concept
> scenarios; structure and commands will evolve as more sources are reviewed.

**Use:** choose a forensic question → run only applicable rows → preserve raw
output → report facts, inferences, negative results, tool failures, and limits.

Use only within a selected forensic section against acquired evidence or
read-only derivatives; save outputs separately. These are examiner commands,
not instructions to add guest-side validation to a scenario. The shared
[rules](../ai/RULES.md) govern claims, finding statuses, counts and human review.
Technique groupings below do not restrict which sources can inform a claim.

## 0. Quick Start

### Investigation structure

| Section | Minimum content |
|---|---|
| **1. Introduction** | Purpose, evidence, questions, scope |
| **1.1 Environment** | Examiner host, tools/versions, workspace, timezones |
| **1.2 Validation** | Evidence hash, image, partition, filesystem, offset |
| **2. Examination** | Named technique → command → raw output → interpretation |
| **3. Conclusion** | Answers, principal findings, negative results, limitations |

Starting structure, not a fixed template. [S5]

### Workspace

| `images/` | `data/` | `recovered/` | `mnt/` |
|---|---|---|---|
| Immutable evidence/read-only references | Hashes, raw output, timelines, notes | Exported/recovered artifacts | Optional; unused by default |

### Timezone gate

> **Before reading timestamps:** record examiner timezone, acquired-system timezone
> (`/etc/timezone`, `/etc/localtime`), and tool-output timezone. If unknown, use
> **UTC** and state the assumption. Never silently mix zones. [S1][S5]

### Workflow

| Step | Do | Output |
|---:|---|---|
| **1** | Validate evidence; record tools | Hash/verification record |
| **2** | Identify partition, filesystem, offset, timezone | Environment record |
| **3** | Fix question, target, evidence, time window | Scope statement |
| **4** | Examine the most direct artifact | Complete raw output |
| **5** | Pivot on path, inode, user, IP, hash, time | Corroboration |
| **6** | Timeline for **when/order**; recovery for **missing/deleted content** | Bounded results |
| **7** | Answer the question; state negatives/failures/limits | Conclusion |

### Boundary

| Area | Question | Output |
|---|---|---|
| **Disk analysis** | What allocated objects, metadata, or content exist? | Paths, inodes, exported files |
| **Timeline analysis** | When/in what order did relevant events occur? | Sourced, time-bounded events |
| **Disk recovery** | Can unavailable/deleted material be reconstructed? | Candidate + validation state |

Allocated `icat` = extraction; `icat -r` = recovery; inspecting or hashing the
output = analysis.

## 1. Disk Forensics

> **Default:** examine E01/images directly. Do not mount unless required.

### 1.1 Orientation and extraction

| Technique | Question | Command/process | Evidence / limit | Src |
|---|---|---|---|---|
| **Image verification** | Is the E01 internally consistent? | `ewfverify <IMAGE.E01>` | E01 + acquisition record; not proof of acquisition completeness | [S1] |
| **Partition identification** | Where is the target filesystem? | `mmls <IMAGE>` | Correct image/sector size; retain start sector as `<OFFSET>` | [S1][S2] |
| **Filesystem identification** | Which filesystem rules apply? | `fsstat -o <OFFSET> <IMAGE>` | Wrong offset invalidates later results | [S1][S2] |
| **Timezone identification** | How should host times be interpreted? | `fcat -o <OFFSET> /etc/timezone <IMAGE>`; preserve `/etc/localtime` | Applications may use different time rules | [S1][S2] |
| **Inode metadata analysis** | What state, owner, size, and times belong to an inode? | `fls -o <OFFSET> -l <IMAGE> [<DIR_INODE>]` → `istat -o <OFFSET> <IMAGE> <INODE>` | Metadata does not identify the actor | [S1][S2] |
| **Path-to-inode resolution** | Which inode represents a path? | `ifind -o <OFFSET> -n <PATH> <IMAGE>` | Deleted names/inode reuse weaken attribution | [S2] |
| **Allocated-content extraction** | What content belongs to the inode? | `icat -o <OFFSET> <IMAGE> <INODE> > <OUTPUT>` | Save outside evidence; verify path/inode link | [S2] |

### 1.2 Linux logs and host artifacts

| Technique | Question | Command/process | Evidence / limit | Src |
|---|---|---|---|---|
| **Authentication-log analysis** | Which login, failure, session, or privilege events exist? | `last -F -i -f <WTMP>`; `lastb -F -i -f <BTMP>`; `grep -aFn '<INDICATOR>' <AUTH_LOG>...` | Exported logs; rotation/tampering/corruption create gaps | [S1] |
| **Cross-log correlation** | Does an indicator recur across artifacts? | `grep -aFn '<USER_IP_PATH_TIME>' <LOG>...` | Recurrence supports association, not causation/identity | [S1] |
| **Account/privilege analysis** | What local privileges existed? | Search `<PASSWD>`, `<SHADOW>`, `<GROUP>` for `<USER>`, `sudo`, `wheel` | Snapshot does not show when/who changed it | [S1] |
| **Shell-history analysis** | Which recorded commands provide pivots? | `grep -nF '<INDICATOR>' <HISTORY>` or `nl -ba <HISTORY>` | May be edited, incomplete, untimestamped, or unflushed | [S1] |
| **Version/advisory correlation** | Does the observed build/configuration match an advisory? | Identify exact package/build/config → compare with vendor advisory/CVE | Vulnerability ≠ exploitation | [S1] |

`strings -a <DAMAGED_BINARY_LOG>` is fallback triage, not validated log parsing.

### 1.3 Hashing and static triage

| Technique | Question | Command/process | Evidence / limit | Src |
|---|---|---|---|---|
| **SHA-256 evidence hashing** | Is this the same evidence/derivative? | `sha256sum <EVIDENCE>` | Proves byte identity, not acquisition completeness | [S5] |
| **Artifact hash correlation** | Are selected files byte-identical? | `sha256sum <FILE>...` | Same bytes ≠ same origin/execution | [S5] |
| **Bounded hash inventory** | Which files match/differ in a defined set? | `find <TREE> -type f -exec sha256sum {} + > <INVENTORY>` | Run only for a defined comparison | [S5] |
| **Static file triage** | What is the candidate and what leads does it contain? | `file <FILE>`; `strings -a <FILE>`; `sha256sum <FILE>` | Strings do not prove behavior | [S1][S5] |
| **Encoded-content decoding** | What does a justified encoded artifact contain? | `base64 --decode <ENCODED> > <DECODED>` → static triage | Preserve original; decoding ≠ execution/malice | [S1] |

### 1.4 Deleted-file recovery

| Technique | Question | Command/process | Evidence / limit | Src |
|---|---|---|---|---|
| **Deleted-entry enumeration** | Which deleted names still survive? | `fls -o <OFFSET> -rdp <IMAGE> [<DIR_INODE>]` | ext4 names may survive, disappear, or refer to reused metadata | [S1][S2][S5] |
| **Candidate inode recovery** | Can bytes be recovered from this inode? | `icat -r -o <OFFSET> <IMAGE> <INODE> > <OUTPUT>` | May be stale, partial, padded, corrupt, or empty | [S2][S5] |
| **Journal-assisted ext4 recovery** | Can the journal recover a known path/window? | Recipe below | Requires ext3/4 filesystem, journal, bounded path/time, separate output; block reuse limits success | [S1][S3] |

```bash
debugfs -R 'dump <8> <JOURNAL>' <EXT4_FILESYSTEM>
ext4magic <EXT4_FILESYSTEM> -j <JOURNAL> -a <AFTER_EPOCH> \
  -b <BEFORE_EPOCH> -f <FS_RELATIVE_PATH> -r -d <OUTPUT_DIR>
```

**Recovery outcome:** complete content, partial content, metadata-only traces,
bounded non-recovery, tool failure or not attempted. These describe an attempt,
not extra claim statuses. Metadata is not recovered content. Validate identity
with available size/hash references and disclose any scenario-assisted matching.

## 2. Memory Forensics

> **Requirement:** validated memory image and exact matching Linux kernel symbols.
> Use the installed Volatility 3 launcher as `<VOL3>` (`vol`, `vol3`, or project
> wrapper). Verify plugin syntax with `<VOL3> <PLUGIN> -h`.
>
> **Route:** establish a process view, pivot to relevant resources, then run only
> the mechanism-specific checks justified by the question or observed anomalies.

**Command form:** `<VOL3> -q -f <MEMORY> -s <SYMBOL_DIR> <PLUGIN> [options]`

| Gate            | Rule                                                                            |
| --------------- | ------------------------------------------------------------------------------- |
| **Evidence**    | Validate image; record acquisition context                                      |
| **Symbols**     | Match the acquired kernel exactly                                               |
| **Scope**       | Run only question-relevant plugins                                              |
| **Result**      | Successful zero rows ≠ plugin/tool failure                                      |
| **Correlation** | Relate processes, mappings, files, sockets, kernel objects; deduplicate objects |

### 2.1 General workflow

| Step | Do | Pivot / output |
|---:|---|---|
| **1** | Validate hash/acquisition; identify kernel banner and exact symbols | `banners.Banners`; validation record |
| **2** | Establish processes, arguments, and parentage | `PsList` + `PsAux` + `PsTree` outputs |
| **3** | If hiding/spoofing is suspected, compare independent process views | PID/identity discrepancies to investigate |
| **4** | Pivot selected PIDs to mappings, libraries, files, and sockets | Process-centred evidence bundle |
| **5** | Test only the suspected userland or kernel mechanism | Bounded plugin result, including valid zero rows |
| **6** | Dump only justified mappings, ELFs, modules, or cached files | Derivative + SHA-256 + recovery limit |
| **7** | Correlate PID/path/inode/hash/address/time with disk and timeline | Observations and proposed interpretation for human review |

### 2.2 Process and resource examination

| Technique | Question | Volatility 3 action | Evidence / limit | Src |
|---|---|---|---|---|
| **Process inventory** | Which processes exist at capture time? | `linux.pslist.PsList --decorate-comm` | Linked-list view; capture is one time slice | [S7][S9] |
| **Process cross-view analysis** | Is a process missing from one enumeration path? | Compare `linux.pslist.PsList`, `linux.psscan.PsScan`, `linux.pidhashtable.PIDHashTable` | A discrepancy may be hiding, termination, stale data, or corruption | [S7] |
| **Process masquerade analysis** | Do executable path, `comm`, arguments, and parentage agree? | `linux.psaux.PsAux`; `linux.pstree.PsTree`; `linux.malware.process_spoofing.ProcessSpoofing` | An unusual name or parent is a lead, not proof | [S7][S9] |
| **Process memory-map analysis** | Which files and permissions back a process's VMAs? | `linux.proc.Maps --pid <PID>` | RWX/unbacked mappings may also be legitimate; mapping ≠ execution/malice | [S6][S7][S9] |
| **Injected-memory triage** | Which mappings may contain injected executable code? | `linux.malware.malfind.Malfind --pid <PID>` | Heuristic candidates require contextual validation | [S7] |
| **Shared-library enumeration** | Which libraries are associated with a process? | `linux.library_list.LibraryList --pids <PID>...` | Compare with mappings; neither view alone proves loading mechanism | [S6][S7] |
| **Process environment analysis** | Which retained environment values explain execution/loading? | `linux.envars.Envars --pid <PID>...` | Variables may be absent, overwritten, or irrelevant to system-wide preload | [S7][S8] |
| **Open-file analysis** | Which files, devices, pipes, and socket descriptors are open? | `linux.lsof.Lsof --pid <PID>...` | Open descriptor proves association at capture, not prior use or intent | [S7][S9] |
| **Process–socket correlation** | Which endpoints belong to selected processes? | `linux.sockstat.Sockstat --pids <PID>...` | Deduplicate shared/inherited descriptors; loopback is not inherently malicious | [S6][S7][S9] |

### 2.3 Mechanism-driven checks

| Suspected mechanism | Technique / question | Volatility 3 action | Evidence / limit | Src |
|---|---|---|---|---|
| **LD_PRELOAD / shared library** | Which processes map the library, and is per-process `LD_PRELOAD` retained? | `Maps` + `LibraryList` + `Envars` | `/etc/ld.so.preload` affects subsequently executed dynamic programs but does not create an environment variable | [S6][S7][S8] |
| **LKM / hidden module** | Are module views inconsistent? | `linux.lsmod.Lsmod`; `linux.malware.modxview.Modxview` | No module finding does not exclude transient modules or direct/moduleless kernel patching | [S7][S9] |
| **System-call table hook** | Do syscall entries resolve to unexpected handlers? | `linux.malware.check_syscall.Check_syscall` | Unknown/unexpected target is a lead; attribute its address before concluding | [S7][S9] |
| **Network protocol hook** | Do protocol operation pointers resolve outside expected kernel code? | `linux.malware.check_afinfo.Check_afinfo` | Covers relevant protocol structures, not every network-hiding method | [S7][S9] |
| **Ftrace hook** | Are callbacks attached through ftrace infrastructure? | `linux.tracing.ftrace.CheckFtrace` | Mechanism-specific; Phalanx2 did **not** use ftrace | [S7] |
| **eBPF program** | Which eBPF programs are resident? | `linux.ebpf.EBPF` | Enumeration requires analyst attribution; presence alone is not malicious | [S7] |
| **Kernel activity/errors** | Do logs record module loading, `/dev/mem`, faults, or protection events? | `linux.kmsg.Kmsg` | Buffer may be overwritten or tampered; a message records an event, not final state | [S7][S9] |

### 2.4 Targeted recovery and correlation

| Technique | Question | Volatility 3 action | Evidence / limit | Src |
|---|---|---|---|---|
| **Targeted VMA/heap extraction** | What data remains in a justified mapping? | `-o <OUT> linux.proc.Maps --pid <PID> --address <VMA_ADDR> --dump` | May contain stale/deallocated data; not necessarily a complete file | [S6][S7] |
| **Memory-resident ELF recovery** | Can a mapped process ELF be reconstructed? | `-o <OUT> linux.elfs.Elfs --pid <PID> --dump` | Reconstructed ELF may differ from or be less complete than the disk file | [S7] |
| **Kernel-module recovery** | Can an identified module be preserved for static analysis? | `-o <OUT> linux.lsmod.Lsmod --dump` | Requires an enumerated module; transient/unlinked code may be absent | [S7][S9] |
| **Page-cache / tmpfs recovery** | Does cached content survive for a known path or tmpfs? | `linux.pagecache.Files --find <PATH>` → `-o <OUT> linux.pagecache.InodePages --find <PATH> --dump`; or `-o <OUT> linux.pagecache.RecoverFs --tmpfs-only` | Only resident pages; output may be sparse/partial and recovered metadata is not original | [S7][S9] |
| **Recovered-artifact triage** | What is the derivative and how does it relate to disk? | `file`; `sha256sum`; `readelf -h -l -d -s`; `strings -a` | Strings do not prove behavior; preserve source PID/address/path | [S6] |

**Useful correlation paths:**

- shared library: `preload configuration/environment → library path/inode/hash → PID/mapping → socket → timeline`
- kernel module: `module view/address → dumped module/hash → disk .ko → kmsg → timeline`
- kernel hook: `hooked object/slot → handler address/symbol → module or unexplained region → related artifacts`

Count affected processes by **PID + path/inode**, not mapping rows: one object may
produce several VMAs or descriptors. [S6]

### 2.5 Phalanx2 Volatility 2 → 3 migration

| Volatility 2 used in [S9] | Current Volatility 3 action | Status |
|---|---|---|
| `linux_pslist` | `linux.pslist.PsList` | Direct equivalent |
| `linux_psaux` | `linux.psaux.PsAux` | Direct equivalent |
| `linux_pstree` | `linux.pstree.PsTree` | Direct equivalent |
| `linux_proc_maps` | `linux.proc.Maps` | Direct equivalent |
| `linux_lsof` | `linux.lsof.Lsof` | Direct equivalent |
| `linux_netstat` | `linux.sockstat.Sockstat` | Current functional replacement |
| `linux_dmesg` | `linux.kmsg.Kmsg` | Current replacement |
| `linux_lsmod` | `linux.lsmod.Lsmod` | Direct equivalent |
| `linux_check_modules` | `linux.malware.check_modules.Check_modules`; prefer `Modxview` for combined views | Available |
| `linux_check_afinfo` | `linux.malware.check_afinfo.Check_afinfo` | Direct equivalent |
| `linux_check_syscall` | `linux.malware.check_syscall.Check_syscall` | Direct equivalent |
| `linux_tmpfs` | `linux.pagecache.RecoverFs --tmpfs-only`; use `Files` / `InodePages` for a known path | Current functional replacement |

**Out of scope:** live execution, `strace`, GDB/IDA work, malware patching,
custom kernel instrumentation, and arbitrary kernel-address dumping. [S6][S9]

## 3. Timeline Forensics

### 3.1 Choose the view

| View | Use | Limit | Src |
|---|---|---|---|
| **TSK filesystem timeline** | Filesystem/inode activity | Disk-derived; names/time semantics need interpretation | [S2][S5] |
| **Plaso multi-artifact timeline** | Cross-artifact correlation | Parser failures/gaps ≠ negative results | [S1][S4] |

### 3.2 TSK filesystem timeline

```bash
fls -o <OFFSET> -r -m / <IMAGE> > <ALLOCATED_BODYFILE>
ils -o <OFFSET> -m -A <IMAGE> > <UNALLOCATED_BODYFILE>
mactime -b <ALLOCATED_BODYFILE> -d -z <TIMEZONE> <DATE_RANGE> > <ALLOCATED.csv>
mactime -b <UNALLOCATED_BODYFILE> -d -z <TIMEZONE> <DATE_RANGE> > <UNALLOCATED.csv>
```

Keep allocated/unallocated views distinct; inspect only the justified window.
[S2][S5]

### 3.3 Plaso timeline

```bash
log2timeline.py --storage-file <TIMELINE.PLASO> <IMAGE.E01>
psort.py -o dynamic -w <OUTPUT.csv> <TIMELINE.PLASO> \
  "date > '<START>' and date < '<END>'"
```

Record parser errors and output timezone. A disk-derived timeline is a view of
underlying disk records. [S1][S4] Apply the independence rule in [RULES.md](../ai/RULES.md):
rendering the same record twice provides one origin; distinct records still need
review of what each independently establishes. Keep Disk and Timeline columns.

### 3.4 Interpret and pivot

| Time | Meaning | Caution |
|---|---|---|
| **mtime** | Content modification | Can be altered/copied |
| **ctime** | Inode status change | Not creation time |
| **atime** | Recorded access | Weak under `relatime`/`noatime`; handling risk |
| **crtime/btime** | Birth/creation, if supported | Filesystem/tool dependent |
| **dtime/journal/log** | Deletion or source-specific event | Semantics are not interchangeable |

**Deleted-artifact pivot:**
`window entry → inode → istat → icat -r → file / strings / SHA-256`

On ext4, deleted filenames are unreliable: they may survive in directory/journal
metadata, be absent, or be reused. Corroborate inode, time, size, content, and source.
[S2][S5]

## Appendix — Deferred

| Approach | Status |
|---|---|
| **EWF/FUSE + loop** | Optional future path: `ewfmount <IMAGE.E01> <EWF_DIR>` → `losetup --find --show --read-only --offset <BYTE_OFFSET> <EWF_DIR>/ewf1`. Direct E01-aware tools remain default. |
| **Filesystem mount** | Avoid unless required; later document read-only setup, verification, risk, cleanup. |
| **Hardware protection / `hdparm`** | Important; safe procedure awaits authoritative review. |
| **LVM** | Deferred: absent from current scenarios. |
| **Web-access logs** | Deferred: no current server scenario. |
| **Raw deleted-directory parsing** | Historical/ext2-specific; omit from current workflow. |

## Sources

| ID | Source | Used for | Scenario / infection mechanism |
|---|---|---|---|
| **[S1]** | [Ali Hadi, “A Linux Forensics Starter Case Study” (2020)](https://www.forensicfocus.com/articles/a-linux-forensics-starter-case-study/) | Workflow, Linux artifacts, recovery escalation, Plaso | Vulnerable Drupal HTTP POST → PHP reverse shell → account/privilege changes; recovered local exploit |
| **[S2]** | [The Sleuth Kit manuals](https://www.sleuthkit.org/sleuthkit/man/) | Filesystem/inode/content/timeline commands | Tool reference; no scenario |
| **[S3]** | [ext4magic documentation](https://ext4magic.sourceforge.net/manpage_en.html) | Journal-assisted ext3/4 recovery | Tool reference; no scenario |
| **[S4]** | [Plaso user documentation](https://plaso.readthedocs.io/en/stable/sources/user/) | Timeline extraction/filtering | Tool reference; no scenario |
| **[S5]** | [Brian Carrier, “Honeynet Scan of the Month 15” (2001)](https://www.sleuthkit.org/case/sotm_15/) | Investigation structure, hashing, filesystem timelines, inode recovery; adapted to current TSK/ext4 | `lk.tgz` with installer, scripts, configs, and ELF tools replaced system binaries/files. **Inference:** precompiled off-host; no victim-side build evidence |
| **[S6]** | [Andrew Case, “Analyzing the Jynx rootkit and LD_PRELOAD” (2012)](https://volatilityfoundation.org/movp-2-4-analyzing-the-jynx-rootkit-and-ld_preload/) | Library mappings, process/socket pivots, heap and library recovery | Controlled VM: one `netcat` launched with `LD_PRELOAD`; no reboot. Separate SecondLook image: widespread mappings, but installation/restart method undocumented |
| **[S7]** | [Volatility 3 Linux plugin documentation](https://volatility3.readthedocs.io/en/stable/volatility3.plugins.linux.html) | Current process, mapping, resource, recovery, module, hook, tracing, and eBPF plugins | Tool reference; no scenario |
| **[S8]** | [`ld.so(8)` Linux manual](https://man7.org/linux/man-pages/man8/ld.so.8.html) | `LD_PRELOAD` and `/etc/ld.so.preload` semantics | Environment form is per execution; preload file applies system-wide to subsequently executed dynamic programs; reboot not required |
| **[S9]** | [Andrew Case, “Phalanx 2 Revealed” (2012)](https://volatilityfoundation.org/phalanx-2-revealed-using-volatility-to-analyze-an-advanced-linux-rootkit/) | Process context, files/sockets, kernel logs, module cross-view limits, syscall/protocol-hook checks; Volatility 2 concepts mapped to Volatility 3 | Manual install on Debian 6; transient helper LKM weakened `/dev/mem`, then a userland controller patched the syscall table and TCP sequence handler. No reboot or automatic persistence demonstrated |
