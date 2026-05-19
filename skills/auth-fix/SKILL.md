---
name: auth-fix
description: Fix NotebookLM authentication when Google blocks headless browser auto-login. Use when notebooklm-mcp or notebooklm-py fails with "Authentication expired" errors, missing cookies, or login challenges. Extracts fresh cookies from Chrome's encrypted SQLite database and saves them in Playwright storage format.
triggers:
  - notebooklm auth failed
  - notebooklm authentication expired
  - notebooklm login not working
  - notebooklm cookies expired
  - notebooklm-mcp auth error
  - notebooklm-py auth error
  - Failed to list notebooks
  - Could not add source
  - Missing required cookies
  - Google challenge page
---

# Auth Fix — NotebookLM Authentication Repair

## Problem

NotebookLM MCP server and `notebooklm-py` fail with "Authentication expired" errors because:

1. **Google blocks headless browsers** — Auto-login triggers CAPTCHA/verification challenges
2. **Stale cookies** — The `storage_state.json` / `state.json` file has expired cookies
3. **Chrome encryption** — Cookies are encrypted in SQLite and can't be read by the MCP server directly
4. **Wrong format** — Storage must be Playwright-style `{"cookies": [{"name": ..., "value": ..., "domain": ...}]}`, NOT a flat dict

## Solution

Extract fresh decrypted cookies from Chrome's SQLite database using `browser_cookie3` and save them in the correct Playwright storage format.

## Prerequisites

- `browser_cookie3` installed: `pip install browser_cookie3`
- Chrome/Chromium logged into Google (via VNC or any browser)
- Chrome cookies database at a standard location (see below)

## Quick Fix (Script)

The fastest way to fix auth — run the bundled extraction script:

```bash
# Auto-detect Chrome profile and extract cookies
python3 scripts/extract_chrome_cookies.py --verify

# Or specify a custom Chrome profile path
python3 scripts/extract_chrome_cookies.py \
  --chrome-profile /path/to/profile \
  --output /root/.local/share/notebooklm-mcp/browser_state/state.json \
  --verify
```

The script will:
1. Find Chrome's encrypted cookies database
2. Decrypt and extract all Google-domain cookies
3. Save them in Playwright format to the MCP server's state directory
4. Verify required cookies (`SID`, `__Secure-1PSIDTS`) are present
5. Optionally test auth by listing notebooks

## Manual Step-by-Step Fix

### 1. Find Chrome Cookies Database

```bash
find /root -path "*/Default/Cookies" -type f 2>/dev/null
```

Common locations:
- `/root/.notebooklm/profiles/default/browser_profile/Default/Cookies`
- `/root/.config/google-chrome/Default/Cookies`
- `/root/.config/chromium/Default/Cookies`

### 2. Extract & Save Fresh Cookies

```python
import browser_cookie3, json
from pathlib import Path

# === CONFIGURATION ===
COOKIE_DB = '/root/.notebooklm/profiles/default/browser_profile/Default/Cookies'
STORAGE_PATH = '/root/.notebooklm/profiles/default/storage_state.json'
# =====================

# Collect cookies from all Google domains
domains = [
    '.google.com', 'accounts.google.com', 'notebooklm.google.com',
    'mail.google.com', 'myaccount.google.com', 'drive.google.com',
    '.youtube.com', 'www.google.com', '.google.com.eg',
    'ogs.google.com', 'studio.workspace.google.com', 'contacts.google.com',
    '.gemini.google.com', 'photos.google.com',
]

all_cookies = []
for domain in domains:
    try:
        cj = browser_cookie3.chrome(cookie_file=COOKIE_DB, domain_name=domain)
        for c in cj:
            all_cookies.append({
                'name': c.name,
                'value': c.value,
                'domain': c.domain,
                'path': '/',
                'secure': True,
                'httpOnly': False
            })
    except Exception:
        pass

# Deduplicate by (name, domain)
seen = set()
unique = []
for c in all_cookies:
    key = (c['name'], c['domain'])
    if key not in seen and c['value']:
        seen.add(key)
        unique.append(c)

# Build Playwright storage state format (CRITICAL: must be {"cookies": [...]} NOT flat dict)
storage_state = {'cookies': unique, 'origins': []}

# Save
Path(STORAGE_PATH).parent.mkdir(parents=True, exist_ok=True)
with open(STORAGE_PATH, 'w') as f:
    json.dump(storage_state, f, indent=2)

print(f"✓ Saved {len(unique)} cookies to {STORAGE_PATH}")

# Verify key auth cookies
for name in ['SID', '__Secure-1PSIDTS', 'HSID', 'SSID', 'APISID', 'SAPISID']:
    found = any(c['name'] == name for c in unique)
    print(f"  {'✓' if found else '✗'} {name}")
```

### 3. Refresh MCP Auth

After saving the cookies, either:
- Call the MCP `refresh_auth` tool
- Restart the Hermes gateway to pick up the new storage state
- Use the `inject_cookies` tool (OWL Bridge fork only): `inject_cookies(state_path="/path/to/state.json")`

### 4. Verify It Works

```python
import asyncio
from notebooklm.client import NotebookLMClient

async def test():
    async with await NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        print(f"✓ Connected! Found {len(notebooks)} notebooks")
        for nb in notebooks:
            print(f"  - {nb.title}")

asyncio.run(test())
```

## Alternative: Direct Python Client (Bypass MCP)

If the MCP server keeps failing, use the Python client directly. **This is the recommended approach on headless VPS** since it avoids the MCP server's auth issues entirely.

### Complete Workflow (Python Client)

