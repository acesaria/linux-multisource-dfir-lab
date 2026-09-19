# Father — runner claim schema and supervised investigation

## Context

Scenario: `userland_father_ldpreload`; owner: current Father runner-refactor task.
Checkout: `/home/anto/linux-multisource-dfir-lab`; stage: bounded code.
Status: runner refactor committed; investigation in progress (Section 1 complete, pending review).
Active notebook RUN_ID: `father-u22-20260913-01` (Ubuntu 22.04), selected in the
notebook. Current section: Section 1 complete, pending human review.
Read [global context](../CONTEXT.md), [rules](../RULES.md) and [code](../code/CONTEXT.md).

## Objective and inputs

Emit exactly the seven claim objects below using only `id`, `statement`,
`basis`, `basis_type` and `validation_limit`. Keep scenario commands, order,
dwells, cleanup and the retained backdoor connection unchanged. No guest-side
validation commands, compatibility reader, source hints or old-schema output.
The user's 2026-09-13 request is captured in the seven definitions below and
this bounded scope; no external prompt file is needed to review the implementation.

- [Father runner](../../scenarios/userland_father_ldpreload/runner.py).
- [Shared claim type](../../scenarios/command_log.py) and
  [manifest validation/serialization](../../orchestrator/core/orchestrator.py).
- Shared type callers: [interactive shell](../../scenarios/interactive_shell/runner.py),
  [ptrace](../../scenarios/ptrace_fa/runner.py),
  [Diamorphine](../../scenarios/kernel_diamorphine/runner.py) and
  [BadBPF](../../scenarios/kernel_ebpf_badbpf/runner.py); migrate their schema only.
- [Runtime tests](../../tests/test_scenario_runtime.py) and
  [claim-reference tests](../../tests/test_forensic_contracts.py).
- [Repository contract](../../README.md) and
  [Father contract](../../scenarios/userland_father_ldpreload/README.md).

## Investigation context after review

The following inputs belong to a later selected forensic task under
[forensics](../forensic/CONTEXT.md); this runner task does not execute them.
Complete the four tables from reviewed evidence under the shared methodology.
Deletion recovery includes bounded journal/inode reconstruction, targeted
unallocated-space carving and an optional RAM complement.

