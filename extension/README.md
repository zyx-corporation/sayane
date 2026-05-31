# Sayane Chrome Extension

Phase 3: capture web context via Local Bridge and insert context packets into LLM UIs.

**Supported Insert (Bridge compile):** ChatGPT, Claude, Gemini, DeepSeek, Open WebUI (`local-openwebui`).  
**Preview only:** `local-custom` (generic localhost DOM).

## Prerequisites

```bash
pip install 'sayane==1.0.3'
sayane init
sayane serve   # keep running — http://127.0.0.1:38741
```

Copy bearer token from `~/.sayane/bridge.token` into extension **Options**.

## Build & load

```bash
cd extension
npm install
npm run build
```

### E2E (Playwright)

```bash
pip install -e ".[dev]"   # from sayane repo root
npm run test:e2e:install
npm run test:e2e
```

See [../docs/extension-e2e.md](../docs/extension-e2e.md).

Chrome → Extensions → Load unpacked → select this `extension/` folder (manifest **0.3.8+**).

## Features

| Action | Description |
|--------|-------------|
| Capture selection | Sends selected text to Bridge `POST /capture` |
| Capture page | Sends page title/URL/text excerpt as candidate |
| Insert (providers) | Fetches context packet from Bridge and fills LLM input |

## Site adapters

Provider logic: `src/providers/` (`registry.ts`, `local-host.ts` for Open WebUI URL rules).  
Legacy `src/sites/*` re-exports providers. Failure codes: `INPUT_NOT_FOUND`, `SITE_MISMATCH`, `UNSUPPORTED_SITE`.

### Open WebUI

- URL: `http://localhost:PORT/` or `/c/...` after login (not `/auth`)
- Keep the Open WebUI tab **active** before opening the popup
- See [../docs/extension-manual.md](../docs/extension-manual.md)

## Permissions

| Permission | Purpose |
|------------|---------|
| `storage` | Bridge URL / token in Options |
| `activeTab` | Read selection on the tab where you opened the popup |
| `scripting` | Inject helpers for capture / LLM insert |
| Host: `127.0.0.1` / `localhost` | Local Bridge + Open WebUI |
| Host: ChatGPT / Claude / Gemini / DeepSeek | Context insert adapters |

Chrome (JA) may label removed `tabs` as 「閲覧履歴の読み取り」— this extension does **not** use the history API.

After manifest changes: remove the extension and **Load unpacked** again (Update alone may not refresh permission UI).

## Security

- Extension does not edit Profile directly; capture → Candidate only.
- Bearer token stored in `chrome.storage.sync` (user-provided).

## Follow-ups (#96)

- `local-librechat` / `local-anythingllm` adapters
- Gemini / DeepSeek real DOM E2E (scheduled / manual)
