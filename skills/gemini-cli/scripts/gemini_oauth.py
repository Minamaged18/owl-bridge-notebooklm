#!/usr/bin/env python3
"""
🦉 OWL Bridge — Gemini CLI OAuth Helper

Automates the OAuth flow for Gemini CLI on headless servers:
1. Starts Gemini CLI with NO_BROWSER=true
2. Extracts the OAuth URL from stdout
3. Navigates VNC Chrome to the URL via CDP
4. Auto-clicks through account chooser and consent screens
5. Extracts the authorization code from the callback URL
6. Pastes the code back into Gemini CLI

Usage:
    python3 gemini_oauth.py                    # Full automated flow
    python3 gemini_oauth.py --cdp-port 9222    # Custom CDP port
    python3 gemini_oauth.py --no-vnc           # Print URL only (manual flow)
"""

import subprocess
import sys
import os
import time
import json
import argparse
import urllib.request
from urllib.parse import urlparse, parse_qs

def get_cdp_targets(port=9222):
    """Get Chrome DevTools Protocol targets."""
    try:
        resp = urllib.request.urlopen(f"http://localhost:{port}/json/list", timeout=5)
        return json.loads(resp.read())
    except Exception as e:
        print(f"❌ Cannot connect to Chrome CDP on port {port}: {e}")
        print("   Make sure Chrome is running with --remote-debugging-port=9222")
        sys.exit(1)

def navigate_and_get_code(ws_url, oauth_url, timeout=120):
    """Navigate Chrome to OAuth URL and extract authorization code."""
    try:
        import websocket
    except ImportError:
        print("❌ websocket-client not installed. Run: pip install websocket-client")
        sys.exit(1)
    
    ws = websocket.create_connection(ws_url, timeout=timeout)
    
    # Navigate to OAuth URL
    ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": oauth_url}}))
    ws.recv()
    print("  → Navigated Chrome to OAuth URL")
    
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        
        # Check current URL
        ws.send(json.dumps({
            "id": int(time.time()),
            "method": "Runtime.evaluate",
            "params": {"expression": "window.location.href"}
        }))
        url = json.loads(ws.recv())['result']['result']['value']
        
        # Check for callback URL with code
        if 'codeassist.google.com/authcode' in url:
            code = parse_qs(urlparse(url).query).get('code', [''])[0]
            ws.close()
            return code
        
        # Auto-click account/consent buttons
        ws.send(json.dumps({
            "id": int(time.time()) + 100,
            "method": "Runtime.evaluate",
            "params": {"expression": """
                var clicked = false;
                var els = document.querySelectorAll('[data-identifier], .JO6PIb, button, [role=button], a, [role=link]');
                els.forEach(function(el) {
                    var t = el.textContent.toLowerCase();
                    if (t.includes('sign in') || t.includes('continue') || t.includes('allow') || 
                        t.includes('approve') || t.includes('mina') || t.includes('minamagedo22')) {
                        el.click();
                        clicked = true;
                    }
                });
                clicked ? 'clicked' : '';
            """}
        }))
        result = json.loads(ws.recv())
        if result.get('result', {}).get('result', {}).get('value') == 'clicked':
            print("  → Auto-clicked button")
    
    ws.close()
    return None

def main():
    parser = argparse.ArgumentParser(description="🦉 Gemini CLI OAuth Helper")
    parser.add_argument("--cdp-port", type=int, default=9222, help="Chrome CDP port")
    parser.add_argument("--no-vnc", action="store_true", help="Print URL only (manual flow)")
    parser.add_argument("--timeout", type=int, default=120, help="OAuth flow timeout (seconds)")
    args = parser.parse_args()
    
    print("🦉 Gemini CLI OAuth Helper")
    print("=" * 40)
    
    if args.no_vnc:
        # Manual flow: just print the URL
        print("\nStarting Gemini CLI (manual mode)...")
        proc = subprocess.Popen(
            ["gemini"],
            env={**os.environ, "NO_BROWSER": "true"},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Read output until we get the URL
        url_line = None
        for line in proc.stdout:
            line = line.strip()
            print(f"  {line}")
            if "accounts.google.com/o/oauth2" in line:
                url_line = line
                break
        
        if url_line:
            print(f"\n📋 Open this URL in your browser:")
            print(f"   {url_line}")
            print(f"\nThen paste the authorization code back into the terminal.")
        
        proc.wait()
        return
    
    # Automated flow with VNC
    print(f"\n1. Checking Chrome CDP on port {args.cdp_port}...")
    targets = get_cdp_targets(args.cdp_port)
    page_target = next((t for t in targets if t['type'] == 'page'), None)
    if not page_target:
        print("   ❌ No page target found in Chrome")
        sys.exit(1)
    print(f"   ✓ Found page: {page_target.get('url', '')[:60]}")
    
    print("\n2. Starting Gemini CLI...")
    proc = subprocess.Popen(
        ["gemini"],
        env={**os.environ, "NO_BROWSER": "true"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Read output until we get the OAuth URL
    oauth_url = None
    stdout = proc.stdout
    if stdout is None:
        print("   ❌ Failed to read Gemini CLI output")
        proc.kill()
        sys.exit(1)
    
    for line in stdout:
        line = line.strip()
        print(f"  {line}")
        if "accounts.google.com/o/oauth2" in line:
            oauth_url = line
            break
    
    if not oauth_url:
        print("   ❌ Failed to get OAuth URL from Gemini CLI")
        proc.kill()
        sys.exit(1)
    
    print(f"\n3. Navigating Chrome to OAuth URL...")
    code = navigate_and_get_code(page_target['webSocketDebuggerUrl'], oauth_url, args.timeout)
    
    if not code:
        print("   ❌ Failed to get authorization code (timeout)")
        proc.kill()
        sys.exit(1)
    
    print(f"\n4. Got authorization code: {code[:20]}...")
    
    # Send code to Gemini CLI
    stdin = proc.stdin
    if stdin is not None:
        stdin.write(code + "\n")
        stdin.flush()
        print("   ✓ Pasted code into Gemini CLI")
    else:
        print("   ❌ Cannot write to Gemini CLI stdin")
        proc.kill()
        sys.exit(1)
    
    print("\n5. Waiting for authentication to complete...")
    # Read remaining output
    if stdout is not None:
        for line in stdout:
            line = line.strip()
            if line:
                print(f"  {line}")
            if "Signed in" in line or "Authenticated" in line or "Plan:" in line:
                print("\n✅ Authentication successful!")
                break
    
    print("\nGemini CLI is ready to use!")
    print("  Interactive: gemini")
    print("  Non-interactive: gemini -p \"your prompt\"")
    
    proc.wait()

if __name__ == "__main__":
    main()
