---
name: gemini-cli
description: Use Google Gemini CLI for AI-powered terminal workflows — coding, file operations, web search, MCP servers. Works on headless servers via NO_BROWSER + VNC OAuth flow. Use when the user wants to use Gemini CLI, authenticate it on a headless server, or integrate it with OWL Bridge.
triggers:
  - gemini cli
  - gemini-cli
  - google gemini cli
  - gemini terminal
  - gemini oauth
  - gemini headless
  - gemini authentication
  - gemini pro
  - gemini code assist
---

# 🦉 Gemini CLI — Headless Server Integration

> Use Google's Gemini CLI on a headless VPS with OAuth authentication via VNC + CDP.

## What is Gemini CLI?

Gemini CLI is Google's open-source AI agent for the terminal. It brings Gemini models directly into your shell with:

- **Code understanding & generation** — query, edit, debug codebases
- **File operations** — read, write, search files
- **Shell commands** — run terminal commands
- **Web search** — Google Search grounding
- **MCP support** — extend with custom tools (including OWL Bridge!)
- **Free tier** — 60 req/min, 1,000 req/day with personal Google account
- **Pro tier** — Gemini 3 with 1M token context (Google One AI Pro)

## Installation

```bash
# Install globally
npm install -g @google/gemini-cli

# Or run instantly
npx @google/gemini-cli

# Verify
gemini --version
```

## Authentication on Headless Servers

### The Problem

Gemini CLI's OAuth flow opens a browser for Google login. On a headless server, there's no browser.

### The Solution: NO_BROWSER + VNC + CDP

1. Set `NO_BROWSER=true` — Gemini CLI prints the URL instead of opening a browser
2. Navigate VNC Chrome to the URL via CDP (Chrome DevTools Protocol)
3. Complete the OAuth flow in VNC Chrome (account chooser → consent → callback)
4. Copy the authorization code from the callback URL
5. Paste it back into the Gemini CLI terminal

### Prerequisites

- VNC stack running: Xvfb + x11vnc + websockify (see `vnc-setup` skill)
- Chrome CDP accessible at `http://localhost:9222`
- Python `websocket-client` package: `pip install websocket-client`

### Step-by-Step

**1. Start Gemini CLI in interactive mode:**

```bash
export NO_BROWSER=true
gemini
```

**2. Copy the OAuth URL from the terminal:**

```
Please visit the following URL to authorize the application:
https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=...
Enter the authorization code: 
```

**3. Navigate Chrome to the URL via CDP:**

```python
import websocket, json, time
from urllib.parse import urlparse, parse_qs

# Get Chrome CDP target
import urllib.request
resp = urllib.request.urlopen("http://localhost:9222/json/list")
targets = json.loads(resp.read())
page = next(t for t in targets if t['type'] == 'page')
ws = websocket.create_connection(page['webSocketDebuggerUrl'])

# Navigate to OAuth URL
ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": "<OAUTH_URL>"}}))
ws.recv()

# Poll for callback URL with authorization code
for i in range(30):
    time.sleep(2)
    ws.send(json.dumps({"id": i+10, "method": "Runtime.evaluate", "params": {"expression": "window.location.href"}}))
    url = json.loads(ws.recv())['result']['result']['value']
    
    if 'codeassist.google.com/authcode' in url:
        code = parse_qs(urlparse(url).query).get('code', [''])[0]
        print(f"CODE: {code}")
        break
    
    # Auto-click account/consent buttons
    ws.send(json.dumps({"id": i+100, "method": "Runtime.evaluate", "params": {"expression": """
        var els = document.querySelectorAll('[data-identifier], button, [role=button]');
        els.forEach(function(el) {
            var t = el.textContent.toLowerCase();
            if (t.includes('mina') || t.includes('sign in') || t.includes('continue') || t.includes('allow')) el.click();
        });
    """}}))
    ws.recv()

ws.close()
```

**4. Paste the code into Gemini CLI:**

The code is pasted into the "Enter the authorization code:" prompt.

**5. Credentials are cached at:**

```
~/.gemini/oauth_creds.json    — OAuth tokens (access + refresh)
~/.gemini/google_accounts.json — Active account
~/.gemini/settings.json        — Auth type configuration
```

### Settings File

Create `~/.gemini/settings.json`:

```json
{
  "selectedAuthType": "oauth-personal",
  "security": {
    "auth": {
      "selectedType": "oauth-personal"
    }
  }
}
```

### Auth Types

| Type | Config | Best For |
|---|---|---|
| OAuth (personal) | `selectedAuthType: "oauth-personal"` | Individual Google accounts, Gemini Pro |
| API Key | `export GEMINI_API_KEY="..."` | Headless without VNC, CI/CD |
| Vertex AI | `GOOGLE_GENAI_USE_VERTEXAI=true` | Enterprise, GCP workloads |

## Usage

### Interactive Mode

```bash
gemini                          # Start interactive session
gemini -p "prompt"             # Non-interactive (headless mode)
gemini -p "prompt" -y         # YOLO mode (auto-approve all)
```

### Non-Interactive Mode (Scripting)

```bash
# Simple text response
gemini -p "Explain this codebase"

# JSON output
gemini -p "List all Python files" --output-format json

# Stream JSON events
gemini -p "Run tests" --output-format stream-json

# Include additional directories
gemini --include-directories ../lib,../docs -p "Review the code"
```

### YOLO Mode (Auto-Approve)

```bash
gemini -y                      # Auto-approve all actions
gemini -p "Refactor this" -y   # Non-interactive + auto-approve
```

### Model Selection

```bash
gemini -m gemini-2.5-flash     # Use specific model
gemini -m gemini-3-pro         # Use Gemini 3 Pro
```

## Gemini CLI + OWL Bridge

Gemini CLI supports MCP servers. You can use OWL Bridge as an MCP server inside Gemini CLI:

```bash
# Add OWL Bridge as MCP server
gemini mcp add notebooklm -- npx notebooklm-mcp@latest
```

Then in Gemini CLI:
```
> @notebooklm List my notebooks
> @notebooklm Ask "What are the key findings?" about notebook "Research"
```

## Troubleshooting

| Problem | Solution |
|---|---|
| "Manual authorization required" | Use interactive mode with NO_BROWSER + VNC |
| "Failed to authenticate with user code" | Code expired — restart flow, paste within 2 min |
| 2FA challenge blocks flow | Complete 2FA on phone, then consent screen appears |
| "Tool not found" | Gemini CLI has different tool names than Hermini |
| File operations blocked | Files must be within workspace directory |
| Auth expires | Refresh token auto-renews; if not, re-run OAuth flow |
| "write_file not found" | Use `read_file`, `grep_search` instead |

## Key Differences from Hermes

| Feature | Gemini CLI | Hermes |
|---|---|---|
| Auth | OAuth / API Key | Config-based |
| File ops | Workspace-scoped | Full filesystem |
| Shell commands | Built-in | Via terminal tool |
| MCP support | Yes | Yes |
| Headless auth | NO_BROWSER + VNC | N/A |
| Free tier | 60 req/min | N/A |
| Pro tier | Google One AI Pro | N/A |

## Migration Note (June 2026)

Google is transitioning Gemini CLI users to **Antigravity CLI**. After June 18, 2026, Google One and unpaid tier users should migrate. Paid Code Assist license holders can continue using Gemini CLI.

See: https://goo.gle/gemini-cli-migration