```python
import asyncio
from notebooklm.client import NotebookLMClient
from notebooklm.types import AudioFormat  # Import enums, not strings

async def main():
    async with await NotebookLMClient.from_storage() as client:
        # List notebooks
        notebooks = await client.notebooks.list()

        # Create notebook
        nb = await client.notebooks.create("My Research")

        # Add sources
        await client.sources.add_url(nb.id, "https://example.com/article")

        # Wait for processing
        await client.sources.wait_until_ready(nb.id)

        # Generate artifacts (all async — returns immediately with task_id)
        audio = await client.artifacts.generate_audio(nb.id, audio_format=AudioFormat.DEEP_DIVE)
        video = await client.artifacts.generate_video(nb.id)
        report = await client.artifacts.generate_report(nb.id)
        slides = await client.artifacts.generate_slide_deck(nb.id)
        mindmap = await client.artifacts.generate_mind_map(nb.id)

        # Poll for completion before downloading
        # Status: 1=in progress, 2=failed, 3=done
        for artifact_type, task_id in [('audio', audio.task_id), ('video', video.task_id)]:
            while True:
                status = await client.artifacts.poll_status(nb.id, task_id)
                if status.status == 3:  # done
                    break
                elif status.status == 2:  # failed
                    print(f"{artifact_type} failed: {status.error}")
                    break
                await asyncio.sleep(30)

        # Download completed artifacts
        await client.artifacts.download_audio(nb.id, '/tmp/audio.mp3')
        await client.artifacts.download_video(nb.id, '/tmp/video.mp4')
        await client.artifacts.download_report(nb.id, '/tmp/report.md')
        await client.artifacts.download_slide_deck(nb.id, '/tmp/slides.pdf')
        await client.artifacts.download_mind_map(nb.id, '/tmp/mindmap.json')

asyncio.run(main())
```

### Key Method Names

The Python client uses different method names than you might expect:
- `client.notebooks.list()` — NOT `list_notebooks()`
- `client.notebooks.create(title)` — NOT `new_notebook()`
- `client.sources.add_url(notebook_id, url)` — NOT `add_source()`
- `client.artifacts.generate_audio(notebook_id, audio_format=AudioFormat.DEEP_DIVE)` — use enum, NOT string
- `client.artifacts.poll_status(notebook_id, task_id)` — check generation status
- `client.artifacts.wait_for_completion(notebook_id, task_id, timeout=120)` — blocking wait

### MCP Tool `inject_cookies` (OWL Bridge Fork Only)

The OWL Bridge fork (Minamaged18/owl-bridge-notebooklm) adds an `inject_cookies` MCP tool that accepts a path to a Playwright-format state.json file. This avoids restarting the MCP server:

```
inject_cookies(state_path="/root/.local/share/notebooklm-mcp/browser_state/state.json")
```

GitHub: https://github.com/Minamaged18/owl-bridge-notebooklm

**Note**: The MCP `studio_status` tool may fail even when auth works — use `client.artifacts.list()` via the Python client instead.

## Key Learnings

1. **Cookie Format Matters**: The storage file MUST be `{"cookies": [{"name": ..., "value": ..., "domain": ...}]}` — a flat dict `{name: value}` will fail validation
2. **Required Cookies**: Google requires at minimum `SID` and `__Secure-1PSIDTS` for authentication
3. **Chrome Encryption**: Chrome encrypts cookies in SQLite. `browser_cookie3` handles decryption automatically (uses keyring or falls back to "peanuts" password)
4. **CDP Doesn't Work**: Chrome DevTools Protocol `Network.getAllCookies` returns 0 cookies for HTTP-only/secure cookies — use `browser_cookie3` instead
5. **VNC Login**: The most reliable way to get fresh cookies is to log into Google via a VNC-displayed Chrome browser, then extract cookies with `browser_cookie3`
6. **MCP Auth Expires Fast**: Google sessions expire quickly. The MCP server's `refresh_auth` tool reads from disk but the cookies may already be stale. Always extract fresh cookies from the browser.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Missing required cookies: SID, __Secure-1PSIDTS` | Re-extract cookies from Chrome after logging in |
| `Authentication expired` | Cookies are stale, extract fresh ones |
| `browser_cookie3` not installed | `pip install browser_cookie3` |
| Chrome profile not found | Check `find /root -path "*/Default/Cookies"` |
| `Flood control exceeded` on Telegram | Wait between sending large files |
| Audio/Video generation fails | These are async — poll status and download when `status=3` |
| `ArtifactParseError` on download | Wait longer for artifact to finish processing |
| `client.artifacts.get()` hangs | Use `download_report()` directly instead of `get()` then download |
| `studio_status` MCP tool fails | Auth may still work — use Python client `artifacts.list()` instead |
| `generate_audio()` with string format | Use `AudioFormat.DEEP_DIVE` enum, not `'deep_dive'` string |
| `AttributeError: 'str' object has no attribute 'value'` | Wrong type passed to generate_audio — use AudioFormat enum |
| MCP `refresh_auth` doesn't help | The state.json itself has stale cookies — extract fresh from Chrome |
| `is_connected()` is not callable | It's a property: `client.is_connected` (no parentheses) |

## File Paths Reference

| File | Path |
|------|------|
| Chrome cookies DB | `/root/.notebooklm/profiles/default/browser_profile/Default/Cookies` |
| Storage state (notebooklm-py) | `/root/.notebooklm/profiles/default/storage_state.json` |
| MCP state (notebooklm-mcp) | `/root/.local/share/notebooklm-mcp/browser_state/state.json` |
| Chrome profile | `/root/.notebooklm/profiles/default/browser_profile/` |
| This skill | `/root/notebooklm-mcp/skills/auth-fix/` |
| Cookie extraction script | `/root/notebooklm-mcp/skills/auth-fix/scripts/extract_chrome_cookies.py` |
| Cookie format reference | `/root/notebooklm-mcp/skills/auth-fix/references/cookie-format.md` |
