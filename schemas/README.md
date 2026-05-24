# Schemas

JSON Schema definitions for Sayane data structures.

| File | Description |
|------|-------------|
| `sayane-profile.schema.json` | Sayane Profile (persona / context structure) |
| `prompt-ir.schema.json` | Prompt IR (pre-adapter intermediate representation) |
| `sayane-confidentiality-policy.schema.json` | Confidentiality Policy (Commercial Edition audit contract) |

Example policies: `examples/confidentiality/default.policy.yaml`

Detection engine and audit store implementations are provided by Commercial Edition (not in this OSS repo). OSS publishes the schema contract only (Issue [#66](https://github.com/zyx-corporation/sayane/issues/66)).
