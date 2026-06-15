# CLI App Split Rewiring Plan: 2026-06-15

## Context

This plan supports #172 and ADR 0004.

The current staged extraction has introduced command registration modules under:

```text
src/sayane/cli/commands/
```

The active CLI behavior has not yet changed because `src/sayane/cli/app.py` still owns the legacy command registration functions.

## Current Staged Modules

```text
src/sayane/cli/commands/all.py
src/sayane/cli/commands/profile.py
src/sayane/cli/commands/core.py
src/sayane/cli/commands/capture.py
src/sayane/cli/commands/export.py
src/sayane/cli/commands/import_bundle.py
src/sayane/cli/commands/review.py
src/sayane/cli/commands/package.py
src/sayane/cli/commands/candidate.py
src/sayane/cli/commands/storage.py
src/sayane/cli/commands/mcp.py
```

## Rewiring Target

`src/sayane/cli/app.py` should become the assembly point.

Target `build_app()` shape:

```python
from sayane.cli.commands.all import register_builtin_commands

...

register_builtin_commands(app, _load, INIT_TEMPLATE)
register_help(app)
from sayane.cli.plugins import register_cli_extensions
register_cli_extensions(app)
return app
```

If help ordering must remain exactly where it is, the registrar can be split so `register_help(app)` stays between core and candidate registration. Preserve behavior over aesthetics.

## Deletion Pass

After rewiring, remove duplicated legacy definitions from `app.py`:

```text
_register_profile
_status_line
_load_judge_settings
_register_core_commands
_register_candidate
_register_storage
_register_mcp
```

Only remove helpers that are no longer referenced.

Keep:

```text
INIT_TEMPLATE
_version_callback
build_app
_load
```

## Required Checks

Run at least:

```bash
python -m compileall src/sayane/cli
pytest
```

If the full test suite is expensive, run CLI-focused and export-focused tests first, then the full suite:

```bash
pytest tests -q
```

## Non-Goals

Do not change:

- CLI command names
- CLI option names
- CLI output text
- Typer app help text intentionally
- export output
- golden fixtures
- candidate lifecycle behavior
- review decision semantics
- Git auto-commit behavior
- bridge serve localhost restriction

## RDE Notes

Expected meaning delta:

```text
ΔM = responsibility boundary relocation only
```

Unexpected meaning drift includes:

- changed command name or command nesting
- changed default option value
- changed output line text
- changed exit status
- changed import/export golden output
- changed approval, rejection, or audit behavior

If any of these occur, stop and treat them as implementation drift rather than refactor noise.
