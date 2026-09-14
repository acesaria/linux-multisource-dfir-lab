# Locked-table mental simulation — 10 September 2026

**Verdict: feasible with the current investigation design, but not ready to
calculate today.** The methodology remains locked. The missing work is evidence
examination, explicit GT claim records and simple aggregation, not a redesign.
No notebook cells, recovery tests or VM actions were executed for this check.
The original manifest and all acquired evidence remain unchanged.

## What was inspected

- The complete immutable `RESULTS_PREVIEW.md` and current unified notebook.
- `manifest.json`, `command_log.jsonl` and `dumps/acquisition.json` for
  `father-u22-20260820-01`.
- Existing orientation outputs, helper behavior and selected preserved recovery records.
- Current recovery documentation and installed tool versions.

## Applicability of each table

| Locked table | Available starting point | Work needed before real values |
|---|---|---|
| 1. Chronology | Recorded image/timezone/partition context; draft preload and library metadata commands | Complete Plaso and native log examination, RAM process times and source locators. Use relative/uncertain times where needed; acquisition metadata is not an attack timestamp. |
| 2. Claim Coverage & Source Support | Input hash, scenario endpoints, backdoor connection facts, 38 command/operation records | Create stable claim IDs, exact propositions and GT references. Examine Disk/Timeline/RAM and manually record S/P/U/N/A, combined reasoning and missing elements. Phase markers are not separate attack claims. |
| 3. Multi-Source Contribution | The locked definitions can be calculated from Table 2 | Complete human support decisions and underlying-origin references. Simple filters/counts suffice; no automatic inference engine. No current numeric result is justified. |
| 4. Footprint Inventory | Draft disk extraction and /tmp listing; planned process/socket examination | Validate staging-file contents, RAM mappings/credentials and socket objects. Deduplicate process identities, shared sockets, hard links and recovery duplicates; retain failed/unexamined scope. |

The current notebook's section 0 has retained orientation outputs. Preload and
/tmp cells are draft commands with pending interpretation; RAM, Plaso chronology
and result-table implementation remain placeholders. Recovery currently has
basic deleted-entry listing plus older raw leads; the two complementary disk
techniques in RECOVERY_NOTES.md need fresh bounded tests.

## Small data additions, without changing the experiment unnecessarily

The manifest has no `claims` array. It contains run/platform/input identities,
scenario-level timing and one backdoor connection record. The command log records
successful install, preload configuration, service restart, staging and cleanup
operations. These can anchor a derived claim list; they do not automatically
prove every intended side effect or supply precise guest event times.

Use a short notebook list or a clearly labelled derived claim sidecar containing:
`id`, exact `statement`, `gt_refs`, and the recorded outcome/validation limit.
Each reviewed observation needs its lens, original record locator, support state,
missing element and combined explanation. Derive numeric columns with ordinary
Python counting. Do not build a general claim-matching or scoring system.

For this run, organize only facts already present in the records; leave the
original manifest unchanged. A future runner may emit the same small claim list
and RAM capture start/end times. If essential runtime or pre-deletion facts were
never recorded, capture them on a fresh run rather than inventing them afterward.
A successful deletion command is not by itself proof that a pre-existing file
was actually present; its prior existence and identity need recorded support.

## Three operational cautions within the locked specification

1. **Independence:** Static Disk and Timeline remain separate columns, but an
   inode and Plaso's rendering of that same inode cannot establish independent
   corroboration. A filestat timestamp does not supply the configuration's value.
2. **Claim meaning:** distinguish 'file was deleted' from 'deleted file content
   was recovered'. Missing content does not automatically downgrade an otherwise
   established deletion claim. Do not mark a combined claim Partial while a lens
   is independently S for that exact same proposition without resolving the mismatch.
3. **Aggregation:** the preview's examples are fictional, not a consistent test
   dataset. Recompute real values. Per-lens counts overlap; corroborated claims
   are a subset of singly sufficient claims. Joint sufficiency needs a written
   combination of complementary evidence, not merely two P cells. Partial or
   unsupported combined claims remain unresolved; pending work stays explicit.

The protected preview still includes an illustrative sentence excluding carving.
The user's explicit override governs execution; the file was not altered.

## Recovery in the mental simulation

Journal reconstruction may supply historical inode/name/extent links. Targeted
unallocated-space carving may supply bytes without original path/history. RAM
may retain complementary mapped or cached content. Combine only demonstrated
identities and origins, with the same S/P/U/N/A and contribution definitions.
The prior PhotoRec candidate is worth validating; extundelete's recorded crash
is a technical failure. Full recovery, partial content, metadata-only traces and
valid scoped negatives all fit the existing tables without another metric.

## Next implementation unit

Define the reference claims from preserved records; test journal recovery and
targeted unallocated-space carving; implement the missing disk/log/Plaso and RAM
sections, then fill the four tables. Keep visible tool commands and small Python
cells. Finish all planned scenario results over the approximately one-month
project horizon; metric selection is closed.
