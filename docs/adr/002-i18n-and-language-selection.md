# ADR-002: i18n and Language Selection

## Status

Accepted

## Date

2026-06-09

## Context

Chronicle Stack is intended to record and reconstruct human-AI collaboration across multiple linguistic and cultural contexts.

The project may be used for Japanese essays, English specifications, Chinese-facing reports, multilingual artifacts, AI-generated translations, external conversation imports, future Sayane context bundles, future dashboards, and future CSG-RAG retrieval views.

If Chronicle Stack is designed only for one language, later localization will become expensive and may also distort meaning. More importantly, language selection errors can damage the core purpose of Chronicle Stack: preserving context, decisions, artifact history, and meaning-change boundaries.

For example, a Japanese CLI may manage an English specification, generate a Japanese RDE report, and later export a Chinese summary. These languages must not be collapsed into one field.

The project therefore requires internationalization from the beginning, even if Chronicle Core v0.1 initially exposes only CLI and file-based reports.

The initial supported user-facing languages are:

- `ja`: Japanese
- `en`: English
- `zh-CN`: Mainland China standard Chinese, Simplified Chinese

## Decision

The project requires i18n support as a first-class requirement.

All user-facing UI text, CLI messages, exported report labels, warning messages, and future dashboard labels must be designed so that they can be resolved through a locale-aware translation mechanism.

The future UI must provide a language selector.

The initial language selector must support:

- Japanese (`ja`)
- English (`en`)
- Mainland China standard Chinese (`zh-CN`)

Chronicle Stack must not hard-code Japanese, English, or Chinese user-facing text directly inside business logic, persistence logic, RDE logic, context-boundary logic, source adapters, or domain models.

Chronicle Core v0.1 may keep limited internal developer-facing strings in English, but user-facing messages must be prepared for externalization.

## Scope

This ADR applies to:

- CLI help text
- CLI success messages
- CLI error messages
- empty states
- warnings
- T-RDE boundary messages
- RDE report section labels
- Markdown export labels
- YAML export labels where labels are user-facing
- future dashboard UI
- future management console UI
- future language selector
- future context-bundle import and export views
- future CSG-RAG search result labels
- future provenance and review-status labels
- future Sayane integration messages

This ADR also applies to generated user-visible reports when they are part of the product output.

## Non-goals

This ADR does not require immediate translation of all documentation into all supported languages.

This ADR does not require Chronicle Core v0.1 to implement a full UI.

This ADR does not require multilingual semantic alignment in v0.1.

This ADR does not require Traditional Chinese (`zh-TW`) support in v0.1.

This ADR does not require machine translation.

This ADR does not require artifact content to be translated before recording.

This ADR does not require all internal code identifiers to be localized.

## Locale model

Chronicle Stack must distinguish between:

- UI locale
- CLI output locale
- source language
- artifact language
- document language
- report generation language
- RDE review language
- user preference

These must not be collapsed into one field.

Example:

```yaml
locale_context:
  ui_locale: ja
  cli_locale: ja
  source_language: en
  artifact_language: en
  document_language: en
  report_language: ja
  rde_review_language: ja
  user_preferred_locale: ja
```

A user may operate a Japanese CLI while managing an English specification and generating a Japanese RDE report.

A future dashboard may display a Chinese UI while inspecting a Japanese artifact and exporting an English summary.

## Initial locale keys

```yaml
supported_user_locales:
  - ja
  - en
  - zh-CN

default_user_locale: ja
fallback_user_locale: en
```

`ja` is the default initial product locale.

`en` is the fallback locale.

`zh-CN` is the initial Chinese user-facing locale and means Mainland China standard Chinese using Simplified Chinese.

The shorthand `ch` is deprecated and must not be used in product-facing locale keys. Existing persisted `ch` preferences, if any, should be migrated to `zh-CN` or safely fall back to `en`.

## Language selector requirement

The future UI must provide a visible language selector.

At minimum, the selector should allow:

- 日本語
- English
- 简体中文

