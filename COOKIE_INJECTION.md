# 🦉 Cookie Injection Guide

> How to authenticate NotebookLM on a headless server where Google blocks automated login.

## Why This Exists

Google's anti-bot detection shows CAPTCHA challenges when it detects headless Chrome. The standard `setup_auth` flow can't solve these automatically. 

**The workaround:** Log in via a real browser displayed on VNC, extract the cookies, and inject them into the MCP server.

## Why CDP Doesn't Work

Chrome DevTools Protocol's `Network.getAllCookies` command returns **0 cookies** for HTTP-only and secure cookie contexts. This is a Chrome security feature, not a bug.

**Solution:** `browser_cookie3` reads Chrome's encrypted SQLite cookie database directly, bypassing CDP entirely.

## Step-by-Step

### 1. Set Up VNC (One-Time)

```bash
# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &

# Start VNC server
DISPLAY=:99 x11vnc -display :99 -forever -shared -rfbport 5900 -noxdamage &

# Start noVNC (browser-based client)
websockify --web /usr/share/novnc/ 6080 localhost:5900 &
```

### 2. Start Chrome on VNC Display

```bash
DISPLAY=:99 chromium --no-sandbox --disable-gpu \
  --no-first-run --no-default-browser-check \
  --user-data-dir=/root/.notebooklm/profiles/default/browser_profile \
  https://notebooklm.google.com
```

### 3. Log In via VNC

Open `http://YOUR_IP:6080/vnc.html` in your browser. You'll see the Chrome window. Log into Google normally.

### 4. Extract Cookies

```bash
pip install browser_cookie3

python3 scripts/extract_chrome_cookies.py \
  --chrome-profile /root/.notebooklm/profiles/default/browser_profile \
  --output ~/.local/share/notebooklm-mcp/browser_state/state.json
```

### 5. Verify

```bash
python3 scripts/extract_chrome_cookies.py \
  --state ~/.local/share/notebooklm-mcp/browser_state/state.json \
  --verify
```

Expected output:
```
✅ Valid! Found 8 cookies for .google.com
   Required: SID ✓ | __Secure-1PSIDTS ✓
```

### 6. Use

**Option A:** Restart MCP server (auto-loads state.json):
```bash
npx notebooklm-mcp
```

**Option B:** Inject without restart:
```
inject_cookies(state_path="~/.local/share/notebooklm-mcp/browser_state/state.json")
```

## Cookie Format

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
    }
  ]
}
```

## Required Cookies

| Cookie | Purpose |
|---|---|
| `SID` | Primary authentication token |
| `__Secure-1PSIDTS` | Timestamp-signed auth token |

## Troubleshooting

| Problem | Fix |
|---|---|
| `browser_cookie3` can't decrypt | Make sure Chrome is closed before extracting |
| `state.json` not found | Create the directory: `mkdir -p ~/.local/share/notebooklm-mcp/browser_state/` |
| Auth still fails after injection | Re-extract cookies — they may have expired |
| Chrome profile locked | Only one Chrome instance can use a profile at a time |
