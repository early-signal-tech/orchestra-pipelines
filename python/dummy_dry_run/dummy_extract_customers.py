"""Dummy extract - customers

Backup of the inline PYTHON_EXECUTE_SCRIPT body for task `dummy_extract_customers`
in stage `stage_extract` of the "Dummy Dry Run Pipeline" Orchestra pipeline.

Environment variables supplied by Orchestra:
  RUN_LABEL = ${{ inputs.run_label }}
  ROW_LIMIT = ${{ ENV.DUMMY_ROW_LIMIT }}
  DATASET = customers

This file is a backup: the pipeline still carries the code inline
(source: INLINE). Edit both, or migrate the task to source: GIT.
"""

import os
label = os.environ.get("RUN_LABEL", "unset")
limit = os.environ.get("ROW_LIMIT", "0")
dataset = os.environ.get("DATASET", "unknown")
print(f"[{label}] dummy extract of {dataset}: pretending to pull {limit} rows")
print(f"[{label}] no external system was contacted")
