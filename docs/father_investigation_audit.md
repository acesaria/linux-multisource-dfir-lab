# Father Investigation Directory Audit

## Scope and constraints

This is a read-only audit of `investigations/father/`. No repository files were edited, deleted, moved, or committed.

The intended final design is:

- Git-tracked reusable assets:
  - `investigations/father/investigation.ipynb`
  - `investigations/father/investigation_utils.py`, only if genuinely used
  - `investigations/father/README.md`
- Run-specific evidence and generated findings:
  - `experiments/<RUN_ID>/`
- The reusable notebook selects the run through one top-level `RUN_ID` variable and derives all selected-run paths from it.
- Methodology belongs in `ai/`.
- The four result tables must not be redesigned or modified.

## Overall assessment

`investigations/father/` currently contains two competing investigation systems:

1. The intended reusable workflow: `investigation.ipynb`, supported by the small helper module `investigation_utils.py`.
2. An older workflow consisting of a second disk notebook, phase-specific shell scripts, separate metrics/findings/report handling, and duplicate methodology and project-status documents.

This does not match the intended final design. The Father directory should contain reusable assets only. Per-run evidence, tool output, recovered artifacts, findings, metrics, and reports should be stored beneath the selected `experiments/<RUN_ID>/` directory.

There is also a documentation conflict:

- `README.md` identifies `investigation.ipynb` as the current supervised notebook.
- `disk_investigation.ipynb` describes itself as the single canonical disk workflow.

Only `investigation.ipynb` should remain canonical.

## 1. What each file does

| File | Current purpose | Assessment |
|---|---|---|
| `README.md` | Directory landing page. It links to notebooks, workflow documents, readiness checks, recovery notes, preview tables, and an external method document. | Useful as a concise landing page, but currently links to duplicate methodology and describes obsolete output locations. |
| `WORKFLOW.md` | Detailed Father investigation methodology and execution sequence, including disk, RAM, timeline, recovery, claims, and the four tables. | Methodology documentation. It should live in `ai/`, not in `investigations/father/`. |
| `IMPLEMENTATION_CHECK.md` | Readiness assessment for a particular implementation state and named run. It identifies missing work and cautions. | Historical project-status material, not reusable investigation code or essential run evidence. |
| `RECOVERY_NOTES.md` | Detailed deletion-recovery plan, technique selection, tool notes, artifact references, and table-interpretation rules. | Methodology mixed with run-specific operational notes. It should not remain in the reusable Father directory. |
| `RESULTS_PREVIEW.md` | Defines the four locked example result tables and their meaning, while marking values fictional. | Useful specification content, but it belongs in `ai/`, not in `investigations/father/`. |
| `investigation.ipynb` | Partially implemented unified Father notebook. It includes orientation, acquisition-integrity work, partial disk examination, and placeholders for RAM, timeline, recovery, result tables, and validation. | This is the notebook to retain and complete. It currently hard-codes a run ID and legacy `shared/...` paths, which must later be corrected. |
| `disk_investigation.ipynb` | A second, more extensive disk-focused notebook. It attempts disk analysis, recovery, journal examination, metrics generation, and report generation. | Competing and obsolete as a canonical workflow. Some cells are useful source material for the unified notebook. |
| `investigation_utils.py` | Helper functions for command execution, checksums, TSK parsing, root filesystem discovery, EWF verification parsing, timestamp checks, and `fls` parsing. | Genuinely used by `investigation.ipynb`; retain it if the unified notebook remains Python/Jupyter based. |
| `runme_disk.sh.deprecated` | Explicitly deprecated shell disk workflow. It performs partition discovery, TSK checks, `/tmp` enumeration, and old recovery-precondition handling. | Obsolete. It should not remain in the minimal final directory. |
| `runme_memory.sh` | Shell-based Volatility phase runner. It writes raw plugin output, findings, summaries, and metrics under `shared/investigations/<RUN_ID>/`. | Old competing execution system. It conflicts with the reusable-notebook design and the requested output location. |
| `runme_timeline.sh` | Shell-based Plaso timeline runner. It writes raw events, findings, summaries, and metrics under `shared/investigations/<RUN_ID>/`. | Old competing execution system. It conflicts with the reusable-notebook design and the requested output location. |
| `.gitignore` | Ignores generated `shared/experiments/*` and `shared/investigations/**` material, among other unrelated rules. | Relevant rules do not match the requested `experiments/<RUN_ID>/` layout. |

