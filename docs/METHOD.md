# Examination method

Design record, 13 November 2026. It replaces the earlier notebook-based method and the four-table contract.

## What is measured

For every declared claim of a scenario run: does each evidence source hold a recoverable trace of the claimed
effect? The analyst knows the scenario, so this is recoverability given a known action, not blind discovery.

- **Ground truth**: the claims in `manifest.json`, backed by `command_log.jsonl`. Ground truth is used to decide
  what to look for and to score, never as forensic support.
- **Sources**: `disk` (file content, metadata, logs, timelines) and `ram`. A timeline is a view of the disk, not
  a source. `combined` is the better of the two unless the analyst records that two partial findings are
  jointly sufficient.
- **Status**: `S` supported, `P` partial, `U` examined and unsupported, `NE` not examined, `TF` tool failure.
- **Criteria first**: each scenario README states, per claim and per source, what counts as supported. It is
  written before the evidence is opened and changes only with a dated note.
- **Cleanup claims** are supported only by a positive trace. Absence of a file or a history is not support.
  Totals are reported with and without cleanup-class claims.
- **Origin rule**: two renderings of the same record (for example `istat` and a timeline row) are one observation.

## Control runs

One benign run per distribution (`interactive_shell`). Three uses: every scenario claim check must be negative
on it; the sweep's output on it is the noise level; it documents which artifacts the distribution has at all.

## Procedure per run

```bash
RUN=shared/experiments/<run_id>
examination/00_open.sh $RUN          # verify hashes, find root filesystem, write run.env, create scores.tsv
examination/10_disk.sh $RUN          # fixed disk sweep
examination/20_memory.sh $RUN        # fixed memory sweep
examination/claims/<scenario>.sh $RUN   # targeted checks, one or two per claim and source
examination/pivot.sh $RUN P01_name '<command>'   # any exploratory command, recorded
python3 examination/metrics.py shared/experiments  # checks, then tables
```

Every step writes native output to `investigation/outputs/<ID>.txt`, errors to `<ID>.err`, and one row to
`outputs/_steps.tsv` (run, step, exit status, lines, time, command). A step that finds nothing ends non-zero;
that is a result, and across distributions it is the portability table. Step prefixes: `D`, `FS`, `T`, `M`
are the fixed sweep; `C_` are scenario checks (exit 0 means the predicate matched); `P` are pivots.

The analyst then reads the outputs, fills `scores.tsv` (status, cited step IDs, note) and writes `notes.md`
under five headings: deviations, what the sweep showed, pivots, unexpected, interpretation and limits.

`metrics.py` refuses to print numbers when a score cites a step the run never produced, a cited step was rerun
after scoring, a row carries another run's ID, or a claim has no score.

## What is kept in git per run

`manifest.json`, `command_log.jsonl`, `investigation/run.env`, `investigation/scores.tsv`,
`investigation/notes.md`, `investigation/outputs/_steps.tsv`. Evidence and bulk outputs stay local.

## Limits

- Sleuth Kit reads Ext2/3/4 but not XFS or Btrfs. A distribution with such a root filesystem needs another way
  to read the disk; `00_open.sh` stops with a message.
- RAM is captured before a graceful shutdown and disk after it. Shutdown changes the disk (logs flush, the
  journal commits, a tmpfs `/tmp` is discarded). This is a design choice and shapes the disk results.
- The stale check compares file times. Run `metrics.py` before committing, not after a fresh clone.
- With about 75 claim instances the results are counts and proportions. No significance tests.
