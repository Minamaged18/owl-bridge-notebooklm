---
name: owl-bridge
description: 🦉 OWL Bridge — Next-gen MCP server for Google NotebookLM with cookie injection, VNC + headless server support, and stealth Chrome automation. Use this skill when the user wants to interact with Google NotebookLM via MCP, authenticate on headless servers, inject cookies, manage notebooks, ask questions, generate audio overviews, or configure the OWL Bridge server.
triggers:
  - notebooklm
  - owl bridge
  - cookie injection
  - headless notebooklm
  - vnc notebooklm
  - notebooklm mcp
  - inject cookies
  - notebooklm authentication
  - notebooklm headless
  - notebooklm server
---

# 🦉 OWL Bridge — NotebookLM MCP

> **The only NotebookLM MCP server that works on headless servers.**
> Cookie injection · VNC workflow · Stealth Chrome · Multi-account

A fork of [PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp) with critical fixes for headless VPS environments where Google's auto-login gets blocked by CAPTCHA.

## What Makes OWL Bridge Different

| Feature | Original | OWL Bridge |
|---|---|---|
| Headless server support | ❌ CAPTCHA blocks login | ✅ Cookie injection via VNC |
| `inject_cookies` tool | ❌ Not available | ✅ Inject without restart |
| Chrome cookie extraction | ❌ Not included | ✅ Built-in script |
| VNC workflow docs | ❌ Not documented | ✅ Full guide |
| CDP cookie bypass | ❌ Not addressed | ✅ `browser_cookie3` approach |

---

## Installation

### From npm (recommended)

```bash
npx notebooklm-mcp@latest
```

### From source

```bash
git clone https://github.com/Minamaged18/notebooklm-mcp.git
cd notebooklm-mcp
npm install
npm run build
npm run dev
```

### Global install

```bash
npm install -g notebooklm-mcp
notebooklm-mcp
```

The package ships two CLI binaries: `notebooklm-mcp` and `owl-bridge-notebooklm` (both identical).

**Requirements:** Node.js ≥ 18, Chrome or Chromium browser.

---

## Quick Start

### Desktop (interactive login)

```bash
npx notebooklm-mcp@latest
```

Then call `setup_auth` from your MCP client to open a visible Chrome window and log in.

### Headless Server + VNC (cookie injection)

```bash
# Step 1: Set up VNC (one-time)
Xvfb :99 -screen 0 1920x1080x24 &
DISPLAY=:99 x11vnc -display :99 -forever -shared -rfbport 5900 &
websockify --web /usr/share/novnc/ 6080 localhost:5900 &

# Step 2: Log in via VNC browser, then extract cookies
pip install browser_cookie3
python3 scripts/extract_chrome_cookies.py \
  --output ~/.local/share/notebooklm-mcp/browser_state/state.json

# Step 3: Start MCP server — authenticated!
npx notebooklm-mcp
```

---

## Authentication

### Method 1: Interactive Login (Desktop)

Call `setup_auth` → opens visible Chrome → log in once → cookies persisted to disk.

### Method 2: Cookie Injection (Headless Server) ✨

```
VNC Chrome login → extract_chrome_cookies.py → inject_cookies tool → done
```

The `inject_cookies` tool accepts a path to a Playwright-format `state.json` and loads it into the active browser session **without restarting** the MCP server.

**Why CDP doesn't work:** Chrome's `Network.getAllCookies` returns 0 cookies for HTTP-only/secure contexts. OWL Bridge uses `browser_cookie3` which reads Chrome's encrypted SQLite cookie database directly.

### Method 3: Auto-login via Env Vars

Set `LOGIN_EMAIL` and `LOGIN_PASSWORD` (or `GOOGLE_EMAIL` / `GOOGLE_PASSWORD`). The server attempts automated login on first run. Works on desktop; may trigger CAPTCHA on headless servers.

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

### Profile Locations