## 2. Duplicated content

### Competing methodology

The following substantially overlap in scope:

- `WORKFLOW.md`
- `IMPLEMENTATION_CHECK.md`
- `RECOVERY_NOTES.md`
- `RESULTS_PREVIEW.md`
- methodology text in `README.md`
- methodology prose embedded in `investigation.ipynb`
- methodology prose embedded in `disk_investigation.ipynb`

The duplicated material includes:

- the static disk, timeline, and RAM evidence model;
- recovery scope and distinctions among metadata, content, tool failure, and negative results;
- claim support states such as `S`, `P`, `U`, `N`, and `A`;
- the four result tables;
- source-independence cautions;
- limitations around timestamps, Plaso, recovery, and memory analysis;
- handling of the Father scenario and its staged `rk.so` input.

The final state should have one methodology location under `ai/`. The reusable notebook should link to the authoritative methodology rather than restating it extensively.

### Disk analysis

`investigation.ipynb`, `disk_investigation.ipynb`, and `runme_disk.sh.deprecated` overlap on:

- E01 verification;
- partition and root-filesystem selection;
- `fsstat`;
- `/etc/ld.so.preload` inode, content, and metadata examination;
- `/lib` symlink handling;
- installed-library inode extraction and hashing;
- `/tmp` discovery and listing;
- deleted `/tmp/rk.so` checks;
- `istat`;
- basic static characterisation;
- disk-analysis limitations.

The unified notebook already has the intended location for this work. The disk notebook should not remain as a parallel implementation.

### Phase output and reporting

`runme_memory.sh` and `runme_timeline.sh` share a separate output pattern:

- accept `RUN_ID`;
- consume `shared/experiments/<RUN_ID>`;
- emit raw results, `findings.json`, `metrics.json`, and `investigation-summary.md` under `shared/investigations/<RUN_ID>`;
- call standalone metrics scripts;
- generate independent Markdown summaries.

This is a second output/reporting system alongside the notebook. It violates the requested model of reusable assets plus run-specific experiment directories.

## 3. Unique and useful content

### `investigation.ipynb`

Despite being incomplete, the unified notebook contains useful unique material:

- evidence-acquisition integrity orientation;
- EWF timing interpretation;
- disk and RAM SHA-256 verification;
- evidence-format identification;
- root filesystem discovery;
- guest timezone and operating-system release examination;
- the correct high-level structure for a unified investigation;
- visible-command execution through the helper;
- placeholders for chronology, claims, contribution, footprint, and scenario-validation sections.

It should be the only retained notebook.

### `investigation_utils.py`

Useful and currently used by the unified notebook:

- `run_command`
- `safe_sha256`
- `get_rootfs_offset`
- `parse_istat`

Potentially useful as the notebook expands:

- `parse_ewfverify`
- `parse_fsstat`
- `parse_mmls_root_offset`
- `detect_timestomp`
- `parse_fls_regular_files`
- `write_json`

These are small, direct utilities rather than a framework.

### `disk_investigation.ipynb`

It contains useful source material, but should not remain as a notebook:

- more complete direct `/tmp` examination;
- deleted-entry enumeration;
- journal-name and metadata investigation;
- bounded shell-history and `/var/log` presence inventories;
- clear distinctions among deleted name or metadata, recovered content, recovery-tool failure, and bounded negative results;
- library `file` and `strings` examination;
- candidate-recovery validation concepts.

### `runme_timeline.sh`

The useful implementation detail is its use of the project Plaso wrapper and curated Linux filter:

```text
orchestrator.forensics.plaso_runner.run_log2timeline(...)
default_linux_filter()
```

That behavior may be reproduced from the unified notebook if timeline extraction remains part of the Father investigation. The shell script itself should not be retained.

### `runme_memory.sh`

The useful detail is the selected Volatility plugin set:

