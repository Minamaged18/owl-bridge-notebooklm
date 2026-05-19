# 📚 OWL Bridge — Skill Registry

> Complete index of all skills in the OWL Bridge project.
> Use this file to quickly find the right skill for your task.

---

## Directory Tree

```
skills/
├── SKILLS.md                          ← You are here (this file)
├── owl-bridge/
│   └── SKILL.md                      — Main OWL Bridge MCP server guide
├── auth-fix/
│   ├── SKILL.md                      — Authentication repair guide
│   ├── references/
│   │   └── cookie-format.md          — Cookie format specification
│   └── scripts/
│       └── extract_chrome_cookies.py — Chrome cookie extraction tool
├── vnc-setup/
│   ├── SKILL.md                      — VNC + virtual display setup
│   ├── references/
│   │   └── chrome-deps.md            — Chrome dependency reference
│   └── scripts/
│       └── setup_vnc.sh              — Automated VNC setup script
├── python-client/
│   ├── SKILL.md                      — Python client (bypass MCP server)
│   └── scripts/
│       └── notebooklm_quickstart.py  — Complete working example
└── integrations/
    ├── claude-code.md                — Claude Code integration
    ├── cursor.md                     — Cursor IDE integration
    ├── hermes-agent.md               — Hermes Agent integration
    ├── codex.md                      — OpenAI Codex CLI integration
    └── http-transport.md             — HTTP transport (n8n, Zapier, Make)
```

---

## Skill Overview

| # | Skill | Purpose | Location |
|---|-------|---------|----------|
| 1 | **owl-bridge** 🦉 | Main MCP server — install, configure, use all tools | [`owl-bridge/SKILL.md`](./owl-bridge/SKILL.md) |
| 2 | **auth-fix** 🔑 | Fix auth failures — cookie extraction, Playwright format | [`auth-fix/SKILL.md`](./auth-fix/SKILL.md) |
| 3 | **vnc-setup** 🖥️ | Virtual display + VNC + Chrome for headless servers | [`vnc-setup/SKILL.md`](./vnc-setup/SKILL.md) |
| 4 | **python-client** 🐍 | Use notebooklm Python client directly (bypass MCP) | [`python-client/SKILL.md`](./python-client/SKILL.md) |
| 5 | **integrations** 🔗 | Connect to Claude, Cursor, Hermes, Codex, HTTP clients | [`integrations/`](./integrations/) |

---

## Skill Descriptions

### 1. 🦉 owl-bridge — Main MCP Server

**When to use:** Any interaction with Google NotebookLM via MCP. Installing, configuring, or troubleshooting the OWL Bridge server.

**What it does:**
- Install and configure the OWL Bridge MCP server
- Authenticate via interactive login, cookie injection, or env vars
- Manage notebooks (add, list, get, select, update, remove, search)
- Ask questions with citation extraction
- Add sources and generate audio overviews
- Multi-account, stealth Chrome, HTTP transport, session management

**Key tools:** `ask_question`, `add_source`, `generate_audio`, `download_audio`, `inject_cookies` (exclusive), `setup_auth`, `re_auth`, `get_health`, + 10 more

---

### 2. 🔑 auth-fix — Authentication Repair

**When to use:** Auth failures, expired cookies, CAPTCHA blocks, "Failed to list notebooks", "Could not add source".

**What it does:**
- Extracts fresh decrypted cookies from Chrome's encrypted SQLite database
- Saves cookies in correct Playwright storage format
- Provides both automated script and manual step-by-step instructions
- Includes complete Python client workflow to bypass MCP server
- Covers the `inject_cookies` tool (OWL Bridge exclusive)

**Key files:**
- `scripts/extract_chrome_cookies.py` — Auto cookie extraction with `--verify`
- `references/cookie-format.md` — Cookie format specification

---

### 3. 🖥️ vnc-setup — Virtual Display & VNC

**When to use:** Setting up NotebookLM on a headless Linux server. Google CAPTCHA blocks automated login.

**What it does:**
- Installs Xvfb + x11vnc + websockify/noVNC + Chrome
- Auto-detects distro (Fedora/RHEL/Ubuntu/Debian/Arch)
- Provides both automated script and manual instructions
- Troubleshooting for Chrome, noVNC, display, and CAPTCHA issues

**Architecture:**
```
Xvfb (virtual display :99)
  └─ x11vnc (VNC server on :5900)
       └─ websockify → noVNC (WebSocket proxy on :6080)
            └─ Chrome (renders into :99, accessible via browser)
```

**Key files:**
- `scripts/setup_vnc.sh` — One-command VNC setup
- `references/chrome-deps.md` — Chrome dependencies per distro

---

### 4. 🐍 python-client — Python Client (Bypass MCP)

**When to use:** When MCP server keeps failing, need direct Python access, building automation, or running on headless VPS.

**What it does:**
- Complete `notebooklm` Python client workflow
- Create notebooks, add sources, generate all 8 artifact types
- Polling pattern for async artifact generation
- Side-by-side comparison: MCP tool names vs Python client methods

**Artifact types:** audio, video, report, slide_deck, mind_map, flashcards, quiz, data_table

**Key files:**
- `scripts/notebooklm_quickstart.py` — Complete working example (200 lines)

