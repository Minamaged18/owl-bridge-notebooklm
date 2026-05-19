# Cursor Integration

Connect OWL Bridge to Cursor IDE for NotebookLM-powered research.

## Configuration

Add to `~/.cursor/mcp.json`:

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

In Cursor's AI chat, ask:
```
What notebooks do I have in NotebookLM?
```

## Troubleshooting

| Problem | Fix |
|---|---|
| MCP server not found | Restart Cursor after editing mcp.json |
| Tools not showing | Check Cursor output panel for MCP errors |
| Auth issues | Use cookie injection workflow (see auth-fix skill) |
