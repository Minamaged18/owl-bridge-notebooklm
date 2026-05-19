# Claude Code Integration

Connect OWL Bridge to Claude Code for NotebookLM-powered research.

## Installation

```bash
claude mcp add notebooklm -- npx notebooklm-mcp@latest
```

Or with a local build:

```bash
claude mcp add notebooklm -- node /absolute/path/to/owl-bridge-notebooklm/dist/index.js
```

## Manual Config

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["notebooklm-mcp@latest"]
    }
  }
}
```

## With Auto-Login

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["notebooklm-mcp@latest"],
      "env": {
        "GOOGLE_EMAIL": "your-email@gmail.com",
        "GOOGLE_PASSWORD": "your-password"
      }
    }
  }
}
```

## Verification

In Claude Code, ask:
```
List my NotebookLM notebooks
```

Expected: Claude calls `list_notebooks` and returns your notebooks.

## Troubleshooting

| Problem | Fix |
|---|---|
| "No tools available" | Restart Claude Code after adding MCP server |
| Auth fails on headless | Use VNC + cookie injection (see auth-fix skill) |
| `setup_auth` hangs | Normal — it opens Chrome for interactive login |
