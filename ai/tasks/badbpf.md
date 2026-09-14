# BadBPF — scenario preparation

## Context

Scenario: `kernel_ebpf_badbpf`; owner: future BadBPF task.
Checkout: `/home/anto/linux-multisource-dfir-lab`; stage: research.
Status: prepared, not launched. Current run: none selected; no BadBPF run was
found in local `shared/experiments/` on 2026-09-13. Notebook section/acceptance: none.
Read [context](../CONTEXT.md), [rules](../RULES.md) and the selected stage context.

## Objective and inputs

Prepare a bounded eBPF execution-hijack/process-concealment case and report its
observability through the same investigation structure and four shared tables.

- [Runner](../../scenarios/kernel_ebpf_badbpf/runner.py) and
  [scenario README](../../scenarios/kernel_ebpf_badbpf/README.md): existing payload,
  trigger, process-label, controlled-pool and visibility behavior.
- Approved preview and operational notebook rules linked from RULES, read-only.
- Configuration, pinned build inputs and matching kernel symbols only for the
  launched task. Locate compatible evidence before proposing a new reference run.

## Proposed scenario claims

These definitions derive from the current runner's actions and existing checks.
`basis` references are run-relative templates pending an acquired run with
successful records. Existing /proc readbacks and visibility checks have trace
costs; this card neither adds nor removes them. Review live-check claims for
post-mortem assessment without assuming their source applicability.

```json
[
  {
    "id": "payload_installed",
    "statement": "The prepared XCrypto payload was installed at /a.",
    "basis": [
      "command_log.jsonl#install_xcrypto"
    ],
    "basis_type": "successful_command",
    "validation_limit": "Installation completion does not independently verify final guest bytes or their persistence until acquisition."
  },
  {
    "id": "execution_hijacked",
    "statement": "The uptime trigger launched XCrypto, confirmed by the hijack log and /proc executable link.",
    "basis": [
      "command_log.jsonl#trigger_hijack",
      "command_log.jsonl#read_exechijack_log",
      "command_log.jsonl#resolve_worker_executable"
    ],
    "basis_type": "successful_commands",
    "validation_limit": "The existing scenario checks precede acquisition and do not establish the complete lifetime of the hijack."
  },
  {
    "id": "worker_masqueraded",
    "statement": "The worker used the uptime argv0 and kworker/u8:2 comm.",
    "basis": [
      "command_log.jsonl#read_worker_identity",
      "manifest.json#scenario_facts.worker_comm"
    ],
    "basis_type": "successful_execution_and_scenario_fact",
    "validation_limit": "These are process labels, not kernel-worker identity; continued labels at capture are not independently verified."
  },
  {
    "id": "simulated_pool_exchange",
    "statement": "The worker exchanged the expected messages with the controlled simulated pool.",
    "basis": [
      "command_log.jsonl#validate_xcrypto_pool",
      "manifest.json#scenario_facts.simulated_pool_marker",
      "manifest.json#scenario_facts.simulated_pool_reply"
    ],
    "basis_type": "successful_execution_and_scenario_fact",
    "validation_limit": "This is a controlled simulated pool exchange, not actual mining or a backdoor; later traffic is not established."
  },
  {
    "id": "worker_hidden",
    "statement": "The worker disappeared from the tested /proc listing after pidhide started.",
    "basis": [
      "command_log.jsonl#list_worker_before",
      "command_log.jsonl#list_worker_after"
    ],
    "basis_type": "successful_commands",
    "validation_limit": "The existing hiding check is limited to the tested /proc enumeration, not every process view or later state."
  },
  {
    "id": "hidden_worker_accessible",
    "statement": "The hidden worker and pidhide passed liveness checks, and direct worker status access returned data.",
    "basis": [
      "command_log.jsonl#check_worker_and_pidhide_alive",
      "command_log.jsonl#read_hidden_worker_status"
    ],
    "basis_type": "successful_commands",
    "validation_limit": "These checks occur before capture; continued execution throughout acquisition is not independently checked."
  }
]
```

## Process and write scope

1. Research comparable eBPF cases and propose a small question-led narrative.
2. Bind the reviewed definitions to the selected run's successful records; keep
   semantic and final-state limits explicit. Propose design changes for review.
3. When launched within an authorized design, check kernel/prebuilt/symbol
   compatibility and acquire through the experiments stage and shared lock.
4. Hand off evidence readiness and the proposed first notebook question.

Future outputs, not existing inputs: bounded research/workflow/experiment notes
under `investigations/badbpf/`, and new runs in configured lab storage. A launched
code task may edit `scenarios/kernel_ebpf_badbpf/` and relevant existing tests;
this card belongs to that case owner. Shared infrastructure, other cases,
acquired evidence, vault and thesis remain outside the write scope.

## Validation and endpoint

Check citations, focused code changes if any, compatibility, run provenance and
actual basis references. Keep the controlled pool distinct from real mining or
a backdoor; eBPF presence alone does not establish malicious behavior. Stop at
human review before a changed-design experiment, notebook advancement or
acceptance of a supported forensic claim.

## Last handoff

- 2026-09-13: created missing card in primary checkout at HEAD `faf373c`, already dirty.
- Six proposed definitions inspected against current runner actions/checks.
- No acquired local run selected; no notebook section or accepted findings.
- No research, build, VM action or forensic execution performed by this refactor.
- Next: review ICM, then launch bounded preparation when selected.
