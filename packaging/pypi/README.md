# PyPI publish checklist (#82)

Community Edition package name: **`sayane`** (Apache-2.0).

## Prerequisites

1. PyPI account + project `sayane` created (or first upload registers it).
2. Trusted Publisher (recommended) or API token stored as GitHub secret `PYPI_API_TOKEN`.
3. Tag `v1.0.2` on `main` (done).

## Local build verify

```bash
cd /path/to/sayane
python3 -m pip install build twine
python3 -m build
twine check dist/sayane-1.0.2*
pip install dist/sayane-1.0.2*.whl
sayane --version   # expect 1.0.2
```

## Manual upload (maintainers)

```bash
twine upload dist/sayane-1.0.2*
```

Use TestPyPI first when validating:

```bash
twine upload --repository testpypi dist/sayane-1.0.2*
pip install -i https://test.pypi.org/simple/ sayane==1.0.2
```

## CI publish

Workflow `.github/workflows/publish-pypi.yml` runs on GitHub Release **published** (or manual `workflow_dispatch`).

Required secret: `PYPI_API_TOKEN` (pypi.org → Account → API tokens → scope: entire project `sayane`).

## Post-publish

1. Update `docs/install.md` — mark PyPI as available, add `pip install sayane==1.0.2`.
2. Update `README.md` / `README_ja.md` install one-liner.
3. Close Issue #82.

## Notes

- Package ships **CLI + Bridge + MCP** only; Chrome Extension remains separate (load unpacked / future store).
- `sayane-pro` is **not** published to PyPI.
