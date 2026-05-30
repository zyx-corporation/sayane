# PyPI publish checklist (#82)

Community Edition package name: **`sayane`** (Apache-2.0).

## Prerequisites

1. PyPI account at https://pypi.org (first upload registers project `sayane`).
2. GitHub repository secret **`PYPI_API_TOKEN`**  
   pypi.org → Account → API tokens → scope: entire project `sayane` (or first upload: no project yet).
3. GitHub **environment** `pypi` (optional; workflow references it).
4. Tag **`v1.0.3`** on `main`.

## Local build verify

```bash
cd /path/to/sayane
bash scripts/build-wheel.sh
pip install dist/sayane-1.0.3*.whl
sayane --version   # expect 1.0.3
```

TestPyPI (optional):

```bash
twine upload --repository testpypi dist/sayane-1.0.3*
pip install -i https://test.pypi.org/simple/ sayane==1.0.3
```

## CI publish (recommended)

1. Add `PYPI_API_TOKEN` to GitHub → Settings → Secrets → Actions.
2. Create GitHub Release **`v1.0.3`** (publish) — triggers `.github/workflows/publish-pypi.yml`.

Or manual workflow:

```bash
gh workflow run publish-pypi.yml -f tag=v1.0.3
```

## Manual upload (maintainers)

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-...   # API token
twine upload dist/sayane-1.0.3*
```

## Post-publish

1. Confirm: `pip install sayane==1.0.3` && `sayane --version`
2. Close Issue #82.
3. Update release notes if needed.

## Notes

- Package ships **CLI + Bridge + MCP** only; Chrome Extension remains separate (load unpacked).
- `sayane-pro` is **not** published to PyPI.
