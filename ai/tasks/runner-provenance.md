# Shared provenance and repository consolidation

## Context

Scope: shared maintenance; scenario/run and notebook section: not applicable.
Owner: supervising task in `/home/anto/linux-multisource-dfir-lab`.
Current stage: code; online methodology review remains pending.
Read [context](../CONTEXT.md), [rules](../RULES.md) and [code](../code/CONTEXT.md).

## Objective and inputs

The user requested two or three logical commits of the pending work, tracking
`ai/` for online review, and consolidation onto one clean local `main` branch.
Inputs: pending Git changes and branch histories; the ICM tree and its
[AGENTS.md](../../AGENTS.md) / [CLAUDE.md](../../CLAUDE.md) entry points;
[repository README](../../README.md); the runner/provenance implementation,
investigation documents and their existing focused tests.

Scenario claims belong in [Father](father.md), [ptrace](ptrace.md),
[Diamorphine](diamorphine.md) and [BadBPF](badbpf.md), not in this shared card.

## Process and write scope

1. Inspect the complete pending inventory and local branch ancestry. Preserve
   existing source changes, notebook contents, evidence and historical commits.
2. Group commits into execution/acquisition provenance, supervised Father
   investigation cleanup, and tracked ICM plus branch consolidation.
3. Track `ai/`, `AGENTS.md` and `CLAUDE.md`; update their former ignored-file
   instructions. Keep evidence, private configuration and environments ignored.
4. Bring `main` forward and reconcile the superseded BadBPF branch history
   while retaining the newer integration already present in the current code.
   Remove local branch names only after their tips are reachable from `main`.
5. Verify the clean checkout, tracked review inputs and focused tests.

Write scope: commits of all existing pending changes, the tracking rules,
review-routing documentation and local Git branches. No new VM experiment,
notebook execution, evidence modification, thesis edit or forensic acceptance.
No remote push or remote branch deletion is included in this local task.

## Implementation and review limits

The [shared claim type](../../scenarios/command_log.py) now uses the five-field
model in RULES, including `basis`, `basis_type` and string validation limits.
The [Father runner](../../scenarios/userland_father_ldpreload/runner.py) emits
exactly the seven definitions in its card. The manifest validator resolves
successful execution records and scenario facts; reference resolution does not
establish independently verified final-state truth.

Other runners received the shared-schema migration while retaining their
existing claim IDs, statements and basis targets. Their proposed task-card
refinements still need case-specific review; they are not all identical to the
runner declarations. Historical manifests are unchanged.

The acquisition changes retain stable command IDs, UTC capture boundaries,
partial failure records and logical-disk SHA-256. Existing guest behavioral
checks remain part of the scenario design. The four-table preview is immutable.
Online reviewers can inspect the tracked code, cards and notebook drafts;
run-relative evidence links require separately provided local evidence.

## Validation and endpoint

Run the existing scenario-runtime, forensic-contract and notebook-helper unit
tests; check Python/notebook syntax, whitespace, tracked ICM links and unchanged
notebook/evidence inputs. No full notebook replay or live VM test.
Endpoint: three logical commits on clean local `main`, with all previous local
branch tips preserved in its ancestry. Online methodology/forensic review and
any later acquisition remain separate tasks; Git commits do not record acceptance.

## Last handoff

- 2026-09-14: primary checkout; consolidation from `public-surface-cleanup` at base `faf373c`.
- Selected three groups: execution/acquisition provenance; Father investigation cleanup; tracked ICM and branch history.
- Validation: 61 existing focused tests passed in 0.68s; no VM or full notebook execution.
- Track all 14 ICM Markdown files and both automatic entry points; evidence and private host configuration stay ignored.
- Retain the newer BadBPF integration from `94f5d69` while preserving original branch history from `55a8db6`.
- Remove redundant local branch names after ancestry checks; preserve remote refs and the existing stash.
- No new methodology freeze, accepted forensic finding or active-run switch is recorded.
- Next: online review of the committed revision; pushing or remote branch cleanup requires a separate request.
