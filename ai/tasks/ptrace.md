# Ptrace — scenario preparation

## Context

Scenario: `ptrace_fa`; owner: future ptrace task; status: prepared, not launched.
Checkout: `/home/anto/linux-multisource-dfir-lab`; current stage: research.
Current run: none selected; no ptrace run was found in local
`shared/experiments/` on 2026-09-13. Notebook section/accepted sections: none.
Read [context](../CONTEXT.md), [rules](../RULES.md) and the selected stage context.

## Objective and inputs

Prepare a small process-injection case with a cited narrative and acquired
records suitable for a supervised investigation under the shared four tables.

- [Runner](../../scenarios/ptrace_fa/runner.py), [shellcode support](../../scenarios/ptrace_fa/shellcode.py)
  and [build inputs](../../scenarios/ptrace_fa/files/): actual behavior and dependencies.
- Approved preview and notebook rules linked from RULES, read-only.
- For a launched research task, 2–3 comparable primary Linux injection cases.
- Configuration/CLI help only for authorized experiments. Check configured
  storage for an existing compatible run before proposing acquisition.

## Proposed scenario claims

The following definitions derive from the current runner, not an acquired run
or forensic findings. `basis` references are run-relative templates to bind to
successful records when a run is selected. The existing identity/liveness checks
are part of the current design and have trace costs; this card adds no checks.

```json
[
  {
    "id": "binaries_installed",
    "statement": "The prepared injector and victim binaries were installed under /tmp.",
    "basis": [
      "command_log.jsonl#install_shellcode_inject_fa",
      "command_log.jsonl#install_victim"
    ],
    "basis_type": "successful_commands",
    "validation_limit": "Installation success does not independently verify final guest bytes or their persistence until acquisition."
  },
  {
    "id": "victim_started",
    "statement": "The victim process was started and its PID was captured.",
    "basis": [
      "command_log.jsonl#start_victim"
    ],
    "basis_type": "successful_command",
    "validation_limit": "The recorded launch and PID do not establish the complete process lifetime or state at capture."
  },
  {
    "id": "injector_executed",
    "statement": "The ptrace injector completed against the recorded victim PID.",
    "basis": [
      "command_log.jsonl#inject_shellcode"
    ],
    "basis_type": "successful_command",
    "validation_limit": "Injector exit status alone does not prove shellcode execution or retained injected content."
  },
  {
    "id": "reverse_shell_validated",
    "statement": "The reverse shell returned the expected execution identity.",
    "basis": [
      "command_log.jsonl#validate_reverse_shell",
      "manifest.json#scenario_facts.reverse_shell_identity"
    ],
    "basis_type": "successful_execution_and_scenario_fact",
    "validation_limit": "The scenario-defined check precedes capture; the retained connection is not independently revalidated during acquisition."
  },
  {
    "id": "victim_survived",
    "statement": "The victim passed the post-injection kill -0 check.",
    "basis": [
      "command_log.jsonl#check_victim_alive"
    ],
    "basis_type": "successful_command",
    "validation_limit": "The check concerns existence at that moment, not later process health or survival throughout acquisition."
  }
]
```

No persistence does not imply no disk evidence. An executable anonymous mapping
alone does not establish injection. Let observed records guide source selection.

## Process and write scope

1. Research comparable investigations and propose the smallest useful narrative.
2. Retain the current design where sufficient. Prepare any proposed change for
   human review before a changed experiment; never add validation-only readbacks
   to strengthen claims or anti-forensic actions merely to force a result.
3. When launched within an authorized design, reuse compatible evidence or
   prepare/build/run/acquire Ubuntu 22.04 under the experiments stage and lock.
4. Bind the scenario claims to that run and hand off the proposed first notebook
   question. Do not implement or execute notebook sections before selection.

Future outputs, not existing inputs: `investigations/ptrace/RESEARCH.md`,
`investigations/ptrace/WORKFLOW.md`, `investigations/ptrace/EXPERIMENT.md` and
bounded provenance records there, created only as needed. A launched code task
may edit `scenarios/ptrace_fa/` and relevant existing tests within its scope.
This card and new run outputs in configured lab storage belong to that owner.
Shared infrastructure, other cases, the vault and thesis are outside scope.

## Validation and endpoint

Verify citations, code changes with focused checks, and actual run/acquisition
provenance and symbols. No successful claim basis or evidence readiness is
assumed from a runner declaration. Stop at notebook selection and human review
of interpretations; report a repeated technical blocker after one bounded repair.

## Last handoff

- 2026-09-13: updated prepared card in primary checkout at HEAD `faf373c`, already dirty.
- Added five proposed source-neutral definitions from current runner actions/checks.
- Local run inventory contains no ptrace run; no run or notebook section selected.
- No research, scenario changes, VM execution or forensic work performed.
- Next: launch preparation when selected; review any design change before execution.