- `linux.proc.Maps`
- `linux.pslist`
- `linux.pstree`
- `linux.psaux`
- `linux.sockstat`
- `linux.bash`

These are appropriate candidates for the unified notebook's RAM section. The shell script and its independent JSON/metrics pipeline are not needed.

## 4. Obsolete files

The following are obsolete under the intended final design:

- `investigations/father/disk_investigation.ipynb`
  - It is a second canonical workflow.
  - It conflicts with `README.md`, which identifies `investigation.ipynb` as current.
  - It relies on helper APIs not present in the supplied `investigation_utils.py`, including `resolve_run_paths`, `ensure_output_dirs`, `save_raw`, and `write_report`.
  - It uses a different output model: `shared/investigations/<RUN_ID>/derived/disk`.

- `investigations/father/runme_disk.sh.deprecated`
  - It is explicitly deprecated.
  - Its comments name the competing disk notebook as replacement.
  - It uses old shell, metrics, and summary behavior.

- `investigations/father/runme_memory.sh`
  - It is an old phase runner with a separate findings, metrics, and report system.
  - It writes to the wrong output root for the final design.

- `investigations/father/runme_timeline.sh`
  - It is an old phase runner with a separate findings, metrics, and report system.
  - It writes to the wrong output root for the final design.

- `investigations/father/IMPLEMENTATION_CHECK.md`
  - It is a point-in-time readiness assessment, not reusable investigation material.

The following are obsolete in this directory after methodology is consolidated under `ai/`:

- `investigations/father/WORKFLOW.md`
- `investigations/father/RECOVERY_NOTES.md`
- `investigations/father/RESULTS_PREVIEW.md`

## 5. Files that should be deleted

After useful material has been incorporated into the unified notebook or authoritative methodology, remove these files from `investigations/father/`:

- `investigations/father/disk_investigation.ipynb`
- `investigations/father/runme_disk.sh.deprecated`
- `investigations/father/runme_memory.sh`
- `investigations/father/runme_timeline.sh`
- `investigations/father/IMPLEMENTATION_CHECK.md`

After methodology is moved or consolidated under `ai/`, also remove these from `investigations/father/`:

- `investigations/father/WORKFLOW.md`
- `investigations/father/RECOVERY_NOTES.md`
- `investigations/father/RESULTS_PREVIEW.md`

No repository deletion was performed as part of this audit.

## 6. Files that should be archived

Git history is the appropriate archive. An in-tree `archive/` directory would preserve the competing workflow and violate KISS.

| File | Archive recommendation |
|---|---|
| `disk_investigation.ipynb` | Preserve useful cells in the unified notebook, then retain historical content through Git history only. |
| `runme_disk.sh.deprecated` | Retain through Git history only. |
| `runme_memory.sh` | Preserve the Volatility plugin list and necessary invocation detail, then retain through Git history only. |
| `runme_timeline.sh` | Preserve the Plaso-wrapper approach, then retain through Git history only. |
| `IMPLEMENTATION_CHECK.md` | Retain through Git history only. |
| `WORKFLOW.md` | Consolidate reusable methodology under `ai/`; retain this version through Git history only. |
| `RECOVERY_NOTES.md` | Consolidate recovery methodology under `ai/`; retain this version through Git history only. |
| `RESULTS_PREVIEW.md` | Consolidate the locked four-table specification under `ai/`; retain this version through Git history only. |

## 7. `disk_investigation.ipynb` cells or commands that must be preserved

Preserve the useful behavior by incorporating it into `investigation.ipynb`, not by retaining a second notebook.

### Preserve directly or adapt

1. Deleted `/tmp` entry examination:

   ```text
   fls -o <offset> -r -d -p <image> <tmp_inode>
   ```

   Preserve the distinction between a deleted directory entry and recovered content.

2. `/tmp` enumeration from the resolved `/tmp` inode:

   ```text
   ifind -o <offset> -n /tmp <image>
   fls -o <offset> -r -p <image> <tmp_inode>
   ```

   This is more robust than relying only on a whole-filesystem recursive listing.

