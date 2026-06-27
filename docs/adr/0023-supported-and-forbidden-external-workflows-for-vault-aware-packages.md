# ADR 0023: Supported and forbidden external workflows for vault-aware packages

## Status

Accepted — 2026-06-28

## Context

ADR 0022 defined the vault-aware external package as the supported reviewable
exchange format, but the operator still needed an explicit statement of what
this format is and is not for.

Without that boundary, a package can drift back into the same ambiguous role
that older external vault workflows had: half review artifact, half unofficial
working store.

## Decision

Vault-aware external packages carry explicit supported and forbidden workflow
metadata in `manifest.json`.

Current supported operator actions:

- `offline_review`
- `candidate_generation_preview`
- `manual_redacted_handoff`

Current forbidden workflows:

- `canonical_working_store`
- `automatic_external_sync_promotion`
- `direct_profile_merge_without_review`
- `long_lived_unreviewed_archive`

## Consequences

Positive:

- the package itself now states the allowed operator use directly
- preview output can show the same boundary without cross-referencing docs
- supported path vs forbidden path becomes executable metadata, not prose only

Negative:

- future expansion still requires deliberate ADR updates
- unsupported workflows may remain manually possible outside Sayane, but they
  are now explicitly outside contract

## Related

- `docs/adr/0022-vault-aware-external-packages-are-the-supported-reviewable-exchange-format.md`
- `docs/storage-manual.md`
