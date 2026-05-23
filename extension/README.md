# Omomuki Chrome Extension

Phase 3 MVP: capture web context via Local Bridge and insert context packets into ChatGPT / Claude.

## Prerequisites

```bash
pip install -e .
omomuki init
omomuki serve   # keep running — http://127.0.0.1:38741
```

Copy bearer token from `~/.omomuki/bridge.token` into extension **Options**.

## Build & load

```bash
cd extension
npm install
npm run build
```

Chrome → Extensions → Load unpacked → select this `extension/` folder.

## Features

| Action | Description |
|--------|-------------|
| Capture selection | Sends selected text to Bridge `POST /capture` |
| Capture page | Sends page title/URL/text excerpt as candidate |
| Insert (ChatGPT / Claude) | Fetches context packet from Bridge and fills LLM input |

## Site adapters

DOM logic lives in `src/sites/` (`chatgpt.ts`, `claude.ts`). If LLM UIs change, update selectors there. Failure codes: `INPUT_NOT_FOUND`, `SITE_MISMATCH`, `UNSUPPORTED_SITE`.

## Permissions

| Permission | Purpose |
|------------|---------|
| `storage` | Bridge URL / token in Options |
| `activeTab` | Read selection on the tab where you opened the popup |
| `scripting` | Inject helpers for capture / LLM insert |
| Host: `127.0.0.1` | Local Bridge |
| Host: ChatGPT / Claude | Context insert adapters |

Chrome (JA) may label removed `tabs` as 「閲覧履歴の読み取り」— this extension does **not** use the history API.

After manifest changes: remove the extension and **Load unpacked** again (Update alone may not refresh permission UI).

## Security

- Extension does not edit Profile directly; capture → Candidate only.
- Bearer token stored in `chrome.storage.sync` (user-provided).
