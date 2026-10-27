# Marketing Analytics dbt Project (MotherDuck)

dbt models on top of the marketing tables that `utils/motherduck_loader.py` writes to the MotherDuck database `PLACEHOLDER_DATABASE` (set `MOTHERDUCK_DATABASE`; schema `main`). Models are built in schema `analytics` of the same database.

## Prerequisites

- The six raw tables already loaded (root README, `--load-to-motherduck`).
- `MOTHERDUCK_TOKEN` exported in your shell. `profiles.yml` holds no secrets.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r synthetic_marketing/dbt/requirements.txt
```

`requirements.txt` pins `duckdb` to the newest version MotherDuck documents as supported (1.5.6); the adapter's `md` extra pins an older one.

## Run

```bash
cd synthetic_marketing/dbt
dbt debug --profiles-dir .   # checks the connection
dbt run   --profiles-dir .
dbt test  --profiles-dir .
```

## Models

| Layer | Models | Materialized as |
|-------|--------|-----------------|
| staging | `stg_sessions`, `stg_campaigns_daily`, `stg_conversions`, `stg_attribution_touchpoints` | view |
| intermediate | `int_*` (user touchpoints, conversions, campaign metrics, channel attribution) | view |
| marts | `campaign_performance`, `channel_attribution`, `daily_summary`, `user_journey` | view |
| marts | `int_ads`, `int_conversions`, `int_sessions` | table |

Tests (`not_null`, `unique`) are declared in the `_*.yml` files next to the models.

## Notes

- The raw `date`, `timestamp` and `session_start` columns are strings (that is how dlt writes them); staging casts them.
- `target/` and `logs/` are gitignored.
