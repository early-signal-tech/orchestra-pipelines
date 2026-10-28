# synthetic_marketing

Synthetic marketing data, end to end in Orchestra, one layer per stage:

| Stage | Tool | What it does |
|---|---|---|
| generate | Python (`PYTHON_EXECUTE_SCRIPT`) | dlt writes one day of Parquet to S3 |
| validate | MotherDuck SQL | reads the day's Parquet from S3, fails the run on any broken check |
| prepare | MotherDuck SQL | creates the six tables if missing |
| load | MotherDuck SQL, one task per table | deletes the day's rows and inserts the latest batch, so a same-day rerun replaces the day |
| dbt | `DBT_CORE_EXECUTE` | `dbt build` without the `data_quality` tests, then those tests in their own task |

The pipeline definition is `pipelines/synthetic_marketing.yaml`. `pipelines/synthetic_marketing_autoheal.yaml` triages its FAILED and WARNING runs with an agent: a code failure gets a fix PR against the failing branch (a human merges it), a data quality warning goes to Slack for a human.

## Data defects

The generator adds production-like problems so the pipeline has something to report:

- **Always on, small share of rows** (rates in `python/config.yaml` under `defects`): unmapped channel, unknown device, overspend, clicks above impressions, bad conversion values, late conversions. Validate lets them through; the dbt tests tagged `data_quality` catch them. That task has `treat_failure_as_warning: true`, so the run ends as WARNING (amber), not FAILED. A dbt `severity: warn` would not work here: dbt exits 0 and Orchestra reports success.
- **On demand, pipeline input `fail_mode`**: `duplicate_conversions` (a retried delivery) or `missing_sessions` (a file that never arrived). Validate fails the run (red) and nothing is loaded.

- [`python/`](python/): generator (`src/`), `config.yaml`, `pyproject.toml`.
- [`dbt/`](dbt/): dbt project on MotherDuck, see its README.

## Orchestra setup

- Bucket `synthetic-marketing-data` and region `eu-west-3` are written in `pipelines/synthetic_marketing.yaml`. The database name lives in the MotherDuck connection and in the `DBT_CORE` connection's `profiles.yml`, not in the repo (the code placeholder is `PLACEHOLDER_DATABASE`).
- The Python connection must clone this repo and link the S3 connection, so the generate task receives the S3 keys as `AWS_S3__<connection>__<field>` variables (Orchestra rejects `AWS_*` names in task env vars). the generator reads `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_REGION` from them (confirmed names), and prints the variable names it finds, never the values.
- The SQL tasks name the MotherDuck connection with `connection:`.

## Secrets

The MotherDuck token and the S3 keys live in Orchestra connections. No secret is stored in the repo.

The SQL tasks read S3 from MotherDuck, which needs a persistent S3 secret. Create it once, outside the pipeline, with your own keys:

```sql
CREATE SECRET IF NOT EXISTS marketing_s3 IN MOTHERDUCK (
    TYPE S3, KEY_ID '<key id>', SECRET '<secret>', REGION '<region>'
);
```

## Notes

- The load tasks have no explicit transaction (the API rejects a `DELETE` after `BEGIN;`, see `CLAUDE.md`). If an insert fails after its delete, that table is empty for the day until the next run.