- [Investigation results contract](../RULES.md#investigation-results-contract): immutable four-table layout and metric requirements.
- [Investigation method](../../docs/INVESTIGATION_METHOD.md): existing operational leads; current RULES supersede older claim/status wording.
- [Notebook](../../investigations/father/investigation.ipynb) and
  [helper](../../investigations/father/investigation_utils.py): selected section only.
- [Active manifest](../../shared/experiments/father-u22-20260913-01/manifest.json),
  [command log](../../shared/experiments/father-u22-20260913-01/command_log.jsonl),
  [transcript](../../shared/experiments/father-u22-20260913-01/terminal_transcript.txt)
  and [acquisition sidecar](../../shared/experiments/father-u22-20260913-01/dumps/acquisition.json).
  Images named by the sidecar and existing raw exports remain read-only.
- [Current runner](../../scenarios/userland_father_ldpreload/runner.py): design
  and stable event IDs, never evidence of an older run's execution.

## Seven scenario claims

These are the user's seven expected-effect definitions, not supported forensic
findings. User-space hiding remains live-system scenario context outside this
scored set. Do not add installation, hiding or split cleanup claims
as extra scored rows. Timestomping here concerns the `touch -r` operation's
atime/mtime effect; it does not assert that every inode timestamp changed.

The following `basis` references are run-relative stable-ID definitions. They
resolve in the [active command log](../../shared/experiments/father-u22-20260913-01/command_log.jsonl)
and [manifest](../../shared/experiments/father-u22-20260913-01/manifest.json).
The manifest's legacy 11-claim array is not this seven-claim list; use these
seven definitions for all forensic assessment. A run switch requires explicit
selection and supervised re-examination.

```json
[
  {
    "id": "preload_persistence",
    "statement": "/etc/ld.so.preload was configured to load /lib/selinux.so.3.",
    "basis": [
      "command_log.jsonl#write_preload"
    ],
    "basis_type": "successful_command",
    "validation_limit": "The file content was not read back inside the guest."
  },
  {
    "id": "implant_timestomp",
    "statement": "The timestamps of /lib/selinux.so.3 were modified using the timestamps of the system libc.",
    "basis": [
      "command_log.jsonl#timestomp_implant"
    ],
    "basis_type": "successful_command",
    "validation_limit": "No timestamp readback was performed; the final timestamp relationship is not independently verified."
  },
  {
    "id": "credential_staging",
    "statement": "/etc/shadow was copied to /tmp/__malicious_harvest with mode 0600.",
    "basis": [
      "command_log.jsonl#harvest_shadow"
    ],
    "basis_type": "successful_command",
    "validation_limit": "The copied content was not read back or independently verified."
  },
  {
    "id": "runtime_loading_backdoor",
    "statement": "The scenario activated and validated the backdoor, with the connection retained until memory acquisition.",
    "basis": [
      "command_log.jsonl#restart_ssh",
      "command_log.jsonl#validate_backdoor",
      "manifest.json#scenario_facts.backdoor_connection"
    ],
    "basis_type": "successful_execution_and_scenario_fact",
    "validation_limit": "The forensic conclusion concerns the state observable near memory acquisition and does not establish the complete historical lifetime of the runtime activity."
  },
  {
    "id": "deleted_staging_artifact",
    "statement": "The staged /tmp/rk.so file was unlinked during scenario cleanup.",
    "basis": [
      "command_log.jsonl#remove_staged_implant"
    ],
    "basis_type": "successful_command",
    "validation_limit": "The command log establishes an unlink operation, not successful erasure or post-mortem recoverability."
  },
  {
    "id": "recon_staged",
    "statement": "Reconnaissance output was written to /tmp/__malicious_recon.",
    "basis": [
      "command_log.jsonl#recon_identity",
      "command_log.jsonl#recon_kernel",
      "command_log.jsonl#recon_os",
      "command_log.jsonl#recon_accounts"
    ],
    "basis_type": "successful_commands",
    "validation_limit": "The final file contents were not read back inside the guest."
  },
  {
    "id": "shell_history_cleanup",
    "statement": "The scenario attempted to clear shell history, remove the history file, and unset HISTFILE.",
    "basis": [
      "command_log.jsonl#clear_history",
      "command_log.jsonl#remove_history_file",
      "command_log.jsonl#unset_histfile"
    ],
    "basis_type": "successful_commands",
    "validation_limit": "Absence of history entries or files does not prove complete history erasure."
  }
]
```

Successful cleanup is the reference for an expected unlink effect; it does not
independently establish prior existence, complete erasure or recoverability.
Existing scenario behavioral checks remain disclosed execution context.

## Process and write scope

Runner refactor committed (`793853d`). Investigation is the active task.

1. Complete notebook sections one at a time under [forensic/CONTEXT.md](../forensic/CONTEXT.md).
2. Each section: propose → build cells → human review → accept → next.
3. After all sections: populate the four result tables and compute metrics per
   [RULES.md § Investigation results contract](../RULES.md#investigation-results-contract).

Write scope: `investigations/father/investigation.ipynb`,
`investigations/father/investigation_utils.py`, this card's handoff,
and findings under `shared/experiments/father-u22-20260913-01/investigation/`.
No runner, manifest, evidence, thesis or shared-type changes.

## Current status

| Section | Status |
|---|---|
| 0. Evidence orientation | ✅ retained draft output |
| 1. Ordinary disk examination | ✅ complete, pending human review |
| 2. Surrounding activity | not started |
| 3. Memory analysis | not started |
| 4. Deletion recovery | not started |
| 5. Chronology | not started |
| 6. Result tables | not started |
| 7. Ground-truth validation | not started |

## Last handoff

- 2026-09-16: Section 1 consolidated into 7 blocks; libc comparison removed;
  observation record created at `investigation/findings/section1-disk-observations.md`.
- ICM cleaned: all broken links to deleted files (RESULTS_PREVIEW, WORKFLOW,
  RECOVERY_NOTES, IMPLEMENTATION_CHECK) replaced with RULES.md anchors.
- RUN_ID corrected to `father-u22-20260913-01` throughout.
- Notebook JSON and Python syntax validated. 11 stale data files removed.
- Stop: human review of Section 1 before starting Section 2.