The selected language should persist across sessions where practical.

Allowed persistence mechanisms:

- user profile preference if authenticated
- local project setting
- local configuration file
- cookie or local storage for browser UI
- URL parameter for temporary override
- CLI option such as `--locale`
- environment variable for CLI automation

Recommended priority for UI:

1. explicit URL parameter
2. authenticated user preference
3. cookie or local storage
4. browser language
5. default locale

Recommended priority for CLI:

1. explicit `--locale` option
2. environment variable
3. project-level Chronicle metadata preference
4. user-level configuration file
5. system locale
6. default locale

## Translation key rule

User-facing text must be referenced through stable translation keys.

Example:

```yaml
cli.init.created: Chronicle created
cli.artifact.created: Artifact created
cli.artifact.no_artifacts: No artifacts found
cli.error.not_initialized: Chronicle is not initialized in this directory
rde.section.preserved: Preserved
rde.section.transformed: Transformed
rde.section.deviation_risks: Deviation Risks
export.review_status.unreviewed: Unreviewed
```

Translation keys must be semantic, not visual.

Preferred:

```text
cli.artifact.no_artifacts
```

Avoid:

```text
gray_empty_text
```

## T-RDE requirement for i18n

Translations can change meaning.

Therefore, T-RDE must apply to important CLI, UI, and report translations.

T-RDE checks must ask:

1. Does the translation preserve the operational, review, provenance, and reconstruction boundaries?
2. Does the translation avoid making a weaker claim sound stronger?
3. Does the translation preserve uncertainty markers?
4. Does the translation preserve the distinction between event, artifact, version, decision, review status, provenance, confidence, and RDE evaluation?
5. Does the translation avoid turning operational success into semantic acceptance?
6. Does the translation avoid culturally narrowing the concept?

## Critical wording boundaries

The following distinctions must be preserved in all supported languages:

- event recorded is not decision accepted
- artifact created is not artifact approved
- artifact updated is not artifact reviewed
- decision recorded is not decision correct
- RDE record exists is not complete meaning validation
- review status is not truth
- provenance is not correctness
- confidence is not truth
- export success is not content validation
- index rebuild success is not semantic completeness
- CLI success is not human acceptance
- Delta-M is not value
- context included is not context endorsed
- source language is not report language
- artifact language is not UI locale

Any translation that collapses these distinctions violates this ADR.

## Translation quality policy

Machine translation may be used only as a draft aid.

Product-facing translations of critical labels, warnings, CLI errors, RDE explanations, review-status labels, provenance labels, and exported report headings must be reviewed by a human or by an explicit T-RDE translation review process before being treated as accepted.

Critical translation categories:

- warnings
- destructive-action messages
- artifact overwrite messages
- review-status labels
- decision labels
- RDE section labels
- T-RDE explanations
- provenance boundary messages
- context-boundary messages
- export summaries
- CLI error messages
- future dashboard status labels

## Chronicle metadata requirements

Chronicle metadata may include locale preferences, but locale fields must remain explicit.

Recommended future metadata shape:

```yaml
locale_context:
  default_user_locale: ja
  fallback_user_locale: en
  cli_locale: ja
  report_language: ja
```

For v0.1, this may remain documentation-only. Future schema changes must preserve backward compatibility.

## Artifact language metadata

Artifact language should be represented separately from UI and report language.

Recommended future artifact metadata:

```yaml
artifact_language: en
source_language: en
report_language: ja
```

This allows Chronicle Stack to manage multilingual workflows without forcing translation or altering artifact content.

## CLI implementation requirements

Chronicle Core v0.1 should introduce an i18n-ready CLI architecture even if full translations are not implemented immediately.

The first implementation should include or prepare for:

- locale registry
- translation dictionaries or message catalogs
- default locale handling
- fallback handling
- CLI locale resolution
- test-case specs for locale behavior

The CLI should avoid embedding user-facing strings deep inside domain services.

