# Sayane (紗綾音)

Sayane is a local-first persona and context portability tool for cross-LLM collaboration.

It helps users extract, structure, migrate, and evaluate their personal context, working style, values, and response preferences across different LLM runtimes such as ChatGPT, Claude, Gemini, and open-source models.

Sayane treats LLMs as execution substrates, not owners of persona.

## Core principles

Sayane rests on three design propositions.

### 1. Separate persona from runtime

> Separate persona from runtime.

A user's values, voice, policy, and context live in an **Sayane Profile** on the user's machine. Custom Instructions, project settings, and vendor "memory" are **projections per runtime**, not the source of truth for persona.

LLMs do not *own* persona—they **execute** prompts compiled from the Profile.

### 2. Everything goes through intermediate representation (IR)

Sayane does not copy prompt strings between platforms. It builds **Prompt IR** (an LLM-agnostic intermediate form) from the Profile, then **Adapters** compile to each target format.

```text
Same persona  ≠  same prompt
One Profile  →  per-target optimized output
```

ChatGPT and Claude payloads differ in shape; identity, values, and policy still derive from the same Profile.

### 3. Meaning changes are evaluated and recorded

Updating the Profile is not a blind settings overwrite—it is a **meaning change**. Captured content becomes a **Candidate**, passes RDE/UIB evaluation, and merges only after explicit **approve**. Lineage records approvals and rejections.

```text
capture → Candidate → evaluate (RDE+UIB) → approve / reject → lineage
          (no immediate merge)
```

```text
Sayane Profile  →  Prompt IR  →  Adapter  →  LLM output
        ↑
Candidate (capture) → RDE evaluation → approved merge → Lineage
```

**Local-first**: the canonical store is on the user's machine (`~/.sayane/`). Community Edition uses Git history by default. **Commercial Edition** (Phase 6) — see [sayane-pro](https://github.com/zyx-corporation/sayane-pro/blob/main/docs/commercial-edition.md).

---

## Not just user profile exchange

Exporting Custom Instructions and pasting them into another LLM, or moving a platform-specific settings blob, is **profile exchange**. Sayane aims for something different.

| Aspect | Typical profile exchange | Sayane |
|--------|-------------------------|---------|
| **Data shape** | Platform-specific text or settings blob | LLM-agnostic **Sayane Profile** + **Prompt IR** |
| **Cross-LLM move** | Copy-paste the same string | **Re-compile per target** via Adapters |
| **Updates** | Overwrite / sync success only | **Candidate → evaluate → approve** audits meaning change |
| **History** | None or vendor-limited logs | **Lineage** kept by the user |
| **Context location** | Scattered in each LLM's memory/projects | **context_index** + local Markdown |
| **Ownership** | Often locked in vendor SaaS | **Local-first** (user holds the source of truth) |
| **Immediate apply** | Paste and it applies | Capture does **not** merge immediately; Critical Distortion can be rejected |

The Profile is not a bio field—it is a **structured medium** for LLMs to approach user context: identity, voice, values, policy, and context are separate sections, composed into Prompt IR at compile time.

Design details: [architecture.md](docs/architecture.md) / [Profile and Prompt IR](docs/profile-ir.md)

## Architecture flow

```text
Sayane Profile
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

Sayane will begin as a standalone application composed of:

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

## Installation

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

See [install.md](docs/install.md) for options and uninstall.

## Quick start (from source)

```bash
git clone https://github.com/zyx-corporation/sayane.git
cd sayane
pip install -e ".[dev]"
sayane init
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

See [`docs/ci.md`](docs/ci.md) for development and CI.

## Documentation

Project design documents are maintained in Japanese under [`docs/`](docs/).

**New users**: [Getting started guide](docs/getting-started.md) (Japanese)

| Topic | Manual |
|-------|--------|
| Install | [install.md](docs/install.md) |
| CLI | [cli-manual.md](docs/cli-manual.md) |
| Local Bridge | [bridge-manual.md](docs/bridge-manual.md) |
| MCP Server | [mcp-manual.md](docs/mcp-manual.md) |
| Chrome Extension | [extension-manual.md](docs/extension-manual.md) |

Sayane is licensed under the Apache License, Version 2.0.

SPDX-License-Identifier: Apache-2.0
