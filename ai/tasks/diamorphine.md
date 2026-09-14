# Diamorphine — scenario preparation

## Context

Scenario: `kernel_diamorphine`; owner: future Diamorphine task.
Checkout: `/home/anto/linux-multisource-dfir-lab`; stage: research.
Status: prepared, not launched. Current run: none selected; no Diamorphine run
was found in local `shared/experiments/` on 2026-09-13. Notebook section/acceptance: none.
Read [context](../CONTEXT.md), [rules](../RULES.md) and the selected stage context.

## Objective and inputs

Prepare a bounded kernel-module case, acquire within an authorized design, then
use the shared investigation structure and four tables with this scenario's claims.

- [Runner](../../scenarios/kernel_diamorphine/runner.py) and
  [scenario README](../../scenarios/kernel_diamorphine/README.md): module loading,
  reconnaissance note, signal-64 helper and existing visibility checks.
- Approved preview and operational notebook rules linked from RULES, read-only.
- Configuration, pinned build inputs and matching kernel symbols only when needed
  for a launched code/experiment task. Locate compatible evidence before a new run.

## Proposed scenario claims

These definitions derive from existing deterministic actions and checks.
`basis` references are run-relative templates, not evidence of an executed run.
Review their post-mortem meaning when binding the selected run; live listing
checks do not automatically become recovered hiding evidence. Existing readback
and enumeration checks are disclosed design activity, not new commands to add.

```json
[
  {
    "id": "reconnaissance_note_created",
    "statement": "Reconnaissance output was written to the scenario note file.",
    "basis": [
      "command_log.jsonl#write_recon_note"
    ],
    "basis_type": "successful_command",
    "validation_limit": "The later scenario-defined access check does not establish content persistence throughout acquisition."
  },
  {
    "id": "module_loaded",
    "statement": "insmod completed for the prepared Diamorphine module.",
    "basis": [
      "command_log.jsonl#load_module"
    ],
    "basis_type": "successful_command",
    "validation_limit": "Successful insmod does not independently establish every hook effect or continued residency at capture."
  },
  {
    "id": "directory_hidden",
    "statement": "The reconnaissance directory disappeared from the tested parent listing after module loading.",
    "basis": [
      "command_log.jsonl#list_parent_before",
      "command_log.jsonl#list_parent_after"
    ],
    "basis_type": "successful_commands",
    "validation_limit": "Expected hiding is limited to the tested parent listing; it does not establish every enumeration view or later state."
  },
  {
    "id": "file_hidden",
    "statement": "The reconnaissance file disappeared from the tested directory listing after module loading.",
    "basis": [
      "command_log.jsonl#list_directory_before",
      "command_log.jsonl#list_directory_after"
    ],
    "basis_type": "successful_commands",
    "validation_limit": "Expected hiding is limited to the tested directory listing, not all access methods or the complete runtime lifetime."
  },
  {
    "id": "hidden_note_accessible",
    "statement": "The hidden reconnaissance note remained readable through its known path.",
    "basis": [
      "command_log.jsonl#read_hidden_note"
    ],
    "basis_type": "successful_command",
    "validation_limit": "The existing direct-access check is before acquisition and does not establish later availability."
  },
  {
    "id": "signal_64_privilege_change",
    "statement": "The signal-64 helper changed from a non-root UID to UID 0.",
    "basis": [
      "command_log.jsonl#signal_64_helper",
      "manifest.json#scenario_facts.signal_64_identity_before",
      "manifest.json#scenario_facts.signal_64_identity_after"
    ],
    "basis_type": "successful_execution_and_scenario_fact",
    "validation_limit": "The helper is short-lived; continued presence at memory capture is not claimed."
  },
  {
    "id": "module_hidden",
    "statement": "Diamorphine was absent from the tested lsmod output.",
    "basis": [
      "command_log.jsonl#load_module",
      "command_log.jsonl#list_modules"
    ],
    "basis_type": "successful_commands",
    "validation_limit": "The existing check concerns lsmod only, not absence from other kernel views or final-state persistence."
  }
]
```

## Process and write scope

1. Research comparable kernel-module cases and propose the investigation questions.
2. Review this claim list against the selected design and actual successful
   records. Keep missing validation explicit; prepare design changes for review.
3. When launched within an authorized design, check module/kernel compatibility
   and acquire the reference run through the experiments stage and shared lock.
4. Hand off evidence readiness, limits and the first notebook question for selection.

Future outputs, not existing inputs: bounded research/workflow/experiment notes
under `investigations/diamorphine/`, plus new runs in configured lab storage.
A launched code task may edit `scenarios/kernel_diamorphine/` and its relevant
existing tests; this card belongs to that case owner. Shared infrastructure,
other cases, acquired evidence, vault and thesis remain outside the write scope.

## Validation and endpoint

Check sources, focused code changes if any, build/kernel/symbol compatibility,
run provenance and the actual claim basis. A module-view discrepancy needs
interpretation; do not automatically call it hiding. Stop before a changed-design
experiment or an unselected notebook section, and before accepting claim support.

## Last handoff

- 2026-09-13: created missing card in primary checkout at HEAD `faf373c`, already dirty.
- Seven proposed definitions inspected against current runner actions/checks.
- No acquired local run selected; no notebook or accepted forensic conclusions.
- No research, build, VM action or forensic execution performed by this refactor.
- Next: review ICM, then launch bounded preparation when selected.
