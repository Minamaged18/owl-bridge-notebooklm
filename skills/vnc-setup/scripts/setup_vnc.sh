#!/usr/bin/env bash
# setup_vnc.sh — Install and start Xvfb + x11vnc + websockify + Chrome
# for NotebookLM Google authentication via VNC.
#
# Usage:
#   chmod +x setup_vnc.sh
#   bash setup_vnc.sh
#
# Environment variables (optional):
#   DISPLAY_NUM   — X display number (default: :1)
#   RESOLUTION    — Screen resolution (default: 1920x1080x24)
#   VNC_PORT      — x11vnc port (default: 5901)
#   NOVNC_PORT    — noVNC port (default: 6080)
#   CHROME_BIN    — Path to Chrome/Chromium binary (auto-detected)

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────

DISPLAY_NUM="${DISPLAY_NUM:-:1}"
RESOLUTION="${RESOLUTION:-1920x1080x24}"
VNC_PORT="${VNC_PORT:-5901}"
NOVNC_PORT="${NOVNC_PORT:-6080}"
NOVNC_WEB_DIR=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${CYAN}[STEP]${NC}  $*"; }

# ── Detect Distro ─────────────────────────────────────────────────────────────

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "${ID}"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

# ── Detect Chrome Binary ──────────────────────────────────────────────────────

detect_chrome() {
    local candidates=(
        "google-chrome-stable"
        "google-chrome"
        "chromium-browser"
        "chromium"
        "/usr/bin/google-chrome-stable"
        "/usr/bin/google-chrome"
        "/usr/bin/chromium-browser"
        "/usr/bin/chromium"
        "/usr/lib/chromium/chromium"
    )
    for candidate in "${candidates[@]}"; do
        if command -v "$candidate" &>/dev/null; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# ── Detect noVNC Web Directory ────────────────────────────────────────────────

detect_novnc_web() {
    local candidates=(
        "/usr/share/novnc"
        "/usr/share/novnc/"
        "/opt/novnc"
        "/opt/novnc/"
    )
    for dir in "${candidates[@]}"; do
        if [ -f "${dir}/vnc.html" ]; then
            echo "$dir"
            return 0
        fi
    done
    # Try to find it
    local found
    found=$(find / -name "vnc.html" -path "*/novnc/*" 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        dirname "$found"
        return 0
    fi
    return 1
}

# ── Install Dependencies ──────────────────────────────────────────────────────

install_deps() {
    local distro="$1"
    log_step "Installing dependencies for: ${distro}"

    case "$distro" in
        fedora|rhel|centos|rocky|alma|ol)
            log_info "Using dnf/yum package manager"
            local PKG_MGR="dnf"
            command -v dnf &>/dev/null || PKG_MGR="yum"

            sudo "$PKG_MGR" install -y \
                xorg-x11-server-Xvfb \
                x11vnc \
                novnc \
                websockify \
                chromium \
                || {
                    log_error "Package installation failed. See references/chrome-deps.md for manual steps."
                    exit 1
                }
            ;;

        ubuntu|debian|linuxmint|pop)
            log_info "Using apt package manager"
            sudo apt-get update -qq
            sudo apt-get install -y \
                xvfb \
                x11vnc \
                novnc \
                websockify \
                chromium-browser \
                || {
                    log_error "Package installation failed. See references/chrome-deps.md for manual steps."
                    exit 1
                }
            ;;

        arch|manjaro)
            log_info "Using pacman package manager"
            sudo pacman -S --noconfirm \
                xorg-server-xvfb \
                x11vnc \
                novnc \
                python-websockify \
                chromium \
                || {
                    log_error "Package installation failed. See references/chrome-deps.md for manual steps."
                    exit 1
                }
            ;;

        *)
            log_warn "Unknown distribution: ${distro}"
            log_warn "Please install manually: Xvfb, x11vnc, novnc, websockify, chromium"
            log_warn "See references/chrome-deps.md for details"
            read -rp "Continue anyway? [y/N] " response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac

    log_info "Dependencies installed successfully"
}

