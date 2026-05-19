#!/usr/bin/env python3
"""
Extract Google cookies from Chrome's encrypted SQLite database
and save them in Playwright storage format for notebooklm-mcp.

Usage:
    python3 scripts/extract_chrome_cookies.py [--output PATH] [--verify]
"""

import json
import argparse
import sys
from pathlib import Path

GOOGLE_DOMAINS = [
    '.google.com', 'accounts.google.com', 'notebooklm.google.com',
    'mail.google.com', 'myaccount.google.com', 'drive.google.com',
    '.youtube.com', 'www.google.com', '.google.com.eg',
    'ogs.google.com', 'studio.workspace.google.com',
    '.gemini.google.com', 'photos.google.com',
]

CHROME_DB_PATHS = [
    '/root/.notebooklm/profiles/default/browser_profile/Default/Cookies',
    '/root/.config/google-chrome/Default/Cookies',
    '/root/.config/chromium/Default/Cookies',
    str(Path.home() / '.config/google-chrome/Default/Cookies'),
    str(Path.home() / '.config/chromium/Default/Cookies'),
]

REQUIRED_COOKIES = ['SID', '__Secure-1PSIDTS']
RECOMMENDED_COOKIES = ['SID', 'HSID', 'SSID', 'APISID', 'SAPISID',
                       '__Secure-1PSID', '__Secure-3PSID',
                       '__Secure-1PSIDTS', '__Secure-3PSIDTS',
                       '__Secure-OSID', 'OSID', 'NID']


def find_chrome_db(custom_path=None):
    if custom_path:
        if Path(custom_path).exists():
            return custom_path
        print(f"Custom path not found: {custom_path}")
        sys.exit(1)
    for path in CHROME_DB_PATHS:
        if Path(path).exists():
            return path
    print("Chrome cookies database not found!")
    sys.exit(1)


def extract_cookies(chrome_db):
    try:
        import browser_cookie3
    except ImportError:
        print("browser_cookie3 not installed! Run: pip install browser_cookie3")
        sys.exit(1)

    all_cookies = []
    for domain in GOOGLE_DOMAINS:
        try:
            cj = browser_cookie3.chrome(cookie_file=chrome_db, domain_name=domain)
            for c in cj:
                all_cookies.append({
                    'name': c.name, 'value': c.value, 'domain': c.domain,
                    'path': getattr(c, 'path', '/'),
                    'secure': getattr(c, 'secure', True),
                    'httpOnly': getattr(c, 'httpOnly', False),
                })
        except Exception:
            pass

    seen = set()
    unique = []
    for c in all_cookies:
        key = (c['name'], c['domain'])
        if key not in seen and c['value']:
            seen.add(key)
            unique.append(c)
    return unique


def main():
    parser = argparse.ArgumentParser(description='Extract Google cookies from Chrome')
    parser.add_argument('--chrome-db', help='Path to Chrome cookies database')
    parser.add_argument('--output', '-o',
                        default='/root/.local/share/notebooklm-mcp/browser_state/state.json')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()

    chrome_db = find_chrome_db(args.chrome_db)
    print(f"Chrome DB: {chrome_db}")

    cookies = extract_cookies(chrome_db)
    if not cookies:
        print("No Google cookies found!")
        sys.exit(1)

    storage_state = {'cookies': cookies, 'origins': []}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(storage_state, f, indent=2)
    print(f"Saved {len(cookies)} cookies to {args.output}")

    # Verify
    names = {c['name'] for c in cookies}
    for name in REQUIRED_COOKIES:
        print(f"  {'OK' if name in names else 'MISSING'} {name} (required)")
    for name in RECOMMENDED_COOKIES:
        if name not in REQUIRED_COOKIES:
            print(f"  {'OK' if name in names else 'MISSING'} {name}")

    if not all(n in names for n in REQUIRED_COOKIES):
        print("WARNING: Some required cookies missing!")
        sys.exit(1)

    print("Done!")


if __name__ == '__main__':
    main()
