## Sayane Community Edition v1.0.2

Local-first persona and context portability for cross-LLM collaboration.

### Highlights

- **Extension provider registry** — dynamic popup insert UI; active targets: ChatGPT, Claude, Gemini, DeepSeek (Extension **0.3.5**)
- **CLI `sayane capture`** — save pending Candidates from `--text`, `--file`, or stdin
- **Gemini / DeepSeek compile adapters** — `sayane compile --target gemini|deepseek`
- **WinGet / Scoop draft** manifests under `packaging/` ([#83](https://github.com/zyx-corporation/sayane/issues/83))
- L3 Playwright E2E pass recorded in `docs/acceptance-spec.md` §6.1

### Install

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/v1.0.2/scripts/install.sh | bash
```

Or:

```bash
pip install "sayane @ git+https://github.com/zyx-corporation/sayane.git@v1.0.2"
```

Extension: `cd extension && npm run build` → load unpacked in Chrome.

### Verification

- **171** pytest passed (2026-05-30)
- Closes: #96, #83, #85, #84 (see CHANGELOG)

**Full changelog**: [CHANGELOG.md](https://github.com/zyx-corporation/sayane/blob/v1.0.2/CHANGELOG.md)
