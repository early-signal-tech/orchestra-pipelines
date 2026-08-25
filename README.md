# orchestra-pipelines

Early Signal's Orchestra pipeline definitions and the Python they run.

## Dummy Dry Run Pipeline

Smoke-test pipeline for Orchestra wiring — four no-op Python tasks plus an
`ORCHESTRA WAIT`. Contacts no external system and writes no data.

- Definition: [`pipelines/dummy_dry_run.yaml`](pipelines/dummy_dry_run.yaml)
- Alias: `dummy_dry_run` · storage: Orchestra-backed
- Stage order: `stage_extract` → `stage_transform` → `stage_settle` → `stage_publish`
- Environment variables read: `DUMMY_ROW_LIMIT`, `DUMMY_TARGET_TABLE`

### Pipeline inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `run_label` | `dry-run` | Free-text label echoed in every task's logs |
| `python_branch` | `main` | Branch of **this** repo the Python tasks run from |

### Tasks

| Stage | Task | Name | Script | Command |
| --- | --- | --- | --- | --- |
| `stage_extract` | `dummy_extract_customers` | Dummy extract - customers | [`python/dummy_dry_run/dummy_extract_customers.py`](python/dummy_dry_run/dummy_extract_customers.py) | `python dummy_extract_customers.py` |
| `stage_extract` | `dummy_extract_orders` | Dummy extract - orders | [`python/dummy_dry_run/dummy_extract_orders.py`](python/dummy_dry_run/dummy_extract_orders.py) | `python dummy_extract_orders.py` |
| `stage_transform` | `dummy_transform` | Dummy transform | [`python/dummy_dry_run/dummy_transform.py`](python/dummy_dry_run/dummy_transform.py) | `python dummy_transform.py` |
| `stage_publish` | `dummy_publish` | Dummy publish | [`python/dummy_dry_run/dummy_publish.py`](python/dummy_dry_run/dummy_publish.py) | `python dummy_publish.py` |

`stage_settle` holds one non-Python task, `dummy_wait` (`ORCHESTRA` / `WAIT`, 1 minute).

The Python tasks use `source: GIT`. Orchestra shallow-clones `python/dummy_dry_run` from this
repo on the `python_branch` branch, cds into it, and runs the command above. The scripts
import only the standard library, so no `build_command` is set — adding a dependency means
adding a `requirements.txt` and a `build_command` to the task.

## Triggering from GitHub Actions

[`ci/run-dummy-dry-run-pipeline.yml`](ci/run-dummy-dry-run-pipeline.yml) runs the pipeline
and waits for it to finish, failing the job if the pipeline fails.

> **This file is not active yet.** Move it to `.github/workflows/` to enable it:
>
> ```bash
> mkdir -p .github/workflows
> git mv ci/run-dummy-dry-run-pipeline.yml .github/workflows/
> ```
>
> It was committed to `ci/` because the Orchestra GitHub App token that authored this
> branch lacks the `workflows` permission, which GitHub requires to write files under
> `.github/workflows/`.

| Event | `python_branch` | `run_label` |
| --- | --- | --- |
| `pull_request` into `main` | the PR branch | `pr-<number>` |
| `push` to `main` | `main` | `main-<short-sha>` |
| `workflow_dispatch` | your input (default `main`) | your input |

PR and push runs are path-filtered to this pipeline's files. Because a PR run sets
`python_branch` to the PR branch, CI exercises the Python under review rather than `main`.

### Setup

1. Add repository secret **`ORCHESTRA_API_KEY`** — an Orchestra *standard* API key
   (Orchestra → Settings → Workspace). A read-only key cannot start runs.
2. The workflow targets the `Staging` environment, the only one configured. Add more
   `options:` under the `environment` input once other environments exist.
