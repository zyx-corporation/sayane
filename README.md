# Sayane (紗綾音)

[日本語版 README](README_ja.md) · [Documentation](docs/index.md) · [Roadmap](docs/roadmap.md)

**Sayane is a local-first toolkit for carrying persona, context, prompts, and audit trails across LLM workflows.**

It keeps your canonical context on your own machine, compiles it for different LLM runtimes such as ChatGPT and Claude, and prevents captured changes from being merged blindly.

Your context should not disappear when you change models.

## Why Sayane exists

AI work is increasingly spread across multiple tools: ChatGPT, Claude, Gemini, Cursor, local models, browser extensions, and knowledge bases. Each runtime has its own memory, prompt format, and assumptions. As a result, serious users often lose:

- the context behind an answer,
- the persona or working stance used to produce it,
- the history of what changed,
- the ability to review whether a captured insight should become part of the canonical profile.

Sayane separates your context from any single vendor memory or chat service. It treats persona and context as local, reviewable project assets.

## What Sayane does

| Need | Sayane mechanism |
|------|------------------|
| Keep a canonical user profile locally | Sayane Profile in `~/.sayane/` |
| Generate prompts for different LLMs | Profile → Prompt IR → target adapter |
| Avoid blind context merges | capture → candidate → evaluate → approve/reject |
| Track accepted and rejected changes | lineage records |
| Use local Markdown context | `context/`, storage index, optional Obsidian/Git workflows |
| Connect tools and editors | CLI, Local Bridge, MCP server, Chrome Extension |

## Current status

Community Edition **v1.0.3** is available on PyPI and supports the core local-first workflow.

| Interface | Status | Primary use |
|-----------|--------|-------------|
| CLI | Available | init / compile / candidate / storage |
| Local Bridge | Available | `sayane serve` + local HTTP API |
| MCP Server | Available | Cursor / Claude Desktop integration |
| Chrome Extension | Available | capture / context insert / candidate actions |
| RDE/Candidate evaluation | Available | evaluate / approve / reject / lineage |
| Storage | Available | Markdown / Obsidian / Git-oriented workflows |

## Try it in 5 minutes

Install the CLI first. See [docs/install.md](docs/install.md) for detailed installation notes.

```bash
# PyPI (macOS / Linux / Windows with Python 3.11+)
pip install 'sayane==1.0.3'
```

```bash
# macOS / Linux install script
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

```powershell
# Windows PowerShell install script
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

Verify the core flow:

```bash
sayane --version
sayane init
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

This verifies:

- local profile store initialization,
- target-specific prompt compilation from one profile,
- the basic flow: Profile → Prompt IR → Adapter output.

## Core workflow

```text
Sayane Profile (local canonical context)
        ↓
Prompt IR (runtime-independent intermediate representation)
        ↓
Adapter (ChatGPT / Claude / Gemini / local targets)
        ↓
Target-specific prompt output

captured context → Candidate → evaluation → approve/reject → lineage
```

The LLM is not the owner of your persona. It is a runtime that receives a compiled prompt from your local profile.

## Core principles

### 1. Separate persona from runtime

Your canonical persona and context belong to the local Sayane Profile, not to vendor memory.

### 2. Compile through Prompt IR

Do not copy one giant prompt string across runtimes. Compile one canonical profile into target-specific outputs.

### 3. Review meaning changes before merge

Captured context should become a candidate first. It should be evaluated, accepted, rejected, and recorded.

```text
capture → candidate → evaluate (RDE/UIB-inspired review) → approve/reject → lineage
```

### 4. Prefer local-first portability

Sayane is designed so that serious AI work can remain inspectable, portable, and independent from any single hosted LLM memory.

## Documentation

Start here:

- [Installation](docs/install.md)
- [Getting started](docs/getting-started.md) (Japanese)
- [CLI manual](docs/cli-manual.md)
- [Local Bridge](docs/bridge-manual.md)
- [MCP Server](docs/mcp-manual.md)
- [Chrome Extension](docs/extension-manual.md)
- [RDE / Candidate evaluation](docs/evaluation-manual.md)
- [Storage / Obsidian / Git](docs/storage-manual.md)
- [Docs index](docs/index.md)

## Development

```bash
git clone https://github.com/zyx-corporation/sayane.git
cd sayane
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

Development references:

- [CI policy](docs/ci.md)
- [Development principles](docs/development-principles.md)
- [Roadmap](docs/roadmap.md)

## Positioning

Sayane is not a prompt snippet manager.

It is a small infrastructure layer for people who want AI collaboration to be:

- portable across models,
- local-first by default,
- reviewable before merge,
- inspectable after change,
- grounded in explicit persona, context, and lineage.

## License

Apache License 2.0  
SPDX-License-Identifier: Apache-2.0
