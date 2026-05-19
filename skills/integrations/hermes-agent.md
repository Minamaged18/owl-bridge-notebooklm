# Hermes Agent Integration

Connect OWL Bridge to Hermes Agent for NotebookLM-powered research.

## Configuration

Add to `~/.hermes/config.yaml` under `mcp_servers:`:

```yaml
mcp_servers:
  notebooklm:
    command: npx
    args: ["notebooklm-mcp@latest"]
```

## With Auto-Login

```yaml
mcp_servers:
  notebooklm:
    command: npx
    args: ["notebooklm-mcp@latest"]
    env:
      GOOGLE_EMAIL: "your-email@gmail.com"
      GOOGLE_PASSWORD: "your-password"
```

## With Cookie Injection (Headless Server)

```yaml
mcp_servers:
  notebooklm:
    command: npx
    args: ["notebooklm-mcp@latest"]
    env:
      # Pre-inject cookies via the inject_cookies tool after startup
      # Or set HEADLESS=false and use VNC
```

## Verification

Ask Hermes:
```
List my NotebookLM notebooks
```

Or:
```
Check notebooklm health
```

## Troubleshooting

| Problem | Fix |
|---|---|
| MCP server not loading | Check `~/.hermes/config.yaml` syntax |
| Auth fails | Use VNC + cookie injection (see auth-fix skill) |
| Gateway not picking up config | Hermes auto-reloads — if not, restart gateway |
| `inject_cookies` not available | Make sure you're using OWL Bridge fork, not original |
