# Father investigation

`investigation.ipynb` is the reusable post-mortem investigation notebook for
Father scenario runs.

Set `RUN_ID` near the top of the notebook. It is the notebook's only
run-specific literal. The notebook imports all forensic helpers from
`investigations.common.forensics` and can run from the repository root or this
directory.

Sections 0 and 1 examine evidence identity, acquisition limits, the prepared
disk layout and bodyfile, persistence locations, preload configuration, the
referenced object, and timestamp relationships. Sections 2–7 remain staged
placeholders and must not be executed until they are implemented.

Run the disk and RAM preparation stages before opening the notebook. Prepared
products are read from:

```text
shared/experiments/<RUN_ID>/investigation/prepared/
```

Visible targeted commands preserve full stdout and stderr under the run's
`investigation/output/` or `investigation/data/` directories. Draft finding
records are written to:

```text
shared/experiments/<RUN_ID>/investigation/findings/findings.json
```

At acceptance time, preserve an executed HTML snapshot with one command:

```bash
jupyter nbconvert --to html investigations/father/investigation.ipynb \
  --output-dir shared/experiments/$RUN_ID/investigation --output executed
```

The project methodology, claim model, evidence rules, recovery scope, and result
definitions are maintained in `ai/`. This directory contains the reusable
investigation assets, not run-specific evidence.
