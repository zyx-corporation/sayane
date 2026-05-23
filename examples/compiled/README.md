# Compiled prompt examples

Generated from `examples/profiles/minimal.yaml` via Phase 1 CLI.

```bash
omomuki compile --target chatgpt --profile examples/profiles/minimal.yaml
omomuki compile --target claude --profile examples/profiles/minimal.yaml
```

| File | Target |
|------|--------|
| `chatgpt.json` | OpenAI chat `messages` |
| `claude.json` | Anthropic `system` + `messages` |
