# Using the ICM

This layer retains the selective reading and Inputs → Process → Outputs of
[Interpretable Context Methodology](https://github.com/RinDig/Interpretable-Context-Methodology).
It is guidance; prepared cards do not start work or grant approval.

## Responsibilities

| Location | Responsibility |
|---|---|
| [AGENTS.md](../AGENTS.md) / [CLAUDE.md](../CLAUDE.md) | Automatic entry pointers |
| [CONTEXT.md](CONTEXT.md) | Project objective, stage and task routing |
| [RULES.md](RULES.md) | Shared methodology, KISS, ownership, preservation and review |
| Stage contexts linked by the router | Only that stage's inputs, process and endpoint |
| [Task cards](tasks/) | Scenario/run, section, claims, scope, checks and handoff |
| [PROMPT_TEMPLATE.md](PROMPT_TEMPLATE.md) | A bounded task or requested delegation |
| [Toolbox](forensic/TOOLBOX.md) | Optional forensic techniques and references |
| [Investigation results contract](RULES.md#investigation-results-contract) | Immutable four-table layout; metric requirements |
| [Implementation and delivery](RULES.md#investigation-implementation-and-delivery) | Tooling, layout, precomputation, judgment, tests, commit style |
| [Investigation method](../docs/INVESTIGATION_METHOD.md) | Notebook/operational detail, subject to current RULES |

Global instructions apply to every scenario. Put scenario paths, claims and
interpretations only in its card and case material. Keep scheduling in the
existing Obsidian plan; code, evidence and results belong in the repository.

## Starting and continuing work

Name the card, bounded objective, current stage and endpoint. For forensic work,
select one notebook section and ask for a reviewable draft. After reviewing it,
explicitly accept the section and select the next one. A successful cell or a
new task does not carry forward unrecorded acceptance.

For preparation, authorize the intended scenario/acquisition design. The task
may research, implement bounded fixes and acquire within that design. A proposed
design change returns for human review before the changed experiment runs.
For a review, specify the card, section and outputs; the reviewer reports
findings without editing or executing unselected evidence work.

Use [PROMPT_TEMPLATE.md](PROMPT_TEMPLATE.md) only when a card is missing or an
explicitly requested delegation needs a bounded brief. Reuse existing handoffs;
do not create parallel progress documents or a second claim methodology.

## Checkout and handoff

Disjoint tasks share the primary checkout. Apply the worktree exception and
shared lab lock in [RULES.md](RULES.md). [.worktreeinclude](../.worktreeinclude)
carries ignored host configuration into supported worktrees; verify the actual
inputs before editing. For a manual worktree, copy only missing named inputs
from the primary checkout without replacing newer state. Do not copy evidence,
private keys or the virtual environment.

`ai/`, `AGENTS.md` and `CLAUDE.md` are tracked for review alongside the code.
Use Git commits and diffs to review changes. Report the card's path and actual outputs.
Replace its compact handoff, including checks not run and pending human review.
Freeze the reviewed ICM revision only after the human accepts it.

For an online review, start with `AGENTS.md`, `ai/CONTEXT.md`, `ai/RULES.md`
and the selected card. Run-relative links under `shared/experiments/` and local
working paths require the separately preserved evidence; they are not included
in Git. Review code and methodology without treating unavailable evidence as
verified or missing forensic support. Committing the ICM does not accept findings.
