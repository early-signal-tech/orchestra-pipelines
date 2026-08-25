"""Dummy transform

Run by the "Dummy Dry Run Pipeline" Orchestra pipeline as task `dummy_transform`
in stage `stage_transform`, via:

    project_dir: python/dummy_dry_run
    command:     python dummy_transform.py

Environment variables injected by Orchestra at runtime:
  RUN_LABEL = ${{ inputs.run_label }}
  TARGET_TABLE = ${{ ENV.DUMMY_TARGET_TABLE }}

No third-party imports: the task declares no build_command, so anything
beyond the standard library needs a requirements.txt and a build_command
added to the task first.
"""

import os
label = os.environ.get("RUN_LABEL", "unset")
target = os.environ.get("TARGET_TABLE", "unset")
print(f"[{label}] dummy transform -> would model into {target}")
print(f"[{label}] transform is a no-op: no warehouse credentials are used")
