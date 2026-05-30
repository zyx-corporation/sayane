# PyPI publish checklist (#82)

Community Edition package name: **`sayane`** (Apache-2.0).

## Prerequisites

Choose **one** auth method:

### A. PyPI Trusted Publishing (recommended)

1. Create project `sayane` on PyPI (first upload can also register via token).
2. PyPI → **sayane** → Publishing → Add GitHub publisher:
   - Owner: `zyx-corporation`
   - Repository: `sayane`
   - Workflow: `publish-pypi.yml`
   - Environment: `pypi` (optional but matches workflow)
3. GitHub → repo → **Settings → Environments → pypi** (create if missing).
4. Re-run workflow — **no `PYPI_API_TOKEN` secret required** when Trusted Publishing is active.

### B. API token (legacy)

1. pypi.org → Account → API tokens → scope **entire project `sayane`** (or first upload).
2. GitHub → **Settings → Environments → pypi → Environment secrets** → `PYPI_API_TOKEN`

> **Common CI failure:** secret added under **Repository secrets** only while workflow uses `environment: pypi`.  
> Add `PYPI_API_TOKEN` to the **`pypi` environment**, not only repo-level secrets.

3. Tag **`v1.0.3`** on `main`.

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

1. Configure **Trusted Publishing** (see above) **or** add `PYPI_API_TOKEN` to the **`pypi` environment**.
2. Create GitHub Release **`v1.0.3`** (published) — triggers this workflow.

Or re-run after fixing credentials:

```bash
gh workflow run publish-pypi.yml --repo zyx-corporation/sayane -f tag=v1.0.3
```

### Troubleshooting `Upload to PyPI` exit code 1

| Symptom | Fix |
|---------|-----|
| `Invalid or non-existent authentication` | Add `PYPI_API_TOKEN` to **Environment `pypi`**, or enable Trusted Publishing |
| Secret in repo secrets only | Move/copy to **Environments → pypi → Secrets** |
| Project name taken | Rename package in `pyproject.toml` or claim name on PyPI |
| Node.js 20 warning | Informational only; unrelated to upload failure |

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
