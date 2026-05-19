# HTTP Transport Integration

Run OWL Bridge in HTTP mode for n8n, Zapier, Make, hosted agents, or any HTTP-based MCP client.

## Start Server

```bash
npx notebooklm-mcp@latest --transport http --port 3000 --host 0.0.0.0
```

Or via env vars:

```bash
NOTEBOOKLM_TRANSPORT=http NOTEBOOKLM_PORT=3000 NOTEBOOKLM_HOST=0.0.0.0 npx notebooklm-mcp@latest
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/mcp` | JSON-RPC requests/responses |
| `GET` | `/mcp` | SSE stream (uses `Mcp-Session-Id` header) |
| `DELETE` | `/mcp` | Terminate a session |
| `GET` | `/healthz` | Liveness probe |

## curl Example

```bash
# Initialize session
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0.0"}
    }
  }'

# List tools (use Mcp-Session-Id from previous response)
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Call a tool
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "list_notebooks",
      "arguments": {}
    }
  }'
```

## n8n Setup

1. Use the **MCP Client** node in n8n
2. Set transport to **HTTP**
3. URL: `http://your-server:3000/mcp`
4. The node handles session management automatically

## Zapier / Make

Use **Webhooks** → **POST** to `http://your-server:3000/mcp` with JSON-RPC body.

## Security

- Default bind: `127.0.0.1` (localhost only)
- For remote access: `--host 0.0.0.0` (trusted networks only)
- Add a reverse proxy (nginx) with HTTPS for production
- Consider adding API key authentication at the proxy level

## Troubleshooting

| Problem | Fix |
|---|---|
| Connection refused | Check server is running and port is correct |
| Session errors | Include `Mcp-Session-Id` header on all requests after initialize |
| CORS errors | Add CORS headers at reverse proxy level |
| Auth fails | Same as stdio — use cookie injection for headless |
