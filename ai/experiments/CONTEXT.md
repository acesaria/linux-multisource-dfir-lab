# Controlled experiments

## Inputs

| Input | Read scope |
|---|---|
| Selected task card and [RULES.md](../RULES.md) | Scenario, distro, claim definitions, approved design and endpoint |
| Existing case workflow/code handoff | Purpose and actual implementation diff |
| [Repository README](../../README.md) and CLI help | Relevant setup/build/run/acquisition options |
| Local configuration | VM, storage, network and shared paths |

## Process

1. Keep one active reference run, normally Ubuntu 22.04. Inspect available
   records before proposing a replacement. Run only the authorized design;
   a new experiment that changes scenario actions, validation or acquisition
   requires human review first. Absence of independent postcondition checks
   is not a reason to add them. Defer distro replicas until reference results
   are complete, then retain the treatment and claim meanings across replicas.
2. Check checkout/revision, interpreter, configuration and kernel/ISF/prebuilt
   compatibility. Use the existing repository interpreter (`.venv/bin/python`;
   absolute path in a worktree). Use explicit shared storage paths rather than
   copying evidence or changing another checkout's configuration.
3. Hold a host-wide `flock` on `/tmp/linux-multisource-dfir-lab.lock` for the
   entire setup/build/run/acquisition sequence. One experiment owner uses this
   shared lock regardless of checkout count. If busy, yield.
4. Preserve exact code provenance before running: relevant dirty diff and
   hashes/copies of relevant untracked inputs in the experiment handoff. Use
   the project CLI. Acquire RAM while the VM is on, then disk after shutdown.
   Preserve commands, tool versions, timestamps, hashes, failures and logs.
5. Check actual command completion and bind scenario-specific claims to their
   successful records. Keep built-in behavioral checks within their recorded
   scope; do not label all expected effects independently verified. Confirm
   manifest/sidecar, image paths, integrity records, capture timing, symbols and
   final VM state. These host/acquisition checks are not new guest attack actions.
6. Report scenario failure, scenario-only execution without acquisition,
   acquisition failure or evidence readiness distinctly. One bounded technical
   repair/retry within the same design is allowed; a repeated failure is a
   blocker, not an invitation to alter the scenario or loop indefinitely.
7. If replacing a reference, record the old ID, reason and new evidence identity
   without changing old records. A notebook run switch must be explicit and
   requires supervised re-examination; previous acceptance does not transfer.

## Outputs and endpoint

- New immutable run under configured `shared/experiments/<RUN_ID>/` (output
  template), including claims, command records and acquisition provenance.
- Existing case experiment note or compact handoff: exact command/revision,
  dirty snapshot, selected run, identity checks and limitations.
- Evidence readiness and a proposed first notebook question for human selection.

Run supported prerequisites autonomously within the approved scope. A shared
infrastructure change needs a bounded code task. Do not add guest `stat`,
`sha256sum`, `cat` or readbacks merely to strengthen ground truth. Do not execute
forensic analysis, accept claims or advance notebook sections in this stage.