| Platform | Chrome Profile | Data Dir |
|---|---|---|
| Linux | `~/.local/share/notebooklm-mcp/chrome_profile/` | `~/.local/share/notebooklm-mcp/` |
| macOS | `~/Library/Application Support/notebooklm-mcp/chrome_profile/` | `~/Library/Application Support/notebooklm-mcp/` |
| Windows | `%APPDATA%\notebooklm-mcp\chrome_profile\` | `%APPDATA%\notebooklm-mcp\` |

---

## Tools Reference

### Q&A

| Tool | Purpose |
|---|---|
| `ask_question` | Ask a question against a notebook. Supports session reuse, citation extraction (`source_format: none/inline/footnotes/json`), and per-call browser overrides. |

### Sources & Studio

| Tool | Purpose |
|---|---|
| `add_source` | Add a source (`type: url` or `type: text`) to a notebook. |
| `generate_audio` | Generate a podcast-style Audio Overview. |
| `download_audio` | Save the most recent Audio Overview to disk. |

### Library Management

| Tool | Purpose |
|---|---|
| `add_notebook` | Add a NotebookLM share-URL to the local library. |
| `list_notebooks` | List every notebook in the library. |
| `get_notebook` | Fetch one notebook by ID. |
| `select_notebook` | Set a notebook as the active default. |
| `update_notebook` | Update notebook metadata. |
| `remove_notebook` | Remove from the local library (does not delete in NotebookLM). |
| `search_notebooks` | Search by name, description, topics, tags. |
| `get_library_stats` | Counts and usage stats. |

### Sessions

| Tool | Purpose |
|---|---|
| `list_sessions` | List active browser sessions. |
| `close_session` | Close one session. |
| `reset_session` | Clear chat history, keep session ID. |

### System

| Tool | Purpose |
|---|---|
| `get_health` | Auth state, session count, configuration snapshot. |
| `setup_auth` | First-time interactive Google login. |
| `re_auth` | Wipe auth + log in again. |
| `cleanup_data` | Categorised preview + delete of stored data. |
| `inject_cookies` | **✨ OWL Bridge exclusive** — Inject cookies from a state.json file without restarting. |

### Read-Only Resources (MCP URIs)

| URI | Purpose |
|---|---|
| `notebooklm://library` | JSON view of the full library. |
| `notebooklm://library/{id}` | One notebook by ID. |

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
      LOGIN_EMAIL: "your-email@gmail.com"
      LOGIN_PASSWORD: "your-password"
