# Father — runner claim schema and supervised investigation

## Context

Scenario: `userland_father_ldpreload`; owner: current Father runner-refactor task.
Checkout: `/home/anto/linux-multisource-dfir-lab`; stage: bounded code.
Status: runner refactor prepared for human review; investigation incomplete.
Active notebook RUN_ID: `father-u22-20260820-01` (Ubuntu 22.04), verified in the
notebook on 2026-09-13. Current section: none selected by this runner task;
section 0 has retained draft output, not acceptance recorded by this card.
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

- [Approved preview](../../investigations/father/RESULTS_PREVIEW.md): immutable layout.
- [Workflow](../../investigations/father/WORKFLOW.md), [implementation check](../../investigations/father/IMPLEMENTATION_CHECK.md)
  and [recovery notes](../../investigations/father/RECOVERY_NOTES.md): existing
  operational leads; current RULES supersede their older claim/status wording.
- [Notebook](../../investigations/father/investigation.ipynb) and
  [helper](../../investigations/father/investigation_utils.py): selected section only.
- [Active manifest](../../shared/experiments/father-u22-20260820-01/manifest.json),
  [command log](../../shared/experiments/father-u22-20260820-01/command_log.jsonl),
  [transcript](../../shared/experiments/father-u22-20260820-01/terminal_transcript.txt)
  and [acquisition sidecar](../../shared/experiments/father-u22-20260820-01/dumps/acquisition.json).
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
resolve in the [September command log](../../shared/experiments/father-u22-20260912-01/command_log.jsonl)
and [manifest](../../shared/experiments/father-u22-20260912-01/manifest.json),
whose 11 legacy claims are not this seven-claim list. The active August log has
38 records without IDs and its manifest has no claims array. Before assessing
August evidence, bind these definitions to exact August line/operation records
in a derived list with the same five fields. Never borrow September basis
records for August findings or rewrite either original manifest. A run switch
requires explicit selection and supervised re-examination.

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

1. Replace Father's eleven legacy claims with the seven exact definitions above.
2. Update the shared type and reference validator; preserve the existing JSON
   writer and `scenario_facts`. Other producers receive only required schema
   edits: renamed reference field, derivation type and non-null limits.
3. Check the exact schema and manifest serialization with mocked execution;
   compare runner code outside the claim functions with the pre-edit files.
4. Record the focused results and a separate diff against the already-dirty
   working tree, then stop for human review.

Write scope: this card, the five runners, shared claim type, manifest validator,
the two named test files and the two README contracts. No notebook/helper,
experiment, preview, vault, thesis, acquired evidence or old-manifest changes.
The existing ICM methodology is unchanged; historical shared handoffs describe
their earlier snapshots and do not supersede this selected runner task.

## Validation and endpoint

Check imports/compilation, seven unique Father IDs, exact five-field objects,
allowed derivation types, rejected missing/failed basis records, retained facts,
JSON serialization and unchanged command order, dwell and connection lifecycle.
Compare the seven objects with the supplied prompt and this card. No live VM.

Human checkpoint: review and accept the runner/schema diff and its focused
checks. A fresh Ubuntu 22.04 acquisition, run selection and notebook sections
belong to a separate task after review; do not begin them automatically.
Claims remain expected effects; reference resolution is not semantic validation
or accepted forensic support. The methodology limitation in RULES applies.

## Last handoff

- 2026-09-14: runner/provenance changes committed as `793853d`; Git consolidation targets the single local `main` branch.
- Father emits the seven exact objects above; historical manifests retain their original claims.
- The shared type and validator use the five-field schema, including scenario-fact references; the JSON writer is unchanged.
- Four sibling producers received schema migration only; their proposed card refinements remain separate review work.
- Review the committed runner, shared type/validator and tests with `git show 793853d`; no temporary local report is required.
- Latest consolidation checks: 61 scenario-runtime, forensic-contract and notebook-helper tests passed; both notebooks parse without execution.
- Source, notebook and immutable-preview hashes match the pre-consolidation working copies; no guest checks or VM actions were added by this Git task.
- Investigation documents and existing cleanup were committed separately as `ea37e18`; evidence and the active run selection are unchanged.
- ICM and automatic entry points are tracked for online review. No methodology freeze or forensic acceptance is inferred from committing them.
- Stop: review the runner/schema implementation and ICM; a fresh acquisition and notebook sections require separate selected tasks.
