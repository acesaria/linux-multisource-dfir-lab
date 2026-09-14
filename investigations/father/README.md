# Father investigation

- [RESULTS_PREVIEW.md](RESULTS_PREVIEW.md): approved, immutable four-table gold standard; all example values are fictional.
- [investigation.ipynb](investigation.ipynb): current supervised notebook.
- [WORKFLOW.md](WORKFLOW.md): implementation sequence, including deletion recovery.
- [IMPLEMENTATION_CHECK.md](IMPLEMENTATION_CHECK.md): current practical readiness and missing inputs.
- [RECOVERY_NOTES.md](RECOVERY_NOTES.md): recovery evidence leads and bounded technique tests.
- [Investigation method](../../docs/INVESTIGATION_METHOD.md): operational and notebook rules.

Methodology was locked on 2026-09-10. No further metric-selection research.
Deletion recovery, carving and ext4 journal examination are fully in scope.
The gold standard is read-only; real results must be computed from actual records.

Use `father-u22-20260820-01` first. Preserve acquired evidence and raw exports;
write draft tool output to `shared/investigations/<RUN_ID>/data/` and extracted
bytes to `recovered/`. No full Run All until the completed notebook is reviewed.
The old disk notebook/helper and shell scripts are implementation references only;
use the unified notebook and current specification for all new work.