3. Per-candidate metadata collection:

   ```text
   istat -o <offset> <image> <inode>
   ```

   Use this for evidence-led candidates, not as automatic interpretation.

4. Installed-library static characterisation:

   ```text
   file -b <extracted-library>
   strings -a -n 8 <extracted-library>
   istat -o <offset> <image> <library-inode>
   ```

   Preserve the limitation that this is descriptive context, not execution proof.

5. Ext4 journal inspection:

   ```text
   jls -o <offset> <image>
   istat -o <offset> <image> <journal-inode>
   icat -o <offset> <image> <journal-inode>
   jcat -o <offset> <image> <journal-inode> <block>
   ```

   Preserve bounded marker searches and the distinction between a journal name/metadata trace and recovered file content.

6. Bounded evidence inventories:

   - `/root/.bash_history` and discovered home-user shell history presence;
   - `/var/log` principal-log presence;
   - persistent journal-directory presence.

   Preserve these as limited presence or metadata checks. Do not present them as timeline parsing or independent corroboration of a Plaso record derived from the same source.

7. Recovery-result representation:

   Preserve distinctions among:

   - content recovered;
   - partial content;
   - metadata or name trace;
   - no result in examined scope;
   - tool failure;
   - not attempted.

   This should use the existing locked table approach rather than a separate disk-only metrics/report system.

### Do not preserve unchanged

1. Helper APIs that do not exist in `investigation_utils.py`:

   ```python
   resolve_run_paths
   ensure_output_dirs
   save_raw
   write_report
   ```

2. The old output convention:

   ```text
   shared/investigations/<RUN_ID>/derived/disk
   ```

3. The `blkls` invocation as implemented.

   The notebook prose says not to write a full multi-gigabyte unallocated stream, but its command helper captures command stdout. Do not copy this contradiction.

4. Assertions requiring manual recovery artifacts from one prior run:

   ```text
   19-extundelete.txt
   20-photorec-stdout.txt
   21-recovery-candidates.json
   22-recovered-rk.so.bin
   ```

   A reusable notebook must not universally require files from one prior run.

5. Hard-coded Father-target assumptions:

   - `/tmp/rk.so`;
   - `EXPECTED_TMP_ARTIFACTS`;
   - scenario-specific journal markers;
   - one particular manifest input layout;
   - a known `rk.so` hash as automatic identity validation.

   These may be valid for a reviewed Father run, but must be represented as selected-run inputs or facts, not universal notebook behavior.

6. A separate `findings.json`, `metrics.json`, and generated-report pipeline.

   The requested design calls for one reusable notebook and per-run output under the experiment directory. A second disk-specific metrics/report system is unnecessary.

## 8. Is `investigation_utils.py` actually needed?

Yes. It is currently needed by `investigation.ipynb`.

The unified notebook imports:

```python
from investigation_utils import get_rootfs_offset, run_command as execute_command, parse_istat
```

Deleting `investigation_utils.py` without modifying the notebook would break the notebook.

It is also appropriate under KISS because it provides small, reusable functions:

- `run_command` centralizes visible command execution and raw stdout/stderr preservation;
- `get_rootfs_offset` avoids duplicating filesystem-discovery logic;
- `parse_istat` supports later disk observations.

The helper module should remain small. The missing helper API used by `disk_investigation.ipynb` should not be added merely to support that obsolete notebook.

## 9. Minimal final directory layout

The final reusable Father directory should be:

```text
investigations/
└── father/
    ├── README.md
    ├── investigation.ipynb
    └── investigation_utils.py
```

If the helper functions are eventually inlined into the notebook, this smaller alternative is possible:

```text
investigations/
└── father/
    ├── README.md
    └── investigation.ipynb
```

Based on the current notebook imports, retaining `investigation_utils.py` is the cleaner minimal option.

Run-specific evidence and generated results should be outside this directory:

```text
experiments/
└── <RUN_ID>/
    ├── manifest.json
    ├── dumps/
    ├── data/
    ├── recovered/
    └── findings/
```

The exact subdirectory names may differ, but all generated tool output, recovered bytes, findings, metrics, and reports must be rooted below the selected `experiments/<RUN_ID>/` directory.

