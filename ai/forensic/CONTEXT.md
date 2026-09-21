# Supervised investigation and results

## Inputs

| Input | Read scope |
|---|---|
| Selected task card | Active run, section, scenario claims, accepted work and write scope |
| [RULES.md](../RULES.md) | Claim/finding distinction, six statuses, four tables, counts and review |
| [Results contract](../RULES.md#investigation-results-contract) | The four table layouts and metric definitions |
| [Notebook style and iteration](../../docs/INVESTIGATION_METHOD.md#notebook-style-and-iteration) | Visible commands, minimal Python, draft-output policy |
| Case workflow and notebook | Selected section and necessary dependencies |
| Selected manifest, command log and acquisition sidecar | Execution basis, evidence identity, images, hashes, timing and symbols |
| [Toolbox](../../docs/linux-dfir-toolbox.md) | Needed technique and its cited source only |

## Process

1. Confirm the user-selected section and active RUN_ID. If no section is
   selected, propose the next question and stop before writing/running cells.
   Claims guide questions, not findings or source eligibility. For older logs,
   bind claims to exact preserved records without changing those records.
2. Build the section as question → visible command → output → manual
   observation/interpretation/limit → next investigative question. Record the
   command and evidence locator; preserve full stdout/stderr behind bounded
   displays. Do not invent missing results or silently transfer old acceptance.
3. Run forensic tools only against acquired evidence or read-only derivatives:
   for example `mmls`, `fls`, `istat`, `icat`, `find`, `stat`, `sha256sum`, Plaso,
   Volatility and bounded recovery/carving tools. Save outputs separately. Use
   image-aware tools by default; any necessary mount must prevent journal replay.
   These are examiner commands, never additions to the VM scenario.
4. Record separate findings with the fields/statuses in RULES. Consider relevant
   RAM strings, paths, content and runtime objects even for a file-related claim.
   Scope Plaso extraction and retain original record locators: another rendering
   of an inode is not independent corroboration of that inode.
5. Validate only the selected section and prerequisites. Show draft assessments
   for human review; a successful command/cell does not establish a claim.
   Record acceptance only after the human provides it, then stop before the next
   section. Never delegate later sections or execute an unfinished notebook whole.

## Investigation coverage

Adapt the narrative to the case: evidence identity/acquisition metadata; disk;
timeline; logs and shell history; RAM; manual claim assessment; result tables.
Plaso supplies the required temporal examination, with explicit parser scope.
This is a coverage guide, not a requirement to replace an existing useful order.

Deletion recovery remains in scope. Use 2–3 complementary targeted techniques
where relevant: journal/inode reconstruction, unallocated-space carving and
optional separately attributed RAM content. Keep content recovery, metadata-only
traces, bounded negatives, unexamined scope and tool failures distinct. A missing
entry or failed recovery tool is not proof of deletion or non-recoverability.

## Outputs and endpoint

- Selected section, full draft command output, locators and interpretations.
- Reviewed finding records feed the four approved tables; simple cells count
  unique claim/source assessments and deduplicated objects under RULES.
- Handoff: actual checks, limits, proposed next question and exact review point.

Do not accept support, deletion interpretations or final scientific conclusions
on the human's behalf. Results and full fresh-kernel replay each require their
selected review task. No automatic scoring, guest validation or forced recovery.
