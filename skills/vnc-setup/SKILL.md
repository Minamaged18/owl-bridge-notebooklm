# VNC Setup for NotebookLM Authentication

Set up a virtual display with VNC + Chrome on a headless Linux server so you can complete Google's CAPTCHA challenges and authenticate with NotebookLM.

## Why VNC Is Required

Google's login flow for NotebookLM presents CAPTCHA challenges (especially on headless servers with no real display). Automated headless Chrome is detected and blocked. The solution is a **virtual framebuffer** that Chrome renders into, accessed via **VNC** through a browser.

**Architecture:**

```
Xvfb (virtual display :1)
  └─ x11vnc (VNC server on :5901)
       └─ websockify → noVNC (WebSocket proxy on :6080)
            └─ Chrome (renders into :1, accessible via browser at http://IP:6080/vnc.html)
```

## Quick Start

```bash
# 1. Run the setup script (auto-detects distro)
bash scripts/setup_vnc.sh

# 2. Open noVNC in your browser
# http://<SERVER_IP>:6080/vnc.html

# 3. Log into Google in the VNC Chrome window

# 4. Extract cookies for notebooklm-mcp
# (see "Extracting Cookies" below)
```

## Step-by-Step Setup

### 1. Install Dependencies

**Fedora / RHEL / CentOS:**

```bash
sudo dnf install -y xorg-x11-server-Xvfb x11vnc novnc websockify chromium
```

**Ubuntu / Debian:**

```bash
sudo apt-get update
sudo apt-get install -y xvfb x11vnc novnc websockify chromium-browser
```

> See `references/chrome-deps.md` for distro-specific dependency details and troubleshooting.

### 2. Start the Virtual Display (Xvfb)

```bash
# Start Xvfb on display :1, 1920x1080, 24-bit color
Xvfb :1 -screen 0 1920x1080x24 &
export DISPLAY=:1
```

### 3. Start the VNC Server (x11vnc)

```bash
# Attach x11vnc to display :1 (VNC port 5901)
x11vnc -display :1 -forever -shared -rfbport 5901 -nopw &
```

- `-forever`: Keep running after client disconnects
- `-shared`: Allow multiple simultaneous viewers
- `-nopw`: No password (use only on trusted networks; see Security note below)

### 4. Start noVNC (websockify)

```bash
# Proxy VNC port 5901 → WebSocket on port 6080
websockify --web /usr/share/novnc/ 6080 localhost:5901 &
```

### 5. Launch Chrome

```bash
# Launch Chrome on the virtual display
DISPLAY=:1 chromium --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --window-size=1920,1080 --start-maximized &
```

> **Important flags:**
> - `--no-sandbox`: Required when running as root
> - `--disable-gpu`: Avoids GPU-related crashes on headless servers
> - `--disable-dev-shm-usage`: Prevents crashes in Docker/low-shm environments

### 6. Access noVNC

Open your browser and navigate to:

```
http://<SERVER_IP>:6080/vnc.html
```

Click **Connect**. You should see the Chrome window rendered on the virtual display.

### 7. Log Into Google

1. In the VNC Chrome window, navigate to `https://accounts.google.com`
2. Complete the full login flow (email → password → 2FA → CAPTCHA if prompted)
3. Once logged in, verify by visiting `https://notebooklm.google.com`

### 8. Extract Cookies After Login

After successful Google login, extract the authentication cookies for use with `notebooklm-mcp`:

```bash
# Using the notebooklm-mcp cookie extraction script
cd /root/notebooklm-mcp
node dist/extract-cookies.js

# Or manually with Chrome DevTools Protocol:
# 1. Find Chrome's remote debugging port (add --remote-debugging-port=9222 to Chrome flags)
# 2. Query cookies via CDP:
curl -s http://localhost:9222/json | jq '.[0].webSocketDebuggerUrl'
# Then use a CDP client to call Network.getAllCookies
```

The key cookies needed are:
- `SID`, `HSID`, `SSID`, `APISID`, `SAPISID` — Google session cookies
- `__Secure-3PSID` — Secure session cookie

## Using the Setup Script

The `scripts/setup_vnc.sh` script automates all steps above:

```bash
# Make executable and run
chmod +x scripts/setup_vnc.sh
bash scripts/setup_vnc.sh
```

The script will:
1. Detect your Linux distribution (Fedora/RHEL or Ubuntu/Debian)
2. Install required packages
3. Start Xvfb on display `:1`
4. Start x11vnc on port `5901`
5. Start websockify/noVNC on port `6080`
6. Launch Chrome on the virtual display
7. Print the noVNC access URL

