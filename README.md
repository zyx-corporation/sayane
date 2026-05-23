# Omomuki

Omomuki is a local-first persona and context portability tool for cross-LLM collaboration.

It helps users extract, structure, migrate, and evaluate their personal context, working style, values, and response preferences across different LLM runtimes such as ChatGPT, Claude, Gemini, and open-source models.

Omomuki treats LLMs as execution substrates, not owners of persona.

## Concept

Omomuki is built around a simple architectural principle:

> Separate persona from runtime.

A user's persona, context, policy, and working memory should not be locked inside a single AI platform. Omomuki defines reusable intermediate representations for persona and prompts, then compiles them into model-specific formats through adapters.

```text
Omomuki Profile
        ↓
Prompt IR
        ↓
Strategy
        ↓
Adapter
        ↓
LLM Runtime
        ↓
Output
        ↓
Evaluation / Lineage
```

## Initial Product Shape

Omomuki will begin as a standalone application composed of:

- a Python core library
- a Python CLI
- a local bridge API
- a Chrome Extension written in TypeScript

The Chrome Extension captures and inserts context. The CLI and core library own profile storage, transformation, lineage, and evaluation.

## Core Goals

- Keep persona and personal context portable across LLMs.
- Avoid platform-specific memory lock-in.
- Compile structured persona/context data into model-specific prompt formats.
- Support local-first storage and user-controlled lineage.
- Evaluate profile changes before merging them into long-term persona state.
- Provide reusable modules for future Kotonoha, Obsidian, VSCode, MCP, and desktop integrations.

## Documentation

Project design documents are maintained in Japanese under [`docs/`](docs/).

## Development (Phase 0)

Repository layout:

```text
schemas/          JSON Schema (Profile, Prompt IR)
src/omomuki/      Python core package (subpackages by layer)
extension/        Chrome Extension skeleton (TypeScript)
examples/         Sample profiles and fixtures
tests/            pytest
```

Setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

```bash
cd extension && npm install && npm run build
```

See [`docs/ci.md`](docs/ci.md) for CI policy.

### CLI (Phase 1)

See the [CLI manual](docs/cli-manual.md) (Japanese) for full usage.

```bash
pip install -e .
omomuki init
omomuki profile inspect --profile examples/profiles/minimal.yaml
omomuki compile --target chatgpt --profile examples/profiles/minimal.yaml
omomuki compile --target claude --profile examples/profiles/minimal.yaml
omomuki export --format markdown --target claude --profile examples/profiles/minimal.yaml
```

## License

Omomuki is licensed under the Apache License, Version 2.0.

SPDX-License-Identifier: Apache-2.0