Methodology and table specification should be consolidated under `ai/`, for example:

```text
ai/
└── father-investigation-method.md
```

The exact `ai/` filename is not material to this audit. There must be one authoritative methodology location, including the unchanged four result tables.

## 10. Broken references and cleanup impacts

### Existing broken or inconsistent references

1. `disk_investigation.ipynb` imports helpers that are not present in `investigation_utils.py`:

   ```python
   resolve_run_paths
   ensure_output_dirs
   save_raw
   write_report
   ```

   The disk notebook is not runnable as supplied.

2. `disk_investigation.ipynb` claims canonical status, conflicting with `README.md`:

   - `README.md` calls `investigation.ipynb` the current supervised notebook.
   - `disk_investigation.ipynb` calls itself the single canonical disk workflow.

3. `README.md` references documentation that would be removed from this directory:

   - `RESULTS_PREVIEW.md`
   - `WORKFLOW.md`
   - `IMPLEMENTATION_CHECK.md`
   - `RECOVERY_NOTES.md`

   After cleanup, these links must be removed or redirected to their authoritative `ai/` replacement.

4. `README.md` references `docs/INVESTIGATION_METHOD.md`.

   This reference requires review during cleanup. It conflicts with the direction that methodology belongs in `ai/`, unless it is redirected to the new authoritative methodology location.

5. `runme_disk.sh.deprecated` references deleted or competing material.

   It points users to `disk_investigation.ipynb` and refers to `disk_notebook.md`, which is not among the audited Father files.

6. `runme_memory.sh` and `runme_timeline.sh` depend on legacy output and metrics infrastructure:

   ```text
   shared/experiments/<RUN_ID>
   shared/investigations/<RUN_ID>
   metrics/memory_metrics.py
   metrics/timeline_metrics.py
   ```

   Those dependencies belong to the obsolete independent phase-output system.

7. `runme_timeline.sh` expects disk findings at an old path:

   ```text
   shared/investigations/<RUN_ID>/derived/disk/findings.json
   ```

   The proposed reusable notebook/output model would not produce this path unless deliberately recreated. This is another reason not to retain the script.

8. `investigation.ipynb` does not satisfy the requested run-selection requirement.

   It currently contains:

   ```python
   RUN_ID = "father-u22-20260820-01"
   ```

   It must later expose one top-level configurable `RUN_ID` variable without hard-coding a specific run. It also currently assumes:

   ```python
   REPO_ROOT = Path("../..")
   RUN_DIR = REPO_ROOT / "shared/experiments" / RUN_ID
   ```

   This conflicts with the requested `experiments/<RUN_ID>/` location.

9. `.gitignore` does not cover the requested experiment root.

   The relevant legacy rules are:

   ```gitignore
   shared/experiments/*
   shared/investigations/**
   ```

   If generated outputs move to `experiments/<RUN_ID>/`, generated evidence and findings may no longer be ignored. The appropriate ignore rule must be decided according to the project's intended evidence-tracking policy.

### References that should survive

After cleanup, `README.md` should reference only:

- `investigation.ipynb`;
- `investigation_utils.py`, if retained;
- the authoritative Father methodology in `ai/`;
- the selected run layout under `experiments/<RUN_ID>/`.

The final README should not reference:

- `disk_investigation.ipynb`;
- `runme_disk.sh.deprecated`;
- `runme_memory.sh`;
- `runme_timeline.sh`;
- `WORKFLOW.md`;
- `IMPLEMENTATION_CHECK.md`;
- `RECOVERY_NOTES.md`;
- `RESULTS_PREVIEW.md`.

## Final recommendation

Keep only:

```text
investigations/father/README.md
investigations/father/investigation.ipynb
investigations/father/investigation_utils.py
```

Use `investigation.ipynb` as the only canonical workflow. Select a run with one top-level `RUN_ID` variable and derive all paths under `experiments/<RUN_ID>/`.

Consolidate methodology, recovery guidance, and the unchanged four result tables under `ai/`. Remove obsolete notebooks, scripts, and status documents from the Father directory after preserving the limited useful command-level material identified above.
