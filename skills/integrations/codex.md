# OpenAI Codex CLI Integration

Connect OWL Bridge to OpenAI Codex CLI for NotebookLM-powered research.

## Installation

```bash
codex mcp add notebooklm npx notebooklm-mcp@latest
```

## Verification

In Codex, ask:
```
List my NotebookLM notebooks
```

## Troubleshooting

| Problem | Fix |
|---|---|
| MCP server not found | Run `codex mcp list` to verify registration |
| Auth fails | Use cookie injection workflow (see auth-fix skill) |