## Stopping the Services

```bash
# Kill all components
pkill -f "Xvfb :1"
pkill -f "x11vnc"
pkill -f "websockify.*6080"
pkill -f "chromium.*no-sandbox"

# Or kill by port
fuser -k 5901/tcp  # x11vnc
fuser -k 6080/tcp  # noVNC
```

## Troubleshooting

### Chrome Won't Start

| Symptom | Cause | Fix |
|---|---|---|
| `Gtk: cannot open display` | Xvfb not running or wrong DISPLAY | `export DISPLAY=:1` and verify Xvfb is running |
| `FATAL:devshm` | `/dev/shm` too small (Docker) | Add `--disable-dev-shm-usage` to Chrome flags |
| `ERROR:gpu_process_transport_factory` | No GPU on headless server | Add `--disable-gpu` to Chrome flags |
| `Running as root without --no-sandbox` | Chrome sandbox requires non-root | Add `--no-sandbox` to Chrome flags |
| Chrome crashes immediately | Missing shared libraries | See `references/chrome-deps.md` |

### noVNC Not Loading

| Symptom | Cause | Fix |
|---|---|---|
| `Connection refused` on port 6080 | websockify not running | Start websockify: `websockify --web /usr/share/novnc/ 6080 localhost:5901 &` |
| Blank screen after connect | x11vnc not attached to correct display | Verify `DISPLAY=:1` matches Xvnc's display |
| `403 Forbidden` | websockify can't reach x11vnc | Check x11vnc is listening: `ss -tlnp \| grep 5901` |
| Page not found at `/vnc.html` | noVNC files not installed | Install `novnc` package; find path: `find / -name vnc.html 2>/dev/null` |

### Display / Rendering Issues

| Symptom | Cause | Fix |
|---|---|---|
| Black screen in noVNC | Nothing rendering on Xvfb | Verify Chrome is running: `DISPLAY=:1 xdotool search --name Chrome` |
| Low resolution | Default Xvfb screen size too small | Restart Xvfb with `-screen 0 1920x1080x24` |
| Color banding / artifacts | Insufficient color depth | Use `24` or `32` for color depth in Xvfb flags |
| Mouse/keyboard not working in noVNC | Browser WebSocket issue | Try a different browser; check browser console for errors |

### Google CAPTCHA Still Appears

- Complete the CAPTCHA manually in the VNC Chrome window
- Google may require additional verification on first login from a new IP
- If CAPTCHA persists, try logging into a less-sensitive Google service first (e.g., Gmail) to "warm up" the session

### Ports Already in Use

```bash
# Check what's using a port
ss -tlnp | grep -E '5901|6080'

# Kill existing processes on those ports
fuser -k 5901/tcp 6080/tcp
```

## Security Considerations

- **`-nopw` on x11vnc** means anyone with network access can control the display. Use only on trusted networks or behind a firewall.
- For production use, set a VNC password: replace `-nopw` with `-passwd YOUR_PASSWORD`
- Restrict noVNC access with firewall rules:
  ```bash
  sudo firewall-cmd --add-port=6080/tcp --permanent  # Allow noVNC
  sudo firewall-cmd --remove-port=5901/tcp --permanent  # Block direct VNC
  sudo firewall-cmd --reload
  ```
- Consider SSH tunneling instead of exposing port 6080:
  ```bash
  ssh -L 6080:localhost:6080 user@server
  # Then access http://localhost:6080/vnc.html locally
  ```

## Environment Variables

The setup script uses these variables (override as needed):

| Variable | Default | Description |
|---|---|---|
| `DISPLAY_NUM` | `:1` | X display number |
| `RESOLUTION` | `1920x1080x24` | Screen resolution and color depth |
| `VNC_PORT` | `5901` | x11vnc listening port |
| `NOVNC_PORT` | `6080` | noVNC/websockify listening port |
| `CHROME_BIN` | auto-detected | Path to Chrome/Chromium binary |

Example with custom settings:

```bash
RESOLUTION=2560x1440x24 VNC_PORT=5902 NOVNC_PORT=6081 bash scripts/setup_vnc.sh
```

## See Also

- `references/chrome-deps.md` — Chrome dependencies for different distros
- `scripts/setup_vnc.sh` — Automated setup script
- Project `README.md` — Full notebooklm-mcp documentation
- `COOKIE_INJECTION.md` — Cookie extraction and injection details
