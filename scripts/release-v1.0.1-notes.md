## Highlights

- Patch release after Community **v1.0.0**, with documented L1/L2 acceptance sign-off (Pass, 2026-05-29).
- Japanese README expanded for beginners; Markdown-first storage wording (Obsidian import optional).
- Context layering / profile layout validation and dogfood doc updates.
- Pre-release Omomuki migration notes removed from user-facing docs.

## Added

- Context layering heuristics, profile layout validation, and dogfood documentation updates.
- Expanded Japanese README for beginner onboarding; restored full README_ja sections after edit truncation.

## Changed

- README_ja: Markdown-first storage wording (Obsidian import is optional, not required).
- CONTRIBUTING split into English (`CONTRIBUTING.md`) and Japanese (`CONTRIBUTING_ja.md`); templates reference `README_ja.md`.
- Removed pre-release Omomuki migration notes from user-facing docs (post-1.0 cleanup).
- Recorded Community v1.0.0 release acceptance sign-off in `docs/acceptance-spec.md` (L1/L2 Pass, 2026-05-29).

## Verification

- `ruff check src tests`: pass
- `pytest -q` (clean venv, sayane-pro not installed): **164 passed**

## Install

```bash
SAYANE_REF=v1.0.1 curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

Full changelog: https://github.com/zyx-corporation/sayane/blob/v1.0.1/CHANGELOG.md
