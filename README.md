# 🦉 OWL Bridge — NotebookLM MCP

> **The only NotebookLM MCP server that works on headless servers.**
> Cookie injection · VNC workflow · Stealth Chrome · Multi-account

[![npm](https://img.shields.io/npm/v/notebooklm-mcp.svg)](https://www.npmjs.com/package/notebooklm-mcp)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)](https://www.typescriptlang.org/)
[![MCP](https://img.shields.io/badge/MCP-Streamable--HTTP-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Headless](https://img.shields.io/badge/Headless%20Server-✓-brightgreen.svg)](#headless-server--vnc-workflow)

A fork of [PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp) with critical fixes for headless VPS environments where Google's auto-login gets blocked by CAPTCHA.

**What makes OWL Bridge different:**

| Feature | Original | OWL Bridge |
|---|---|---|
| Headless server support | ❌ CAPTCHA blocks login | ✅ Cookie injection via VNC |
| `inject_cookies` tool | ❌ Not available | ✅ Inject without restart |
| Chrome cookie extraction | ❌ Not included | ✅ Built-in script |
| VNC workflow docs | ❌ Not documented | ✅ Full guide |
| CDP cookie bypass | ❌ Not addressed | ✅ `browser_cookie3` approach |

---

## Quick Start

### Standard (Desktop)

```bash
npx notebooklm-mcp@latest
```

### Headless Server (VPS)

```bash
# Step 1: Set up VNC (one-time)
Xvfb :99 -screen 0 1920x1080x24 &
DISPLAY=:99 x11vnc -display :99 -forever -shared -rfbport 5900 &
websockify --web /usr/share/novnc/ 6080 localhost:5900 &

# Step 2: Log in via VNC browser, then extract cookies
pip install browser_cookie3
python3 scripts/extract_chrome_cookies.py --output ~/.local/share/notebooklm-mcp/browser_state/state.json

# Step 3: Start MCP server — authenticated!
npx notebooklm-mcp
```

---

## The Problem We Solve

On headless servers, `setup_auth` fails because Google shows CAPTCHA challenges that can't be solved in automated Chrome. The original workaround was "just use a desktop" — not an option for VPS users.

**OWL Bridge's solution:** Log in once via a VNC-displayed Chrome (where you can solve CAPTCHA manually), then extract the cookies and inject them into the MCP server. The cookies persist across server restarts.

**Why CDP doesn't work:** Chrome's `Network.getAllCookies` CDP command returns 0 cookies for HTTP-only/secure contexts. We use `browser_cookie3` which reads Chrome's encrypted SQLite cookie database directly.

---

## Authentication

### Method 1: Interactive Login (Desktop)

```
setup_auth → opens visible Chrome → log in once → cookies persisted
```

### Method 2: Cookie Injection (Headless Server) ✨

```
VNC Chrome login → extract_cookies.py → inject_cookies tool → done
```

The `inject_cookies` tool accepts a path to a Playwright-format state.json and loads it into the active browser session without restarting the MCP server.

### Method 3: Auto-login via Env Vars

Set `GOOGLE_EMAIL` and `GOOGLE_PASSWORD` in your environment. The server will attempt automated login on first run. Works on desktop; may trigger CAPTCHA on headless servers.

### Profile Locations

| Platform | Path |
|---|---|
| Linux | `~/.local/share/notebooklm-mcp/chrome_profile/` |
| macOS | `~/Library/Application Support/notebooklm-mcp/chrome_profile/` |
| Windows | `%APPDATA%\notebooklm-mcp\chrome_profile\` |

---

## Headless Server + VNC Workflow

**Full guide for VPS users who need NotebookLM on a server without a display.**

### Prerequisites

```bash
# Install VNC stack
sudo apt install x11vnc novnc websockify

# Install Chrome dependencies (Fedora/RHEL)
sudo dnf install atk at-spi2-atk cups-libs dbus-libs libxkbcommon \
  xcb-util-* libXcomposite libXdamage libXfixes libXrandr mesa-libgbm \
  pango alsa-lib gtk3

# Install Python cookie extractor
pip install browser_cookie3
```

### Start VNC Stack

```bash
# Virtual display
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &

# VNC server
DISPLAY=:99 x11vnc -display :99 -forever -shared -rfbport 5900 -noxdamage &

# noVNC (browser-based VNC client)
websockify --web /usr/share/novnc/ 6080 localhost:5900 &
```

Access at `http://YOUR_IP:6080/vnc.html`

### Log In & Extract

```bash
# Start Chrome with persistent profile on VNC display
DISPLAY=:99 chromium --no-sandbox --disable-gpu \
  --user-data-dir=/root/.notebooklm/profiles/default/browser_profile \
  https://notebooklm.google.com

# After logging in via VNC, extract cookies
python3 scripts/extract_chrome_cookies.py \
  --chrome-profile /root/.notebooklm/profiles/default/browser_profile \
  --output ~/.local/share/notebooklm-mcp/browser_state/state.json

# Verify cookies
python3 scripts/extract_chrome_cookies.py \
  --state ~/.local/share/notebooklm-mcp/browser_state/state.json \
  --verify
```

### Cookie Format

```json
{
  "cookies": [
    {
      "name": "SID",
      "value": "g.a000...",
      "domain": ".google.com",
      "path": "/",
      "httpOnly": true,
      "secure": true
    },
    {
      "name": "__Secure-1PSIDTS",
      "value": "sidts-Cj...",
      "domain": ".google.com",
      "path": "/",
      "httpOnly": true,
      "secure": true
    }
  ]
}
```

Minimum required cookies: `SID` + `__Secure-1PSIDTS`

---

## Tools

### Q&A

| Tool | Purpose |
|---|---|
| `ask_question` | Ask a question against a notebook. Supports session reuse, citation extraction, and per-call browser overrides. |

### Sources & Studio

| Tool | Purpose |
|---|---|
| `add_source` | Add a source (URL or text) to a notebook. |
| `generate_audio` | Generate an Audio Overview. |
| `download_audio` | Save the most recent Audio Overview. |

### Library

| Tool | Purpose |
|---|---|
| `add_notebook` | Add a NotebookLM share-URL to the local library. |
| `list_notebooks` | List every notebook in the library. |
| `get_notebook` | Fetch one notebook by ID. |
| `select_notebook` | Set a notebook as the active default. |
| `update_notebook` | Update notebook metadata. |
| `remove_notebook` | Remove from the local library. |
| `search_notebooks` | Search by name, description, topics, tags. |
| `get_library_stats` | Counts and usage stats. |

### Sessions

| Tool | Purpose |
|---|---|
| `list_sessions` | List active browser sessions. |
| `close_session` | Close one session. |
| `reset_session` | Reset chat history. |

### System

| Tool | Purpose |
|---|---|
| `get_health` | Auth state, session count, configuration snapshot. |
| `setup_auth` | First-time interactive Google login. |
| `re_auth` | Wipe auth + log in again. |
| `cleanup_data` | Categorised preview + delete of stored data. |
| `inject_cookies` | **✨ OWL Bridge exclusive** — Inject cookies from a state.json file without restarting. |

---

## Connect to AI Clients

### Claude Code

```bash
claude mcp add notebooklm -- npx notebooklm-mcp@latest
```

### Cursor

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

### Hermes Agent

```yaml
mcp_servers:
  notebooklm:
    command: npx
    args: ["notebooklm-mcp@latest"]
    env:
      GOOGLE_EMAIL: "your-email@gmail.com"
      GOOGLE_PASSWORD: "your-password"
```

### HTTP Transport (n8n, Zapier, hosted agents)

```bash
npx notebooklm-mcp@latest --transport http --port 3000 --host 0.0.0.0
```

---

## Multi-Account

```bash
npx notebooklm-mcp@latest --account work
npx notebooklm-mcp@latest --account personal
```

Each account gets its own Chrome profile, cookies, and auth state.

---

## Configuration

| Env Var | Default | Purpose |
|---|---|---|
| `HEADLESS` | `true` | Run Chrome headless. |
| `ANSWER_TIMEOUT_MS` | `600000` | Hard ceiling on answer wait. |
| `STEALTH_ENABLED` | `true` | Human-typing/mouse/delay stealth. |
| `NOTEBOOKLM_TRANSPORT` | `stdio` | `stdio` or `http`. |
| `NOTEBOOKLM_PORT` | `3000` | HTTP port. |
| `NOTEBOOKLM_ACCOUNT` | _(unset)_ | Multi-account profile slug. |
| `GOOGLE_EMAIL` | _(unset)_ | Auto-login email. |
| `GOOGLE_PASSWORD` | _(unset)_ | Auto-login password. |

Full reference: [`docs/configuration.md`](./docs/configuration.md)

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `setup_auth` shows CAPTCHA | Google anti-bot on headless | Use VNC + cookie injection |
| `Network.getAllCookies` returns 0 | HTTP-only/secure cookies | Use `browser_cookie3` instead |
| `state.json` validation error | Wrong format | Must be `{"cookies": [{"name":..., "value":..., "domain":...}]}` |
| Auth expires after days | Google cookie rotation | Re-extract cookies from VNC Chrome |
| Chrome won't launch on VPS | Missing deps | Install Chrome dependencies (see above) |

Full troubleshooting: [`docs/troubleshooting.md`](./docs/troubleshooting.md)

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  AI Agent   │────▶│  OWL Bridge  │────▶│  Google         │
│  (Claude,   │◀────│  MCP Server  │◀────│  NotebookLM     │
│   Cursor,   │     │              │     │                 │
│   Hermes)   │     │  ┌────────┐  │     │  ┌───────────┐  │
└─────────────┘     │  │Patchr. │  │     │  │ Chrome    │  │
                    │  │Chrome  │  │     │  │ Profile   │  │
                    │  └────────┘  │     │  │ (cookies) │  │
                    │              │     │  └───────────┘  │
                    │  ┌────────┐  │     └─────────────────┘
                    │  │Cookie  │  │
                    │  │Inject  │◀──── VNC Chrome login
                    │  └────────┘  │
                    └──────────────┘
```

---

## Development

```bash
npm install
npm run build
npm run dev
npm run check
```

---

## Credits

- **Original:** [PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp) — the foundation
- **OWL Bridge fork:** Mina Maged — cookie injection, VNC workflow, headless server support
- **Cookie extraction:** `browser_cookie3` library for bypassing CDP limitations

---

## Skills & Documentation

OWL Bridge includes a complete skill system for AI agents:

| Skill | Purpose |
|---|---|
| 🦉 [owl-bridge](skills/owl-bridge/SKILL.md) | Main MCP server guide — all tools, config, workflows |
| 🔑 [auth-fix](skills/auth-fix/SKILL.md) | Fix authentication — cookie extraction, Playwright format |
| 🖥️ [vnc-setup](skills/vnc-setup/SKILL.md) | VNC + Chrome setup for headless servers |
| 🐍 [python-client](skills/python-client/SKILL.md) | Use notebooklm Python client directly |
| 🔗 [integrations](skills/integrations/) | Claude Code, Cursor, Hermes, Codex, HTTP transport |

📚 **[Full Skill Registry](skills/SKILLS.md)** — problem → skill mapping, dependency pipeline, file paths.

---

## License

MIT. See [LICENSE](./LICENSE).
