# Investigation method

Methodology approved and locked by the user on 2026-09-10.
The [investigation results contract](../ai/RULES.md#investigation-results-contract) is
the sole results specification and must not be edited. Its four tables and definitions
are binding; its example values and observations are fictional.
This document supplies execution, provenance and notebook rules, not another
metric-selection proposal. Deletion recovery is fully in scope.

## Sequence

1. Study 2–3 authoritative similar investigations. Compare their investigative
   pivots, source use and limits; adapt live techniques to acquired evidence.
2. State lab assumptions and propose a question-led narrative. Change a case
   when a meaningful question or missing ground-truth fact requires it; record
   each new run's actual revision and acquisition, following the lifecycle below.
3. Examine one notebook section at a time with the human. Evidence drives the
   next pivot: question → technique → output → interpretation → next question.
4. Define each GT claim from trustworthy run records, then manually assess the
   forensic support in the three lenses and their combination. Populate all four
   locked tables from these reviewed records; calculate their counts simply.
5. Keep laboratory validation distinct from forensic observations, then replay
   the accepted procedure on another run if useful. Recheck every verdict.

## Run lifecycle

- During development, keep **one active frozen RUN_ID per scenario**, normally
  Ubuntu 22.04. Frozen means an immutable acquired snapshot, not a permanent ban
  on improving the runner. This applies to Father as well as subsequent cases.
- A runner change affecting actions, validation or recorded ground truth makes
  the current RUN_ID unsuitable as the reference for the revised design.
  Execute the scenario and acquire fresh RAM/disk under a new RUN_ID.
- The user reports roughly 2–3 minutes for scenario execution plus acquisition;
  necessary reruns are preferable to preserving a deficient experiment. This
  estimate excludes preparation/build work and notebook review.
- Examples: record a missing ground-truth fact in Father; add a small ptrace
  cleanup/anti-forensic action when it supports a useful investigative question.
  Explain the change and its trace effects; do not add actions to force a score.
- Preserve previous evidence and logs unchanged. Record the superseded ID,
  reason, revision and validated replacement in the case task/experiment note.
  Never backfill the new ground truth into an old run or mix different runs.
- Switch the notebook to the validated replacement explicitly. Previous outputs
  and section acceptance belong to their original RUN_ID; reuse clear methods,
  but re-examine the replacement with the human section by section.
- Produce the complete notebook and real tables on that one reference run
  before acquiring/refreshing other distro replicas. Then hold the treatment
  and ground-truth definitions fixed across replicas. Older existing runs remain
  historical material; reuse them only if their design/provenance is compatible.

## Evidence and interpretation

- Disk and RAM are acquisitions; Plaso provides a temporal view of underlying
  artifacts. Plaso is required for temporal examination in this project.
- Document evidence integrity, partition/offset, tool versions, clock/timezone
  assumptions and the gap between RAM capture and disk acquisition.
- Preserve original evidence and accepted raw exports. Draft outputs follow the
  iteration policy below; display bounded output and retain full command output.
- Record observations, inferences and assumptions distinctly, with locators.
  Ground truth can validate an account, not replace missing forensic evidence.
- Disclose prior scenario knowledge and assisted searches. Research/design is
  scenario-aware; the resulting investigation must not claim to be blinded.
- Distinguish absent artifact, not observed within scope, not examined, missing
  input, partial content and tool failure. None silently becomes zero.
- State timestamp semantics and uncertainty. A timestamp anomaly alone does
  not prove tampering; offline visibility alone does not prove live hiding.
- Mount only when an examination needs it: read-only, with filesystem-specific
  journal-replay prevention. Image-aware tools are the simpler default.
- Deleted-file recovery is part of the investigation: inode/journal examination,
  bounded carving and, when useful, separately attributed RAM-resident content.
  Names/journal metadata are not recovered content. No baseline is assumed.
  Research techniques briefly, test actual image/tool compatibility, and retain
  successful, partial, negative and failed attempts with their exact scope.

## Notebook style and iteration

The notebook should read like a practical terminal investigation with Python
support. The forensic question, command, output and interpretation are the main
content. These rules apply to helper modules as well as visible cells.

- Within the selected section, replace draft code freely when a clearer design
  needs it. Optimize readability of the result, not the number of changed lines.
- Show important tool invocations explicitly. Prefer a named command string
  followed by execution when that best exposes the technique. For example,
  after the executor supports command strings (illustrative, not a current API):

  ```python
  create_body_cmd = f'fls -r -m / -o {ROOT_OFFSET} "{DISK_IMAGE}"'
  body = run_command(create_body_cmd, label="filesystem.body")
  ```

  For simple commands, ordinary argument splitting inside the helper is enough;
  do not invent a shell parser. Quote paths correctly; treat actual shell
  operators explicitly if needed. An argument list is fine when clearer.
- Every extra variable, helper, branch or artifact must have a concrete purpose:
  parameterizing RUN_ID/evidence, answering the current question, retaining its
  output, or calculating a selected result. Remove speculative machinery.
- Keep execution helpers small and direct: invoke, show/capture output, report
  failure and return the result. No generic pipeline, command registry, report
  framework or helper hierarchy. Length is a review signal, not a line-count cap.
- Routine cell reruns must work. Reuse stable filenames and replace that cell's
  **unaccepted draft outputs**, including draft binary extractions; no collision
  exception, mandatory setup restart, overwrite switch or automatic version tree.
  Accepted evidence/exports remain immutable. Before accepting results, preserve
  a coherent examination snapshot and continue edits in a separate draft location.
- Draft files represent the latest invocation, not immutable execution history.
  Keep displayed output/locators consistent; do not point historical log entries
  at overwritten files as if those files still held the earlier invocation.
- Preserve full stdout/stderr and distinguish a failed command from no findings.
  Use ordinary tool/Python errors; add assertions or custom handling only for a
  concrete integrity, wrong-input or data-loss risk. File existence during a
  normal rerun is not an error. Essential image/hash verification remains DF work.
- Record run/image identity, relevant integrity checks, versions and time context
  once at the appropriate step. Extra hashes, per-call environment inventories,
  JSON audit logs and repeated preflight checks need a specific scientific use.
- Reuse only helpers that simplify current calls. The preserved source notebook
  is a reference, not a requirement to retain its unused framework or interfaces.
  Replace tests that enforce obsolete complexity; verify cheap cell/helper reruns
  and meaningful failure handling without executing unselected forensic sections.

## Locked results: implementation rules

Use the exact columns, support statuses and contribution definitions in the
gold standard. No metric-selection research or alternative scoring documents.
An uncalculable detail requires a small explicit implementation accommodation,
not a new methodology. Never alter the protected preview to make results fit.

1. **Chronology:** use acquired records with timestamp meaning, original locator,
   uncertainty and relative ordering where absolute precision is unavailable.
   Scenario command times cannot substitute for a missing forensic event.
2. **Claim Coverage & Source Support:** give each GT claim a stable ID, an exact
   proposition and a run-record reference. Define what establishes that claim
   before assigning S/P/U/N/A. Record the missing element for P; reserve N/A for
   genuine non-applicability. Unexamined input and failed tools remain explicit
   examination states in the note, not silently completed negative searches.
3. **Multi-Source Contribution:** derive source-sufficient counts from reviewed
   S entries. Corroboration requires independently sufficient underlying records;
   Static Disk and Timeline parsing the same record is one origin. Joint support
   requires an explicit combined argument and no independently sufficient lens;
   two P entries do not automatically establish a claim. Source totals overlap
   and must not be added as if mutually exclusive. Unresolved claims have no
   sufficient single or combined account. Pending examinations are disclosed;
   no final numeric row is presented as complete while its inputs are pending.
4. **Footprint Inventory:** count distinct relevant process identities, socket
   objects and validated staging artifacts. Document process/PID reuse, shared
   descriptors, inode/hard-link identity, and recovered-copy deduplication.
   Define the preview's process label by the evidence actually established;
   mapping a library alone does not prove that every process executed a hook.

Deletion recovery feeds the existing tables. A name/inode trace, a reconstructed
file and a demonstrated deletion action are distinct observations. Assess each
against the actual claim predicate: missing content does not automatically
invalidate independently proven deletion, and matching bytes alone do not prove
the original path or deletion history. Place method, provenance, content extent,
validation and failed/negative scope in the supporting detail and table notes.
Do not turn a recovered library into a staging-artifact count unless that role
is established. Keep raw carver output and any bounded derivative separately.

The preview's illustrative deletion-recovery exclusion is superseded by the
2026-09-10 user directive. Its illustrative rows are not an acceptance fixture:
recompute real totals from the real claim table and independent origins.

One reference run per scenario supports case-specific reporting. Later replicas
use the same treatment and claim definitions; explain applicability changes and
observed differences without treating one run per distro as a statistical effect.
