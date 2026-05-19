# Chrome Dependencies by Distribution

Chrome/Chromium requires several system libraries to run under Xvfb. This document covers distro-specific dependency details for headless VNC setups.

## Fedora / RHEL / CentOS / Rocky / AlmaLinux

### Install Chrome

**Option 1: Chromium from official repos (recommended)**

```bash
sudo dnf install -y chromium
```

**Option 2: Google Chrome (official)**

```bash
# Add Google Chrome repo
sudo tee /etc/yum.repos.d/google-chrome.repo << 'EOF'
[google-chrome]
name=Google Chrome
baseurl=https://dl.google.com/linux/chrome/rpm/stable/x86_64
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub
EOF

sudo dnf install -y google-chrome-stable
```

### Required Libraries

```bash
sudo dnf install -y \
    xorg-x11-server-Xvfb \
    xorg-x11-xauth \
    xorg-x11-fonts-Type1 \
    xorg-x11-fonts-misc \
    libX11 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXfixes \
    libXi \
    libXrandr \
    libXrender \
    libXtst \
    libXScrnSaver \
    gtk3 \
    nss \
    nspr \
    alsa-lib \
    cups-libs \
    dbus-libs \
    atk \
    at-spi2-atk \
    pango \
    cairo \
    gdk-pixbuf2 \
    libnotify \
    liberation-fonts \
    dejavu-sans-fonts \
    dejavu-serif-fonts
```

### Common Issues on Fedora/RHEL

| Issue | Fix |
|---|---|
| `error while loading shared libraries: libnss3.so` | `sudo dnf install -y nss` |
| `Gtk: cannot open display` | Ensure Xvfb is running and `DISPLAY` is set |
| `FATAL:devshm` | Add `--disable-dev-shm-usage` to Chrome flags |
| Missing fonts / garbled text | Install `liberation-fonts` and `dejavu-sans-fonts` |
| `sandbox: 0` error | Add `--no-sandbox` flag (required for root) |
| SELinux blocking Chrome | `sudo setenforce 0` (temporary) or configure SELinux policy |

## Ubuntu / Debian / Linux Mint / Pop!_OS

### Install Chrome

**Option 1: Chromium from official repos (recommended)**

```bash
sudo apt-get update
sudo apt-get install -y chromium-browser
```

On newer Ubuntu versions (22.04+), Chromium may be a snap package. For VNC use, prefer the deb version:

```bash
# Remove snap version if present
sudo snap remove chromium

# Install via official Chromium PPA or download .deb
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f  # Fix any dependency issues
```

**Option 2: Google Chrome (official)**

```bash
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | \
    sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable
```

### Required Libraries

```bash
sudo apt-get install -y \
    xvfb \
    xauth \
    x11vnc \
    novnc \
    websockify \
    libx11-6 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    libxss1 \
    libgtk-3-0 \
    libnss3 \
    libnspr4 \
    libasound2 \
    libcups2 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libnotify4 \
    fonts-liberation \
    fonts-dejavu \
    xfonts-base \
    xfonts-100dpi \
    xfonts-75dpi \
    xfonts-scalable
```

### Common Issues on Ubuntu/Debian

| Issue | Fix |
|---|---|
| `error while loading shared libraries: libnss3.so` | `sudo apt-get install -y libnss3` |
| `chromium-browser` not found (snap only) | Use Google Chrome .deb or install Chromium from PPA |
| `Gtk: cannot open display` | Ensure Xvfb is running and `DISPLAY` is set |
| `FATAL:devshm` | Add `--disable-dev-shm-usage` to Chrome flags |
| Missing fonts / garbled text | Install `fonts-liberation` and `fonts-dejavu` |
| `dpkg: dependency problems` | Run `sudo apt-get install -f` after `.deb` install |
| Snap Chromium won't work with Xvnc | Snap confinement blocks X11 access; use `.deb` instead |

## Arch Linux / Manjaro

### Install Chrome

```bash
# Chromium from official repos
sudo pacman -S --noconfirm chromium

# Or Google Chrome from AUR
yay -S --noconfirm google-chrome
```

### Required Libraries

```bash
sudo pacman -S --noconfirm \
    xorg-server-xvfb \
    xorg-xauth \
    x11vnc \
    novnc \
    python-websockify \
    libx11 \
    libxcomposite \
    libxcursor \
    libxdamage \
    libxext \
    libxfixes \
    libxi \
    libxrandr \
    libxrender \
    libxtst \
    libxss \
    gtk3 \
    nss \
    nspr \
    alsa-lib \
    libcups \
    dbus \
    atk \
    at-spi2-atk \
    pango \
    cairo \
    gdk-pixbuf2 \
    libnotify \
    ttf-liberation \
    ttf-dejavu \
    xorg-fonts-type1 \
    xorg-fonts-misc
```

## Alpine Linux (Docker)

Alpine uses musl libc and requires additional compatibility layers:

```bash
apk add --no-cache \
    chromium \
    chromium-chromedriver \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    libstdc++ \
    harfbuzz \
    nss \
    nspr \
    alsa-lib \
    cups-libs \
    dbus-libs \
    gtk+3.0 \
    ttf-freefont \
    font-noto
```

> **Note:** Alpine's Chromium may have rendering differences. For NotebookLM auth, Fedora/Ubuntu/Debian are recommended.

## Verifying Chrome Works

After installing dependencies, verify Chrome can start on the virtual display:

```bash
# Start Xvfb
Xvfb :1 -screen 0 1920x1080x24 &
export DISPLAY=:1

# Test Chrome launch
chromium --no-sandbox --disable-gpu --disable-dev-shm-usage \
    --headless --dump-dom https://example.com 2>&1 | head -20

# If that works, try with a window (requires Xvfb running)
chromium --no-sandbox --disable-gpu --disable-dev-shm-usage \
    --window-size=1920,1080 &
sleep 3
DISPLAY=:1 xdotool search --name "example" 2>/dev/null && echo "Chrome is rendering!" || echo "Chrome window not found"
```

## Minimal Docker Setup

For Docker environments, here's a minimal setup:

```dockerfile
FROM fedora:40

RUN dnf install -y \
    xorg-x11-server-Xvfb \
    x11vnc \
    novnc \
    websockify \
    chromium \
    && dnf clean all

COPY skills/vnc-setup/scripts/setup_vnc.sh /usr/local/bin/setup_vnc.sh
RUN chmod +x /usr/local/bin/setup_vnc.sh

EXPOSE 6080 5901

CMD ["setup_vnc.sh"]
```

Run with:

```bash
docker build -t notebooklm-vnc .
docker run -d -p 6080:6080 -p 5901:5901 --shm-size=2g notebooklm-vnc
```

> **Important:** Use `--shm-size=2g` to avoid Chrome crashes in Docker (the default 64MB `/dev/shm` is too small).
