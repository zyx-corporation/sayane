# Sayane Community v1.0.14

Resident App Release Reliability

## Summary

Sayane v1.0.14 packages the current resident app release-readiness line.

This release stabilizes:

- Bridge startup when optional native `watchfiles` wheels are broken
- one-command resident app release smoke across API, UI session, and native
  macOS preview
- local package metadata verification through an isolated reproducible check

## Commands

```bash
bash scripts/check-resident-app-release-smoke.sh --start --with-native
bash scripts/build-wheel.sh
```

## Safety boundary retained

- No production resident daemon runtime
- No daemon identity/readiness/API proof by startup alone
- No direct profile patch UI
- No OS service integration closure in this release
