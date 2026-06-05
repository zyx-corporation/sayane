# Context Portability — Import to Candidate Review

## Principle

**Import is not merge.** Imported context must pass through Candidate Review before entering canonical storage.

## Flow

```text
bundle import
  → parse / validate metadata
  → diff against stored profile
  → generate Candidates
  → Candidate Review (evaluate / approve / reject / edit)
  → approved → stored context with lineage
```

## Supported Formats

| Format | Extension | Status |
|---|---|---|
| YAML | `.yaml`, `.yml` | ✅ Full support |
| JSON | `.json` | ✅ |
| Markdown | `.md` | ⚠️ Partial — identity, knowledge, important_terms sections |

## CLI

```bash
# Import a YAML bundle
sayane import-bundle bundle.yaml --profile default

# Import a markdown bundle
sayane import-bundle bundle.md --profile default
```

## Bridge API

```bash
POST /import
Content-Type: application/json
Authorization: Bearer <token>

{
  "path": "/path/to/bundle.yaml",
  "profile_id": "default",
  "source_format": "yaml",
  "source_target": "chatgpt",
  "source_scopes": ["identity", "interaction"]
}
```

Response:
```json
{
  "import_id": "abc123...",
  "candidate_count": 2,
  "candidate_ids": ["def456...", "ghi789..."]
}
```

## Safety Model

### What Import Does NOT Do

- Does not directly mutate canonical Profile IR
- Does not silently merge imported data
- Does not overwrite existing context
- Does not import `promptExport: never` fields as approved
- Does not auto-import formation private_raw data

### What Import Does

1. **Parse** the bundle and extract metadata
2. **Diff** each section against stored profile
3. **Generate Candidates** with:
   - `action: "add"` for new sections/values
   - `action: "update"` for changed values
   - No candidate for identical values
4. **Preserve import metadata** in lineage
5. **Infer conservative policy** where absent

### Conflict Handling

| Scenario | Candidate Type |
|---|---|
| New section, not in profile | `add` |
| Changed value in existing section | `update` → meaning_changed |
| Identical value | No candidate (duplicate) |
| Unknown section format | `review_required` |

## Lineage

Each imported candidate records:

```
Source: bundle_import/yaml
URI: /path/to/bundle.yaml
Import ID: <uuid>
Source target: chatgpt
Source scopes: [identity, interaction]
```

## Formation-Layer Policy

| Layer | Import Behavior |
|---|---|
| abstracted_effect | Candidate generated, reviewable |
| private_raw | Blocked — never imported |
| session_consent | Blocked — session-scoped only |

Policy follows `docs/formation-layer-ethics.md`.

## Limitations

- Markdown parsing is partial (identity, knowledge, important_terms)
- ChatGPT-compact markdown format is not yet parsed
- No automated conflict resolution
- No cross-LLM semantic diff
