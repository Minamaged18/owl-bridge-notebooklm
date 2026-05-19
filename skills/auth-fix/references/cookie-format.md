# Playwright Cookie Storage Format Reference

## Overview

The NotebookLM MCP server (`notebooklm-mcp`) and Python client (`notebooklm-py`) both use Playwright's storage state format for persisting authentication cookies. This reference describes the exact format required.

## Correct Format

The storage state file (`state.json` or `storage_state.json`) MUST be a JSON object with a `"cookies"` array:

```json
{
  "cookies": [
    {
      "name": "SID",
      "value": "g.a000...",
      "domain": ".google.com",
      "path": "/",
      "expires": 1735689600,
      "httpOnly": false,
      "secure": true,
      "sameSite": "Lax"
    },
    {
      "name": "__Secure-1PSIDTS",
      "value": "g.a000...",
      "domain": ".google.com",
      "path": "/",
      "expires": 1735689600,
      "httpOnly": true,
      "secure": true,
      "sameSite": "None"
    }
  ],
  "origins": []
}
```

## Common Mistake: Flat Dict

A flat dictionary format will **fail validation**:

```json
// ❌ WRONG — will not work
{
  "SID": "g.a000...",
  "__Secure-1PSIDTS": "g.a000..."
}
```

## Cookie Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Cookie name (e.g., `"SID"`) |
| `value` | string | ✅ | Cookie value |
| `domain` | string | ✅ | Domain scope (e.g., `".google.com"`) |
| `path` | string | ✅ | URL path scope (usually `"/"`) |
| `expires` | number | ❌ | Unix timestamp (omit for session cookies) |
| `httpOnly` | boolean | ❌ | HTTP-only flag (default: `false`) |
| `secure` | boolean | ❌ | Secure flag (default: `false`) |
| `sameSite` | string | ❌ | SameSite policy: `"Strict"`, `"Lax"`, or `"None"` |

## Required Cookies for Google Auth

Minimum cookies needed for NotebookLM authentication:

| Cookie | Purpose |
|--------|---------|
| `SID` | Google session ID |
| `__Secure-1PSIDTS` | Secure session token |

Recommended full set for robust auth:

| Cookie | Purpose |
|--------|---------|
| `SID` | Google session ID |
| `HSID` | Hashed session ID |
| `SSID` | Secure session ID |
| `APISID` | API auth |
| `SAPISID` | Secure API auth |
| `__Secure-1PSID` | Secure session variant |
| `__Secure-3PSID` | Secure session variant |
| `__Secure-1PSIDTS` | Secure token |
| `__Secure-3PSIDTS` | Secure token |
| `__Secure-OSID` | Origin-specific ID (NotebookLM) |
| `OSID` | Origin-specific ID |
| `NID` | Google preferences |

## File Locations

| Consumer | Default Path |
|----------|-------------|
| `notebooklm-mcp` | `~/.local/share/notebooklm-mcp/browser_state/state.json` |
| `notebooklm-py` | `~/.notebooklm/profiles/default/storage_state.json` |

## Generating from Chrome

Use `browser_cookie3` to extract from Chrome's encrypted SQLite database:

```python
import browser_cookie3

cj = browser_cookie3.chrome(
    cookie_file="/path/to/Default/Cookies",
    domain_name=".google.com"
)

cookies = []
for c in cj:
    cookies.append({
        "name": c.name,
        "value": c.value,
        "domain": c.domain,
        "path": c.path,
        "httpOnly": c.has_nonstandard_attr("httponly"),
        "secure": c.secure,
        "sameSite": "Lax"
    })

storage_state = {"cookies": cookies, "origins": []}
```

## Why Not CDP?

Chrome DevTools Protocol's `Network.getAllCookies` returns **0 cookies** for HTTP-only/secure contexts due to browser security isolation. Reading the SQLite database directly via `browser_cookie3` bypasses this limitation.

## References

- [Playwright Storage State Documentation](https://playwright.dev/docs/api/class-browsercontext#browser-context-storage-state)
- [browser_cookie3 GitHub](https://github.com/borisbabic/browser_cookie3)
- [OWL Bridge Fork (inject_cookies tool)](https://github.com/Minamaged18/owl-bridge-notebooklm)
