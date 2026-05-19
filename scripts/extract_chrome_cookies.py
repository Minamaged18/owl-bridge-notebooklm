#!/usr/bin/env python3
"""
🦉 OWL Bridge — Chrome Cookie Extractor for NotebookLM

Extracts Google authentication cookies from Chrome's encrypted SQLite database
and converts them to Playwright storage state format.

Why not CDP? Chrome's Network.getAllCookies returns 0 cookies for HTTP-only/
secure contexts. This script reads the SQLite DB directly via browser_cookie3.

Usage:
    python3 extract_chrome_cookies.py --output state.json
    python3 extract_chrome_cookies.py --chrome-profile /path/to/profile --output state.json
    python3 extract_chrome_cookies.py --state state.json --verify
"""

import json
import sys
import os
import argparse
from pathlib import Path

def get_chrome_cookie_db_path(custom_profile=None):
    """Get the path to Chrome's Cookies SQLite database."""
    if custom_profile:
        db_path = Path(custom_profile) / "Default" / "Cookies"
        if db_path.exists():
            return str(db_path)
        # Try without Default subdirectory
        db_path = Path(custom_profile) / "Cookies"
        if db_path.exists():
            return str(db_path)
    
    home = Path.home()
    candidates = [
        home / ".config" / "google-chrome" / "Default" / "Cookies",
        home / ".config" / "google-chrome-beta" / "Default" / "Cookies",
        home / ".config" / "chromium" / "Default" / "Cookies",
        home / "snap" / "chromium" / "current" / ".config" / "chromium" / "Default" / "Cookies",
        home / ".cache" / "ms-playwright" / "chromium-1217" / "chrome-linux64" / "Default" / "Cookies",
        home / ".cache" / "ms-playwright" / "chromium-1223" / "chrome-linux64" / "Default" / "Cookies",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    
    return None

def extract_cookies(db_path, domain=".google.com"):
    """Extract cookies from Chrome's SQLite database."""
    try:
        import browser_cookie3
    except ImportError:
        print("❌ browser_cookie3 not installed. Run: pip install browser_cookie3")
        sys.exit(1)
    
    try:
        # Determine browser type from path
        db_str = str(db_path).lower()
        if "chrome" in db_str and "chromium" not in db_str:
            cookies = browser_cookie3.chrome(
                cookie_file=db_path,
                domain_name=domain
            )
        else:
            cookies = browser_cookie3.chromium(
                cookie_file=db_path,
                domain_name=domain
            )
        
        result = []
        for cookie in cookies:
            result.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "httpOnly": cookie.has_nonstandard_attr("httponly") or cookie.name.startswith("__Secure"),
                "secure": cookie.secure,
                "sameSite": "Lax"
            })
        
        return result
    
    except Exception as e:
        print(f"❌ Error extracting cookies: {e}")
        print("   Make sure Chrome is fully closed before extracting.")
        sys.exit(1)

def to_playwright_format(cookies):
    """Convert to Playwright storage state format."""
    return {"cookies": cookies}

def verify_state(state_path):
    """Verify a state.json file has the required cookies."""
    with open(state_path) as f:
        data = json.load(f)
    
    cookies = data.get("cookies", [])
    domains = set(c.get("domain", "") for c in cookies)
    names = set(c.get("name", "") for c in cookies)
    
    print(f"📋 Found {len(cookies)} cookies across {len(domains)} domains")
    
    for domain in sorted(domains):
        domain_cookies = [c for c in cookies if c.get("domain") == domain]
        print(f"   {domain}: {len(domain_cookies)} cookies")
        for c in domain_cookies:
            value_preview = c.get("value", "")[:20] + "..." if len(c.get("value", "")) > 20 else c.get("value", "")
            print(f"     - {c['name']} = {value_preview}")
    
    # Check required cookies
    has_sid = "SID" in names
    has_psidts = "__Secure-1PSIDTS" in names
    
    print()
    if has_sid and has_psidts:
        print("✅ Valid! Has required authentication cookies")
        print(f"   Required: SID {'✓' if has_sid else '✗'} | __Secure-1PSIDTS {'✓' if has_psidts else '✗'}")
        return True
    else:
        print("⚠️  Missing required cookies!")
        print(f"   Required: SID {'✓' if has_sid else '✗'} | __Secure-1PSIDTS {'✓' if has_psidts else '✗'}")
        print("   You may need to log into Google again via VNC.")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="🦉 OWL Bridge — Extract Chrome cookies for NotebookLM auth",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--chrome-profile",
        help="Path to Chrome profile directory (auto-detected if not specified)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path for state.json"
    )
    parser.add_argument(
        "--state", "-s",
        help="Verify an existing state.json file"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify mode (use with --state)"
    )
    parser.add_argument(
        "--domain",
        default=".google.com",
        help="Cookie domain to extract (default: .google.com)"
    )
    
    args = parser.parse_args()
    
    # Verify mode
    if args.verify or args.state:
        state_path = args.state or args.output
        if not state_path:
            print("❌ Specify --state <path> to verify")
            sys.exit(1)
        verify_state(state_path)
        return
    
    # Extract mode
    db_path = get_chrome_cookie_db_path(args.chrome_profile)
    
    if not db_path:
        print("❌ Chrome cookie database not found!")
        print("   Searched standard locations. Use --chrome-profile to specify custom path.")
        sys.exit(1)
    
    print(f"🔍 Reading cookies from: {db_path}")
    
    cookies = extract_cookies(db_path, args.domain)
    
    if not cookies:
        print(f"❌ No cookies found for domain: {args.domain}")
        print("   Make sure you're logged into Google in Chrome.")
        sys.exit(1)
    
    print(f"✅ Extracted {len(cookies)} cookies for {args.domain}")
    
    state = to_playwright_format(cookies)
    
    # Determine output path
    output_path = args.output
    if not output_path:
        # Default to MCP server's browser_state directory
        home = Path.home()
        default_dir = home / ".local" / "share" / "notebooklm-mcp" / "browser_state"
        default_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(default_dir / "state.json")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(state, f, indent=2)
    
    print(f"💾 Saved to: {output_path}")
    print()
    print("Next steps:")
    print(f"  1. Verify: python3 {sys.argv[0]} --state {output_path} --verify")
    print(f"  2. Start MCP server: npx notebooklm-mcp")
    print(f"  3. Or inject via tool: inject_cookies(state_path=\"{output_path}\")")

if __name__ == "__main__":
    main()
