"""Dummy extract - orders

Run by the "Dummy Dry Run Pipeline" Orchestra pipeline as task `dummy_extract_orders`
in stage `stage_extract`, via:

    project_dir: python/dummy_dry_run
    command:     python dummy_extract_orders.py

Environment variables injected by Orchestra at runtime:
  RUN_LABEL = ${{ inputs.run_label }}
  ROW_LIMIT = ${{ ENV.DUMMY_ROW_LIMIT }}
  DATASET = orders

No third-party imports: the task declares no build_command, so anything
beyond the standard library needs a requirements.txt and a build_command
added to the task first.
"""

import os
label = os.environ.get("RUN_LABEL", "unset")
limit = os.environ.get("ROW_LIMIT", "0")
dataset = os.environ.get("DATASET", "unknown")
print(f"[{label}] dummy extract of {dataset}: pretending to pull {limit} rows")
rows = [{"id": i, "dataset": dataset} for i in range(int(limit))]
print(f"[{label}] built {len(rows)} in-memory rows; nothing was written anywhere")
