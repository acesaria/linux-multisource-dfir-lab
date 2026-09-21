# Father — scenario claims

Scenario: `userland_father_ldpreload`. Reference run: `father-u22-20260913-01` (Ubuntu 22.04).

**This card holds the claim definitions only.** Live status, stages, the notebook blueprint and the
handoff are in [investigation-refactor.md](investigation-refactor.md); the active prompt is in
[next.md](next.md). Do not track progress here.

The runner emits these seven claims into the run manifest, which is the binding copy. They are
expected scenario effects, not forensic findings: see
[RULES.md § Execution-derived claims](../RULES.md#execution-derived-claims). User-space hiding is
live-system context outside this scored set; do not add installation, hiding or split-cleanup
claims as extra rows. Timestomping here concerns the `touch -r` operation's atime/mtime effect and
does not assert that every inode timestamp changed.

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
