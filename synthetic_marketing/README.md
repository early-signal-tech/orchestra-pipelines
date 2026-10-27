# synthetic_marketing

Synthetic marketing data, end to end in Orchestra, one layer per stage:

| Stage | Tool | What it does |
|---|---|---|
| generate | Python (`PYTHON_EXECUTE_SCRIPT`) | dlt writes one day of Parquet to S3 |
| validate | MotherDuck SQL | reads the day's Parquet from S3, fails the run on any broken check |
| prepare | MotherDuck SQL | creates the six tables if missing |
| load | MotherDuck SQL, one task per table | inserts the day's rows, skipping primary keys already loaded |
| dbt | `DBT_CORE_EXECUTE` | builds the models |

Status: **pending**. The code is a copy of a private source repo (`main` at `64407a2`). The pipeline draft is `pipelines/synthetic_marketing.yaml`; nothing here has run in Orchestra. The SQL was checked locally with DuckDB 1.5.6 on one generated day (second load adds 0 rows; a broken attribution makes validate fail), not on MotherDuck.

- [`python/`](python/): generator (`src/`), `config.yaml`, `pyproject.toml`.
- [`dbt/`](dbt/): dbt project on MotherDuck, see its README.

## Orchestra setup

- Bucket `synthetic-marketing-data` and region `eu-west-3` are written in `pipelines/synthetic_marketing.yaml`. The database name lives in the MotherDuck connection and in the `DBT_CORE` connection's `profiles.yml`, not in the repo (the code placeholder is `PLACEHOLDER_DATABASE`).
- The Python connection must clone this repo and link the S3 connection, so the generate task receives the S3 keys as `AWS_S3__<connection>__<field>` variables (Orchestra rejects `AWS_*` names in task env vars). Field names are unconfirmed: the generator prints the variable names it finds, never the values.
- The SQL tasks name the MotherDuck connection with `connection:`.

## Secrets

The MotherDuck token and the S3 keys live in Orchestra connections. No secret is stored in the repo.

The SQL tasks read S3 from MotherDuck, which needs a persistent S3 secret. Create it once, outside the pipeline, with your own keys:

```sql
CREATE SECRET IF NOT EXISTS marketing_s3 IN MOTHERDUCK (
    TYPE S3, KEY_ID '<key id>', SECRET '<secret>', REGION '<region>'
);
```

## Unverified in Orchestra

- Whether `query` accepts several statements (the prepare task sends six `CREATE TABLE IF NOT EXISTS`).
- What `set_outputs` returns for SQL (the validate task sets it).
- Which timezone `current_date` uses on MotherDuck (the generator uses the container date, UTC).
