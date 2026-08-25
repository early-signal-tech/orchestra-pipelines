# orchestra-pipelines

Backups of Early Signal's Orchestra pipeline definitions and the Python they run.

## Dummy Dry Run Pipeline

Smoke-test pipeline for Orchestra wiring — four stages of no-op Python plus an
`ORCHESTRA WAIT`. Contacts no external system and writes no data. No schedule;
trigger manually.

- Definition: [`pipelines/dummy_dry_run.yaml`](pipelines/dummy_dry_run.yaml)
- Alias: `dummy_dry_run` · storage: Orchestra-backed, published version 1
- Pipeline input: `run_label` (string, default `dry-run`)
- Environment variables read: `DUMMY_ROW_LIMIT`, `DUMMY_TARGET_TABLE`

### Stage order

`stage_extract` → `stage_transform` → `stage_settle` → `stage_publish`

### Task scripts

| Stage | Task | Name | Script |
| --- | --- | --- | --- |
| `stage_extract` | `dummy_extract_customers` | Dummy extract - customers | [`python/dummy_dry_run/dummy_extract_customers.py`](python/dummy_dry_run/dummy_extract_customers.py) |
| `stage_extract` | `dummy_extract_orders` | Dummy extract - orders | [`python/dummy_dry_run/dummy_extract_orders.py`](python/dummy_dry_run/dummy_extract_orders.py) |
| `stage_transform` | `dummy_transform` | Dummy transform | [`python/dummy_dry_run/dummy_transform.py`](python/dummy_dry_run/dummy_transform.py) |
| `stage_publish` | `dummy_publish` | Dummy publish | [`python/dummy_dry_run/dummy_publish.py`](python/dummy_dry_run/dummy_publish.py) |

`stage_settle` holds one non-Python task, `dummy_wait` (`ORCHESTRA` / `WAIT`, 1 minute).

## Note on drift

The pipeline stores this Python inline (`source: INLINE`), so these files are copies.
Changing a script here does not change what Orchestra runs. To make this repo the source
of truth, migrate the pipeline to git-backed storage and switch each task to `source: GIT`.
