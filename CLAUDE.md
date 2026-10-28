# orchestra-pipelines

Gotchas found by running things (CLI 0.5.1, Oct 2026):

- `orchestra pipeline validate` reads `.oml` as plain YAML. OML blocks (`%sql ... %%`, `.` terminators) fail; check those locally with `oml/validate_oml.py` (`orchestra-lang`).
- `pipeline update` fails with 422 `extra_forbidden` on `storage_provider`: CLI and API disagree.
- Pipeline aliases allow only letters, numbers, underscores. Hyphens give 422.
- Creating or updating a pipeline returns an nginx 403 HTML page when any query contains `union all` followed by `select`, even in a SQL comment (a web filter; `validate` is not affected). Build one row and `UNPIVOT` it instead, as in `pipelines/synthetic_marketing.yaml` validate. The same filter blocks a `DELETE` that follows another statement (`BEGIN;` then `DELETE`), so the load tasks run `DELETE` first with no explicit transaction.
- A new pipeline keeps its `schedule:` even when unpublished. Test files carry no schedule.
- A hook blocks reading the env file, so commands that use `ORCHESTRA_API_KEY` are run by the user.
- `tracker/` and the planning notes are local only (gitignored). This repo is public.