# ── Kill Existing Processes ───────────────────────────────────────────────────

kill_existing() {
    log_step "Stopping any existing VNC services..."

    local pids
    pids=$(pgrep -f "Xvfb ${DISPLAY_NUM}" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill 2>/dev/null || true
        log_info "Stopped existing Xvfb on ${DISPLAY_NUM}"
    fi

    pids=$(pgrep -f "x11vnc.*${VNC_PORT}" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill 2>/dev/null || true
        log_info "Stopped existing x11vnc on port ${VNC_PORT}"
    fi

    pids=$(pgrep -f "websockify.*${NOVNC_PORT}" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill 2>/dev/null || true
        log_info "Stopped existing websockify on port ${NOVNC_PORT}"
    fi

    # Wait for ports to be freed
    sleep 1
}

# ── Start Xvfb ────────────────────────────────────────────────────────────────

start_xvfb() {
    log_step "Starting Xvfb on display ${DISPLAY_NUM} (${RESOLUTION})..."

    if pgrep -f "Xvfb ${DISPLAY_NUM}" &>/dev/null; then
        log_warn "Xvfb already running on ${DISPLAY_NUM}, skipping"
        return 0
    fi

    Xvfb "$DISPLAY_NUM" -screen 0 "$RESOLUTION" -ac +extension GLX +render -noreset &
    sleep 2

    if pgrep -f "Xvfb ${DISPLAY_NUM}" &>/dev/null; then
        log_info "Xvfb started successfully (PID: $(pgrep -f "Xvfb ${DISPLAY_NUM}" | head -1))"
    else
        log_error "Xvfb failed to start"
        exit 1
    fi
}

# ── Start x11vnc ──────────────────────────────────────────────────────────────

start_x11vnc() {
    log_step "Starting x11vnc on port ${VNC_PORT}..."

    if pgrep -f "x11vnc.*${VNC_PORT}" &>/dev/null; then
        log_warn "x11vnc already running on port ${VNC_PORT}, skipping"
        return 0
    fi

    x11vnc -display "$DISPLAY_NUM" \
        -forever \
        -shared \
        -rfbport "$VNC_PORT" \
        -nopw \
        -noxdamage \
        -xkb \
        2>/dev/null &

    sleep 2

    if pgrep -f "x11vnc.*${VNC_PORT}" &>/dev/null; then
        log_info "x11vnc started successfully on port ${VNC_PORT}"
    else
        log_error "x11vnc failed to start"
        log_error "Check if port ${VNC_PORT} is in use: ss -tlnp | grep ${VNC_PORT}"
        exit 1
    fi
}

# ── Start noVNC (websockify) ──────────────────────────────────────────────────

start_novnc() {
    log_step "Starting noVNC (websockify) on port ${NOVNC_PORT}..."

    if pgrep -f "websockify.*${NOVNC_PORT}" &>/dev/null; then
        log_warn "websockify already running on port ${NOVNC_PORT}, skipping"
        return 0
    fi

    if [ -z "$NOVNC_WEB_DIR" ]; then
        log_error "Cannot find noVNC web files (vnc.html)"
        log_error "Install novnc package or set NOVNC_WEB_DIR manually"
        exit 1
    fi

    websockify \
        --web "$NOVNC_WEB_DIR" \
        "$NOVNC_PORT" \
        "localhost:${VNC_PORT}" \
        2>/dev/null &

    sleep 2

    if pgrep -f "websockify.*${NOVNC_PORT}" &>/dev/null; then
        log_info "noVNC started successfully on port ${NOVNC_PORT}"
    else
        log_error "websockify failed to start"
        exit 1
    fi
}

# ── Start Chrome ──────────────────────────────────────────────────────────────

start_chrome() {
    log_step "Starting Chrome on display ${DISPLAY_NUM}..."

    local chrome_bin
    chrome_bin="${CHROME_BIN:-$(detect_chrome)}"

    if [ -z "$chrome_bin" ]; then
        log_error "Chrome/Chromium not found!"
        log_error "Install it or set CHROME_BIN environment variable"
        exit 1
    fi

    log_info "Using Chrome binary: ${chrome_bin}"

    # Check if Chrome is already running on this display
    if pgrep -f "chromium.*no-sandbox" &>/dev/null || pgrep -f "chrome.*no-sandbox" &>/dev/null; then
        log_warn "Chrome already running, skipping"
        return 0
    fi

    DISPLAY="$DISPLAY_NUM" "$chrome_bin" \
        --no-sandbox \
        --disable-gpu \
        --disable-dev-shm-usage \
        --disable-software-rasterizer \
        --window-size=1920,1080 \
        --start-maximized \
        --remote-debugging-port=9222 \
        2>/dev/null &

    sleep 3

    if pgrep -f "chrom" &>/dev/null; then
        log_info "Chrome started successfully"
    else
        log_error "Chrome failed to start"
        log_error "Try running manually: DISPLAY=${DISPLAY_NUM} ${chrome_bin} --no-sandbox --disable-gpu"
        exit 1
    fi
}

# ── Print Summary ─────────────────────────────────────────────────────────────

print_summary() {
    local server_ip
    server_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "YOUR_SERVER_IP")

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  VNC Setup Complete!"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "  Display:       ${DISPLAY_NUM}"
    echo "  Resolution:    ${RESOLUTION}"
    echo "  VNC Port:      ${VNC_PORT}"
    echo "  noVNC Port:    ${NOVNC_PORT}"
    echo "  Chrome Debug:  9222"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────┐"
    echo "  │  Open noVNC in your browser:                            │"
    echo "  │                                                         │"
    echo "  │  http://${server_ip}:${NOVNC_PORT}/vnc.html              │"
    echo "  │                                                         │"
    echo "  └─────────────────────────────────────────────────────────┘"
    echo ""
    echo "  Next steps:"
    echo "  1. Open the noVNC URL above in your browser"
    echo "  2. Click 'Connect'"
    echo "  3. Log into Google in the VNC Chrome window"
    echo "  4. Extract cookies for notebooklm-mcp"
    echo ""
    echo "  To stop all services:"
    echo "    pkill -f 'Xvfb ${DISPLAY_NUM}'; pkill -f x11vnc;"
    echo "    pkill -f 'websockify.*${NOVNC_PORT}'; pkill -f chromium"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  VNC + Chrome Setup for NotebookLM Authentication            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    # Detect distro
    local distro
    distro=$(detect_distro)
    log_info "Detected distribution: ${distro}"

    # Detect Chrome
    CHROME_BIN="${CHROME_BIN:-$(detect_chrome || true)}"
    if [ -n "${CHROME_BIN:-}" ]; then
        log_info "Found Chrome binary: ${CHROME_BIN}"
    else
        log_warn "Chrome binary not found yet — will install"
    fi

    # Detect noVNC web directory
    NOVNC_WEB_DIR=$(detect_novnc_web || true)
    if [ -n "$NOVNC_WEB_DIR" ]; then
        log_info "Found noVNC web files: ${NOVNC_WEB_DIR}"
    fi

    # Install dependencies
    install_deps "$distro"

    # Re-detect Chrome and noVNC after install
    CHROME_BIN="${CHROME_BIN:-$(detect_chrome)}"
    NOVNC_WEB_DIR="${NOVNC_WEB_DIR:-$(detect_novnc_web)}"

    # Kill existing processes
    kill_existing

    # Start services
    start_xvfb
    start_x11vnc
    start_novnc
    start_chrome

    # Print summary
    print_summary
}

main "$@"
