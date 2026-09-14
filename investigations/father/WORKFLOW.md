# Father — implementation of the locked result tables

Updated 2026-09-10. Methodology approved; investigation implementation is incomplete.
Gold standard: [RESULTS_PREVIEW.md](RESULTS_PREVIEW.md), read-only.
Operational rules: [INVESTIGATION_METHOD.md](../../docs/INVESTIGATION_METHOD.md).
Static readiness check: [IMPLEMENTATION_CHECK.md](IMPLEMENTATION_CHECK.md).

## Scope

Question: what can Static Disk, Timeline and RAM establish about the compromise,
and what does their combination add? Use `father-u22-20260820-01` first.
Known LD_PRELOAD compromise, supplied SSH/sudo access and scenario knowledge are
experimental context, not blinded discoveries. Plaso is required; its records
retain their underlying origins for the independence test.

Deletion recovery is fully included: deleted directory/inode records, ext4
journal reconstruction, bounded carving and useful retained RAM content. The
preview's illustrative deletion-recovery exclusion is superseded by the user.
Do not modify the preview. No further metric-selection research or debate.

## Notebook sequence

### 0. Case and evidence
Preserve orientation, image identity/integrity, partition offset, filesystem
features, symbols, timestamp semantics and acquisition-gap limitations. These
checks are prerequisites, not GT attack claims or footprint objects.

### 1. Preload configuration and installed library
Read the acquired preload configuration, resolve the referenced library, inspect
metadata and exact bytes, characterize the object. Record extraction provenance.
Configuration and file presence do not alone establish runtime mapping or hooks.

### 2. Surrounding activity: files, accounts and logs
Inspect evidence-led candidates under /tmp, content and metadata of potential
staging artifacts, relevant accounts/history, auth/service logs and wtmp/btmp.
Run a scoped Plaso extraction, retaining parser names and original record locators.
Use direct log inspection to verify interpretation without duplicating origins.
Do not infer a deletion event merely from a file being absent in a snapshot.

### 3. RAM context
Validate matching symbols and tool compatibility. Examine process mappings,
ancestry, credentials, command lines and socket ownership using observed pivots.
Deduplicate process identities and socket objects; distinguish LISTEN from
ESTABLISHED and volatile associations from historical traffic or exfiltration.
Dump selected mapped/cached content only when it answers an actual recovery lead.

### 4. Deleted-file recovery
Use [RECOVERY_NOTES.md](RECOVERY_NOTES.md) for the bounded test sequence. Basic
deleted-entry enumeration is one observation, not the complete recovery method.
Check filesystem/journal and tool compatibility, attempt a justified journal
reconstruction, then bounded carving where useful. Preserve complete tool output,
raw candidates, offsets and separately named derivatives; never write to evidence.
Content, metadata-only observations, bounded negatives and tool failures remain
distinct. Identify any use of known input size/hash or planted path as assistance.
Compare recovered bytes with the installed copy without assuming identical bytes
prove which file instance was deleted. Feed reviewed outcomes into the existing
claim and footprint tables; do not introduce another metric system.

### 5. Chronology (Table 1)
Select source records from disk/log/Plaso and RAM; retain timestamp semantics and
precision, relative ordering, unknowns and conflicts. Use 'at RAM capture' for
untimed volatile observations. Join with explicit identities (inode, PID/start,
service identity, socket object), accounting for aliases/reuse/acquisition gap.
Do not fill a missing forensic event with a command-log timestamp.

### 6. Claim coverage, contribution and inventory (Tables 2–4)
Declare stable GT claim IDs and predicates from the actual run records before
classifying the observations. Define what full/partial support means per claim,
including whether a proposition concerns deletion, original identity or content.
Map Static Disk, Timeline and RAM records into S/P/U/N/A with locators, missing
elements and examination state. Review the combined argument explicitly.

Derive the source-sufficient, independently corroborated, jointly sufficient
and unresolved counts using the preview's definitions and the operational rules.
Do not copy the demo totals or sum overlapping source columns. Store a minimal
human-reviewed list of claim records in the notebook; basic Python filtering
and counting is sufficient. No automatic interpretation or generic scoring engine.

Count relevant processes, sockets and validated staging artifacts with explicit
deduplication. Recovered candidates are not automatically validated artifacts;
failed/unexamined scopes are not zero. Detail tables support the four final tables.

### 7. Reference validation and replay
Trace the claim list to manifest facts and successful command/transcript records.
Keep GT support distinct from forensic support, and label assisted searches.
A derived claim sidecar may organize already-recorded facts without modifying
the original run. A missing observed fact requires a fresh instrumented run if
essential, not retrospective invention. Record capture intervals on future runs.
After review, replay the complete procedure in a selected fresh-kernel session.
Later distributions retain treatment, claim semantics and counting rules.

## Implementation discipline

Use visible standard commands and the existing `run_command` helper; preserve
full outputs in `shared/investigations/<RUN_ID>/data/` and extracted/recovered
bytes in `recovered/`. Keep new output labels distinct from orientation outputs, since ordinary draft
reruns replace a label's previous output.
Ponytail remains off for notebook/helper work. No new VM run, full-notebook run,
large framework, arbitrary positive-result target or metric redesign is needed
for the static readiness check.
