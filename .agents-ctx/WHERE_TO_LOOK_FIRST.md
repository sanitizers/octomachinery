# Where to Look First

When picking up a task, get oriented before proposing anything.
Read, in this order:

1. The packaging metadata -- what the project is, what it depends
   on, what it exposes.
2. The source of the module the task is about.
3. The shared test fixtures, then the tests for that module --
   they are the behavioral contract.
4. `tox.ini` and `.pre-commit-config.yaml` -- how things get run
   locally and in CI.
5. The main CI/CD workflow.

Here:

1. `setup.cfg` (the metadata) and `pyproject.toml` (the build
   backend and `setuptools-scm`).
2. `octomachinery/<area>/` -- `app/` for the app runtime, routing
   and server, `github/` for the GitHub API, models and
   entities, `utils/` for helpers.
3. `tests/conftest.py`, then `tests/<area>/.../<module>_test.py`.
4. As above.
5. `.github/workflows/ci-cd.yml`, which delegates to
   `tox-dev/workflow`'s `reusable-tox.yml`.

Other places worth knowing:

- `docs/` -- Sphinx docs (RST), published at
  <https://octomachinery.dev>.
