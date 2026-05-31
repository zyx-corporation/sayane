# Sayane (紗綾音)

[日本語版 README](README_ja.md)

Sayane is a **local-first persona/context portability tool** for cross-LLM workflows.  
It keeps a canonical user context locally, then compiles it for different runtimes (ChatGPT, Claude, etc.).

## What this tool does

- Keeps canonical persona/context in a local store (`~/.sayane/`)
- Compiles one Profile into per-target prompt outputs
- Prevents immediate blind merges (capture → candidate → evaluate)
- Tracks approved/rejected changes as lineage

## What you can verify in 5 minutes

Install CLI first (detailed steps: [docs/install.md](docs/install.md)).

```bash
# PyPI (macOS / Linux / Windows with Python 3.11+)
pip install 'sayane==1.0.3'

# macOS / Linux (install script)
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

Then verify the core flow:

```bash
sayane --version
sayane init
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

Within 5 minutes, you can verify:

- local profile store initialization
- target-specific prompt compilation from one profile
- the core flow: Profile → compile

## Current status (Community Edition v1.0.3)

| Interface | Status | Primary use |
|-----------|--------|-------------|
| CLI | Available | init / compile / candidate / storage |
| Local Bridge | Available | `sayane serve` + HTTP API |
| MCP Server | Available | Cursor / Claude Desktop integration |
| Chrome Extension | Available | capture / context insert / candidate actions |
| RDE/Candidate evaluation | Available | evaluate / approve / reject / lineage |
| Storage (Obsidian/Git) | Available | import / index / export / commit |

## Start here

- [Installation](docs/install.md)
- [Getting started](docs/getting-started.md) (Japanese)
- [CLI manual](docs/cli-manual.md)
- [Local Bridge](docs/bridge-manual.md)
- [MCP Server](docs/mcp-manual.md)
- [Chrome Extension](docs/extension-manual.md)
- [RDE / Candidate evaluation](docs/evaluation-manual.md)
- [Storage / Obsidian / Git](docs/storage-manual.md)
- [Docs index](docs/index.md)

## Core principles

### 1. Separate persona from runtime

Canonical persona belongs to local Sayane Profile, not vendor memory.

### 2. Compile through intermediate representation (Prompt IR)

Do not copy one prompt string across runtimes; re-compile per target.

### 3. Evaluate meaning changes before merge

```text
capture → candidate → evaluate (RDE/UIB) → approve/reject → lineage
```

## Development

- [CI policy](docs/ci.md)
- [Development principles](docs/development-principles.md)
- [Roadmap](docs/roadmap.md)

## License

Apache License 2.0  
SPDX-License-Identifier: Apache-2.0
