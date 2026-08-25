"""Dummy publish

Backup of the inline PYTHON_EXECUTE_SCRIPT body for task `dummy_publish`
in stage `stage_publish` of the "Dummy Dry Run Pipeline" Orchestra pipeline.

Environment variables supplied by Orchestra:
  RUN_LABEL = ${{ inputs.run_label }}
  TARGET_TABLE = ${{ ENV.DUMMY_TARGET_TABLE }}

This file is a backup: the pipeline still carries the code inline
(source: INLINE). Edit both, or migrate the task to source: GIT.
"""

import os
label = os.environ.get("RUN_LABEL", "unset")
target = os.environ.get("TARGET_TABLE", "unset")
print(f"[{label}] dummy publish complete for {target}")
print(f"[{label}] end-to-end dry run finished with no side effects")
