# Bounded code and AI-layer changes

## Inputs

| Input | Read scope |
|---|---|
| Selected task card and [RULES.md](../RULES.md) | Objective, ownership, methodology, write scope and checks |
| Named implementation, callers and tests | Behavior affected by the requested change |
| [Repository README](../../README.md) | CLI/provenance contract only when affected |
| Existing case research/workflow | Reason for a scenario change, if proposed |

For an AI-layer refactor, read the entire actual `ai/` tree, root entry points,
all stage contexts and current cards before editing. Check their dependencies;
do not assume the root files describe the complete system.

## Process

1. Inspect actual behavior, dirty changes and ownership. Work in the primary
   checkout; apply the shared worktree exception only when needed.
2. Make the bounded diff. For AI Markdown, preserve routing and responsibility
   boundaries, centralize shared rules, remove contradictions and duplication,
   and keep claims in their scenario cards. Avoid new permanent documents unless
   an existing role or missing scenario card needs them.
3. Runner changes must preserve the distinction between successful execution
   and independently verified state. Do not add guest postcondition checks to
   strengthen claims. Prepare any design change for human review; do not silently
   change actions, existing validation behavior or acquisition design.
4. Run focused checks. For Markdown, check links, existing input paths, headings,
   claims, source neutrality and conflicting instructions. For code, test the
   changed behavior where meaningful. No extra framework or broad test campaign.
5. Record a reviewable Git diff and limits, including tracked AI files.
   Continue only through already authorized stages.

## Outputs and endpoint

- Bounded changes and compact handoff with actual checks and remaining mismatch.
- Human review before a changed-design experiment or methodology freeze.

A documentation/schema change alone does not rewrite historical manifests or
require a VM rerun. An approved change to the recorded treatment needs fresh
acquisition; preserve previous runs. Notebook code belongs to the supervised
forensic stage. Stop for unresolved write ownership or shared-infrastructure
redesign, after preparing the concrete change needed for review.
