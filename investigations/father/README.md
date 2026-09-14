# Father investigation

`investigation.ipynb` is the reusable post-mortem investigation notebook for
Father scenario runs.

Set the run identifier near the top of the notebook:

```python
RUN_ID = "father-u22-20260913-01"
```

The notebook reads immutable execution and acquisition artifacts from:

```text
experiments/<RUN_ID>/
```

It writes investigation workspace data and derived results under:

```text
experiments/<RUN_ID>/investigation/
```

`investigation_utils.py` contains small helpers used by the notebook.

The project methodology, claim model, evidence rules, recovery scope, and result
definitions are maintained in `ai/`. This directory contains the reusable
investigation assets, not run-specific evidence.