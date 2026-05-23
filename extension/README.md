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

## Security

- Extension does not edit Profile directly; capture → Candidate only.
- Bearer token stored in `chrome.storage.sync` (user-provided).
