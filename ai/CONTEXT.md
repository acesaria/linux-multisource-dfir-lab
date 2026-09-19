# ICM routing

Demonstrate Linux digital-forensics techniques through controlled experiments:
prepare a clean VM, execute a deterministic scenario, acquire RAM and disk,
preserve provenance, then investigate the acquired evidence manually. Compare
what is observable across Ubuntu 22.04, Ubuntu 24.04 and Debian 13 within the
tested conditions. Completion means reviewed investigations and the four shared
result tables for the planned scenarios, followed by the thesis.

The runner supplies an execution-derived reference of expected effects, not
independently verified final-state truth. [RULES.md](RULES.md) defines claims,
findings, counts, evidence protection and human review for every scenario.
Scenario claims, current runs and notebook sections belong in task cards.

## Entry

1. Read [RULES.md](RULES.md) and the selected task card.
2. Read the current stage below, then only its named inputs.
3. Complete the authorized objective and replace the card's `Last handoff`.
4. Continue within the authorized scope; stop at the stated human checkpoint.
   File existence or successful execution is not human acceptance.

For an AI-layer refactor, inspect the complete `ai/` hierarchy and root entry
points before editing. Ordinary case work keeps selective reading. Paths in
code spans are repository-relative unless labelled otherwise; Markdown links
are relative to their document. Templates describe future outputs, not existing
inputs. There is no shared progress file or automatic scheduler.

## Stages

| Work | Context | Result |
|---|---|---|
| Targeted research and narrative design | [Research](research/CONTEXT.md) | Cited findings and proposed workflow |
| Bounded implementation or AI-layer refactor | [Code](code/CONTEXT.md) | Focused, checked diff |
| VM preparation, scenario execution and acquisition | [Experiments](experiments/CONTEXT.md) | Immutable run and provenance |
| Selected notebook section and result tables | [Forensics](forensic/CONTEXT.md) | Observations and assessments for human review |

## Task cards

| Task | Card |
|---|---|
| Father | [father.md](tasks/father.md) |
| ptrace | [ptrace.md](tasks/ptrace.md) |
| Diamorphine | [diamorphine.md](tasks/diamorphine.md) |
| BadBPF | [badbpf.md](tasks/badbpf.md) |
| Shared provenance and repository consolidation | [runner-provenance.md](tasks/runner-provenance.md) |
| Investigation layer refactor (staged) | [investigation-refactor.md](tasks/investigation-refactor.md) |

Use [PROMPT_TEMPLATE.md](PROMPT_TEMPLATE.md) for a missing card or an explicitly
requested delegation; [README.md](README.md) explains handoffs. Do not load
other cases, the whole toolbox or historical reports without a concrete need.
Thesis editing is a separate human-authorized task.
