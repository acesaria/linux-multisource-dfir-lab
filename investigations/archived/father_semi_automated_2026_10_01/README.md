# Archived: semi-automated Father investigation (2026-10-01)

Kept for reference after ac chose a simpler, manual investigation style on 2026-10-01. It is not
the active notebook.

## What it was

`investigation.ipynb` executes Sections 0–6 against `father-u22-20260913-01`. Each examining block
ended with a claim check. The check evaluated the claim's elements (`claims.py`) on that run's
values and proposed a status by a strict rule: all elements observed gives supported, some gives
partial, none gives unsupported. Section 6 validated the 21 proposals, read ac's accepted statuses
from the run's `findings/findings.py`, and rendered the four tables and counts.

Fresh-kernel replay: 136 cells, 168 s, no errors.

## What it produced (proposals, never accepted)

| Claim | Disk | Timeline | RAM |
|---|---|---|---|
| preload_persistence | S | P | S |
| implant_timestomp | S | P | P |
| credential_staging | S | S | S |
| runtime_loading_backdoor | P | P | S |
| deleted_staging_artifact | S | P | P |
| recon_staged | S | P | S |
| shell_history_cleanup | U | U | S |

Support rate: Disk 5/7, Timeline 1/7, RAM 5/7. Corroborated 3; supported by exactly one source 4.

Two caveats travel with these numbers:
- The RAM S for `shell_history_cleanup` rests on command text in unattributed memory. Part of
  that text is the lab harness's own command list and terminal echo carrying the
  `__FORENSIC_LAB_` prompt.
- "During cleanup" in `deleted_staging_artifact` was read as "after the file's last read, before
  memory capture", comparing a guest-clock time with a host-recorded one.

## Why it was archived

The claim checks are specific to each scenario and sensitive to each distro. With four scenarios
and three distros left in one month, writing and porting them would cost more than judging the
findings by hand against a written element checklist. The investigation techniques this notebook
added are kept for the simplified notebook: page cache, exited-task carving, memory string search,
and journal decoding of the implant and earlier preload inodes.

## Running it again

It needs `fx.propose`, `fx.finding`, `fx.check_findings`, `fx.support_rates` and
`fx.contribution` in `investigations/common/forensics.py`. It also needs the `pagecache.Files`
and `psscan` products in `prepare.py`'s RAM stage. If those are later removed, recover them from
the commit that contains this folder.
