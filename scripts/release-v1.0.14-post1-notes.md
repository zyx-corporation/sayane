# Sayane Community v1.0.14.post1

Native-First Resident App Hardening

## Summary

Sayane `v1.0.14.post1` continues the current resident app release line.

This post-release adds or stabilizes:

- native macOS as the primary operator-facing UI path
- `/app/ui` as a debug-only compatibility surface for smoke, fallback, and handoff
- action-first native recovery/navigation surfaces
- fail-closed launcher/runtime checks for local Bridge and native smoke
- package build exclusions that keep local Swift build outputs out of the sdist

## Commands

```bash
bash scripts/check-resident-app-release-smoke.sh --start --with-native
bash scripts/build-wheel.sh
```

## Operator impact

- the native app is now the default operator path in docs and handoff material
- browser shell usage remains available, but explicitly as debug/smoke compatibility
- local release verification stays reproducible even when user-local Python shims are damaged
- package artifacts stay small enough for practical release handling

## Safety boundary retained

- No production resident daemon runtime
- No daemon identity/readiness/API proof by startup alone
- No direct profile patch UI
- No OS service integration closure in this release
