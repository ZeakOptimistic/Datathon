# Submission Notes

## Current Best Public Candidate

Use:

```text
outputs/submission_best.csv
```

Known public score:

```text
912428.76513
```

Backup:

```text
outputs/submission_public_912428.csv
```

## Reproducibility Check

Run:

```bash
uv run --with pandas --with numpy python scripts/forecast_improved.py
sha256sum outputs/submission_public_912428.csv outputs/submission_best.csv outputs/submission_improved.csv
```

All three hashes should match:

```text
f0b353494bac15c90e485bb6ad5f7ddb7236fbe86d0b1361571ba9c3346ff8dd
```

## Model Summary

The current generator:

- predicts `Revenue` with normalized month/day seasonality plus weekday adjustment
- uses a recent YoY shrinkage level method for annual scale
- predicts `COGS` as `Revenue * seasonal COGS/Revenue ratio`

Do not overwrite `outputs/submission_best.csv` with the lower-level scaled/blended candidate that scored `1219493.70666`.