---

### 5. 🔗 integrations — AI Client Integration Guides

**When to use:** Connecting OWL Bridge to a specific AI client.

| Client | File | Transport |
|---|---|---|
| Claude Code | [`claude-code.md`](./integrations/claude-code.md) | stdio |
| Cursor IDE | [`cursor.md`](./integrations/cursor.md) | stdio |
| Hermes Agent | [`hermes-agent.md`](./integrations/hermes-agent.md) | stdio |
| OpenAI Codex | [`codex.md`](./integrations/codex.md) | stdio |
| n8n/Zapier/Make | [`http-transport.md`](./integrations/http-transport.md) | HTTP |

---

## Skill Dependencies

The skills form a **pipeline** for headless server authentication:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  vnc-setup  │ ──▶ │  auth-fix   │ ──▶ │  owl-bridge │
│             │     │             │     │             │
│ Set up      │     │ Extract     │     │ Use MCP     │
│ virtual     │     │ cookies     │     │ server      │
│ display +   │     │ from VNC    │     │ with        │
│ VNC +       │     │ Chrome      │     │ injected    │
│ Chrome      │     │             │     │ cookies     │
└─────────────┘     └─────────────┘     └─────────────┘
     Step 1              Step 2              Step 3
```

**Typical workflow on a headless VPS:**
1. **vnc-setup** — Create virtual display, start VNC, launch Chrome
2. Log into Google via VNC Chrome (solve CAPTCHA manually)
3. **auth-fix** — Extract cookies from Chrome's SQLite database
4. **owl-bridge** — Inject cookies and use NotebookLM

> **Desktop users:** Skip `vnc-setup`. Use `setup_auth` for interactive login.

**Alternative path (Python client):**
```
vnc-setup → auth-fix → python-client
```
Use the Python client directly when the MCP server is problematic.

---

## Quick Reference: Problem → Skill

| Problem | Use This Skill |
|---|---|
| "Authentication expired" / "auth failed" | [auth-fix](./auth-fix/SKILL.md) |
| "Missing required cookies: SID, __Secure-1PSIDTS" | [auth-fix](./auth-fix/SKILL.md) |
| Google CAPTCHA blocks login | [vnc-setup](./vnc-setup/SKILL.md) → [auth-fix](./auth-fix/SKILL.md) |
| Need to install/configure OWL Bridge | [owl-bridge](./owl-bridge/SKILL.md) |
| "How do I inject cookies without restarting?" | [owl-bridge](./owl-bridge/SKILL.md) (`inject_cookies`) |
| "state.json validation error" | [auth-fix](./auth-fix/SKILL.md) (cookie format) |
| "Chrome won't launch on VPS" | [vnc-setup](./vnc-setup/SKILL.md) (Chrome deps) |
| "noVNC not loading" / "blank screen" | [vnc-setup](./vnc-setup/SKILL.md) |
| "How do I use NotebookLM on a headless server?" | [vnc-setup](./vnc-setup/SKILL.md) → [auth-fix](./auth-fix/SKILL.md) → [owl-bridge](./owl-bridge/SKILL.md) |
| "MCP server keeps failing" | [python-client](./python-client/SKILL.md) |
| "How do I generate audio/video/reports?" | [owl-bridge](./owl-bridge/SKILL.md) or [python-client](./python-client/SKILL.md) |
| "Connect to Claude Code" | [integrations/claude-code.md](./integrations/claude-code.md) |
| "Connect to Cursor" | [integrations/cursor.md](./integrations/cursor.md) |
| "Connect to Hermes Agent" | [integrations/hermes-agent.md](./integrations/hermes-agent.md) |
| "Connect to n8n/Zapier" | [integrations/http-transport.md](./integrations/http-transport.md) |
| "studio_status MCP tool fails" | [auth-fix](./auth-fix/SKILL.md) (use Python client) |
| "Audio/Video generation fails" | [python-client](./python-client/SKILL.md) (polling pattern) |

---

## File Paths Reference

| File | Path |
|------|------|
| This registry | `skills/SKILLS.md` |
| OWL Bridge skill | `skills/owl-bridge/SKILL.md` |
| Auth fix skill | `skills/auth-fix/SKILL.md` |
| Cookie extraction script | `skills/auth-fix/scripts/extract_chrome_cookies.py` |
| Cookie format reference | `skills/auth-fix/references/cookie-format.md` |
| VNC setup skill | `skills/vnc-setup/SKILL.md` |
| VNC setup script | `skills/vnc-setup/scripts/setup_vnc.sh` |
| Chrome deps reference | `skills/vnc-setup/references/chrome-deps.md` |
| Python client skill | `skills/python-client/SKILL.md` |
| Python quickstart script | `skills/python-client/scripts/notebooklm_quickstart.py` |
| Integration guides | `skills/integrations/` |
| Chrome cookies DB | `~/.config/google-chrome/Default/Cookies` |
| Storage state (notebooklm-py) | `~/.notebooklm/profiles/default/storage_state.json` |
| MCP state (notebooklm-mcp) | `~/.local/share/notebooklm-mcp/browser_state/state.json` |

---

*🦉 OWL Bridge — The only NotebookLM MCP that works on headless servers.*
*Last updated: 2026-05-19*