```

### HTTP Transport (n8n, Zapier, hosted agents)

```bash
npx notebooklm-mcp@latest --transport http --port 3000 --host 0.0.0.0
```

---

## Multi-Account Support

```bash
npx notebooklm-mcp@latest --account work
npx notebooklm-mcp@latest --account personal
```

Each account gets its own Chrome profile, cookies, and auth state under `<dataDir>/accounts/<slug>/`.

---

## Configuration Reference

Resolution order (highest wins): per-call tool params → environment variables → built-in defaults.

### Browser

| Env Var | Default | Purpose |
|---|---|---|
| `HEADLESS` | `true` | Run Chrome headless. |
| `BROWSER_TIMEOUT` | `30000` | Per-action browser timeout (ms). |
| `ANSWER_TIMEOUT_MS` | `600000` | Hard ceiling on answer wait (ms). |
| `BROWSER_CHANNEL` | `chrome` | `chrome` or `chromium`. |

### Stealth

| Env Var | Default | Purpose |
|---|---|---|
| `STEALTH_ENABLED` | `true` | Master switch for human-like behaviour. |
| `STEALTH_RANDOM_DELAYS` | `true` | Random delays between actions. |
| `STEALTH_HUMAN_TYPING` | `true` | Human-like keystroke timing. |
| `STEALTH_MOUSE_MOVEMENTS` | `true` | Realistic mouse motion before click. |
| `TYPING_WPM_MIN` | `160` | Minimum typing speed. |
| `TYPING_WPM_MAX` | `240` | Maximum typing speed. |
| `MIN_DELAY_MS` | `100` | Minimum action delay (ms). |
| `MAX_DELAY_MS` | `400` | Maximum action delay (ms). |

### Sessions

| Env Var | Default | Purpose |
|---|---|---|
| `MAX_SESSIONS` | `10` | Concurrent browser sessions. |
| `SESSION_TIMEOUT` | `900` | Idle seconds before GC. |

### Authentication (auto-login, opt-in)

| Env Var | Default | Purpose |
|---|---|---|
| `AUTO_LOGIN_ENABLED` | `false` | Enable scripted login. |
| `LOGIN_EMAIL` | _(unset)_ | Google email for auto-login. |
| `LOGIN_PASSWORD` | _(unset)_ | Google password for auto-login. |
| `AUTO_LOGIN_TIMEOUT_MS` | `120000` | Auto-login attempt ceiling (ms). |

### Transports

| Env Var | Default | Purpose |
|---|---|---|
| `NOTEBOOKLM_TRANSPORT` | `stdio` | `stdio` or `http`. |
| `NOTEBOOKLM_PORT` | `3000` | HTTP port. |
| `NOTEBOOKLM_HOST` | `127.0.0.1` | HTTP bind address. |

### Multi-Account & Profiles

| Env Var | Default | Purpose |
|---|---|---|
| `NOTEBOOKLM_ACCOUNT` | _(unset)_ | Multi-account profile slug. |
| `NOTEBOOKLM_PROFILE` | `full` | `minimal`, `standard`, or `full`. |
| `NOTEBOOKLM_DISABLED_TOOLS` | _(unset)_ | CSV of tool names to suppress. |
| `NOTEBOOK_PROFILE_STRATEGY` | `auto` | `auto`, `single`, or `isolated`. |

### Provenance

| Env Var | Default | Purpose |
|---|---|---|
| `NOTEBOOKLM_AI_MARKER` | `true` | Prefix answers with AI-generated marker. |
| `NOTEBOOKLM_AI_MARKER_PREFIX` | _(default text)_ | Override the prefix string. |

### CLI Flags

| Flag | Purpose |
|---|---|
| `--transport <stdio\|http>` | Pick transport. |
| `--port <number>` | HTTP port. |
| `--host <addr>` | HTTP bind address. |
| `--account <slug>` / `-a <slug>` | Multi-account profile. |
| `config get / set / reset` | Manage `settings.json`. |

Full configuration docs: [`docs/configuration.md`](./docs/configuration.md)

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `setup_auth` shows CAPTCHA | Google anti-bot on headless | Use VNC + cookie injection |
| `Network.getAllCookies` returns 0 | HTTP-only/secure cookies | Use `browser_cookie3` instead |
| `state.json` validation error | Wrong format | Must be `{"cookies": [{"name":..., "value":..., "domain":...}]}` |
| Auth expires after days | Google cookie rotation | Re-extract cookies from VNC Chrome |
| Chrome won't launch on VPS | Missing system deps | Install Chrome dependencies (atk, gtk3, etc.) |
| Chrome profile locked | Two instances using same profile | Close other Chrome instances first |

Full troubleshooting: [`docs/troubleshooting.md`](./docs/troubleshooting.md)

---

## Other Skills in This Directory

The `skills/` directory contains additional OWL Bridge skills:

- **`skills/cookie-injection/`** — Detailed guide for the VNC cookie injection workflow.
- **`skills/headless-setup/`** — Step-by-step headless server setup.
- **`skills/notebook-management/`** — Managing the local notebook library.

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
npm run build      # Compile TypeScript
npm run dev        # Watch mode with tsx
npm run check      # Lint + format + build
npm run lint       # ESLint only
npm run format     # Prettier only
```

---

## Credits

- **Original:** [PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp) — the foundation
- **OWL Bridge fork:** Mina Maged — cookie injection, VNC workflow, headless server support
- **Cookie extraction:** `browser_cookie3` library for bypassing CDP limitations

## License

MIT. See [LICENSE](./LICENSE).
