# orchestra-pipelines

Gotchas found by running things (CLI 0.5.1, Oct 2026):

- `orchestra pipeline validate` reads `.oml` as plain YAML. OML blocks (`%sql ... %%`, `.` terminators) fail; check those locally with `oml/validate_oml.py` (`orchestra-lang`).
- `pipeline update` fails with 422 `extra_forbidden` on `storage_provider`: CLI and API disagree.
- Pipeline aliases allow only letters, numbers, underscores. Hyphens give 422.
- A new pipeline keeps its `schedule:` even when unpublished. Test files carry no schedule.
- Only create, change or delete our own `zz_` pipelines. Never touch the existing ones in the account (`triage_test`, `dummy_dry_run`, Triage Example and the rest).
- A hook blocks reading the env file, so commands that use `ORCHESTRA_API_KEY` are run by the user.
- `tracker/` and the planning notes are local only (gitignored). This repo is public.