Domain services may return structured data or error objects. CLI rendering should be responsible for locale-specific messages.

## Future UI implementation requirements

When a dashboard or management UI is introduced, it must include:

- language selector component
- locale registry
- translation files or dictionaries
- default locale handling
- fallback handling
- tests or test-case specs for language switching

The management UI must support the language selector from its first non-prototype release.

## Testing requirements

At minimum, the project must define tests or test scenarios for:

- default locale resolution
- fallback locale behavior
- unsupported locale falls back to English
- explicit CLI locale overrides default locale
- selected UI locale persists where practical
- old `ch` locale preferences migrate or fall back safely
- critical wording remains distinct across locales
- CLI operational labels do not become semantic acceptance claims in translation
- RDE section labels preserve the six-part meaning-change structure across locales
- export labels do not overstate review status or RDE completion

## Recommended file structure

The exact implementation is framework-dependent, but a possible CLI-oriented structure is:

```text
src/chronicle/i18n/locales/ja.yaml
src/chronicle/i18n/locales/en.yaml
src/chronicle/i18n/locales/zh-CN.yaml
src/chronicle/i18n/locale_registry.py
src/chronicle/i18n/translate.py
src/chronicle/i18n/resolver.py
```

For future UI implementation, an equivalent structure may be used:

```text
src/ui/i18n/locales/ja.json
src/ui/i18n/locales/en.json
src/ui/i18n/locales/zh-CN.json
src/ui/i18n/locale-registry.ts
src/ui/i18n/translate.ts
src/ui/components/language-selector.tsx
```

For documentation-only planning, equivalent files may be specified under:

```text
docs/i18n/
```

## Design-pattern implications

### Strategy pattern

Locale resolution can be represented as a strategy to support CLI option, environment variable, project metadata, user preference, browser language, URL parameter, and fallback logic.

Examples:

- CliLocaleResolutionStrategy
- UiLocaleResolutionStrategy
- ReportLanguageResolutionStrategy

### Adapter pattern

External locale codes may need adapters if product locale keys are mapped to browser, API, OS, or standards-compliant locale identifiers.

Examples:

- BrowserLocaleAdapter
- SystemLocaleAdapter
- LegacyLocaleAdapter

### Specification pattern

Critical wording constraints may be represented as specifications for translation review.

Examples:

- ReviewStatusTranslationSpec
- RdeBoundaryTranslationSpec
- ProvenanceBoundaryTranslationSpec
- OperationalVsSemanticStatusSpec

### Repository pattern

Translation catalogs may be loaded through a repository-like boundary if they become replaceable resources.

Examples:

- TranslationCatalogRepository
- LocalePreferenceRepository

## Consequences

### Benefits

- multilingual CLI, reports, and future UI are supported from the beginning
- later public release is easier
- language-specific meaning drift becomes auditable
- RDE and review-status wording remains safe across languages
- Chronicle Stack can operate across Japanese, English, and Chinese workflows
- future Sayane and CSG-RAG integrations can preserve language boundaries

### Costs

- more upfront structure for CLI and report rendering
- translation maintenance burden
- need for i18n tests
- need to review critical labels across languages
- possible future addition of other Chinese locale variants such as `zh-TW`
- need to keep internal domain models separate from localized presentation text

## Non-goals

This ADR does not define final dashboard UI behavior.

This ADR does not require immediate translation of every document.

This ADR does not require automatic translation of artifact content.

This ADR does not define multilingual semantic retrieval for CSG-RAG.

This ADR does not require all experimental sketches to follow production-grade i18n.

However, once prototype logic influences persisted locale preferences, exported documents, CLI output, review status, provenance, or user-visible interpretation, it must be brought under this ADR.

## Related documents

- `docs/adr/001-t-rde-tdd-and-design-patterns.md`
- `docs/specs/chronicle-stack-basic-spec-v0.1.md`
- `docs/data-model.md`
- `docs/cli-reference.md`
- `docs/storage-format.md`
- `docs/testing-strategy.md`
