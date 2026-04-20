#!/usr/bin/env bash
#
# One-time installer for the air-side methane telemetry on Raspberry Pi.
#
# Assumes the repo has been copied to the SD card (e.g. /home/pi/methane-visualization-analysis)
# and the Pi has NO network. All Python deps are installed from vendored wheels
# under vendor/wheels/. After this script runs successfully, the systemd service
# is enabled so every subsequent boot auto-starts the air transmitter.
#
# Usage:
#   sudo ./install_pi.sh
#
# Re-running is safe: the venv is reused, the service file is re-rendered, and
# the service is restarted to pick up any changes.

set -euo pipefail

# Resolve repo location from this script's path so install works regardless of cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ $EUID -ne 0 ]]; then
    echo "Error: install_pi.sh must be run as root. Try: sudo ./install_pi.sh" >&2
    exit 1
fi

REPO_DIR="$SCRIPT_DIR"
SERVICE_USER="${SUDO_USER:-pi}"
VENV_DIR="$REPO_DIR/.venv"
WHEEL_DIR="$REPO_DIR/vendor/wheels"
SERVICE_TEMPLATE="$REPO_DIR/services/air_tx.service"
SERVICE_DEST="/etc/systemd/system/air_tx.service"

# Sanity checks before touching anything.
if [[ ! -f "$REPO_DIR/air_tx_pi5.py" ]]; then
    echo "Error: air_tx_pi5.py not found in $REPO_DIR" >&2
    exit 1
fi
if [[ ! -d "$WHEEL_DIR" || -z "$(ls -A "$WHEEL_DIR" 2>/dev/null || true)" ]]; then
    echo "Error: no vendored wheels found in $WHEEL_DIR" >&2
    echo "Run 'pip download -r requirements-air.txt -d vendor/wheels --no-deps' on a workstation with network, then commit the wheels and re-copy the repo to the Pi." >&2
    exit 1
fi
if [[ ! -f "$SERVICE_TEMPLATE" ]]; then
    echo "Error: service template not found at $SERVICE_TEMPLATE" >&2
    exit 1
fi

# 1) Create the venv as the service user so ownership is correct from the start.
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtualenv at $VENV_DIR ..."
    sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR"
else
    echo "Reusing existing virtualenv at $VENV_DIR"
fi

# 2) Install deps from vendored wheels, fully offline.
echo "Installing Python dependencies from $WHEEL_DIR (offline) ..."
sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install \
    --quiet \
    --no-index \
    --find-links "$WHEEL_DIR" \
    -r "$REPO_DIR/requirements-air.txt"

# 3) Render the systemd unit template with the real repo path + service user.
# Uses bash string substitution (not sed) so paths containing &, \, or | do
# not need special escaping.
echo "Rendering systemd unit to $SERVICE_DEST ..."
template_content="$(<"$SERVICE_TEMPLATE")"
rendered="${template_content//@REPO_DIR@/$REPO_DIR}"
rendered="${rendered//@SERVICE_USER@/$SERVICE_USER}"
printf '%s' "$rendered" > "$SERVICE_DEST"
chmod 644 "$SERVICE_DEST"

# 4) Make sure run_air.sh is executable (git may not preserve the bit on some copy flows).
chmod +x "$REPO_DIR/run_air.sh"

# 5) Enable + start (or restart, if already running).
echo "Enabling and starting air_tx.service ..."
systemctl daemon-reload
systemctl enable air_tx.service >/dev/null
systemctl restart air_tx.service

echo ""
echo "Install complete. The air transmitter will now start automatically on every boot."
echo ""
echo "Check status:   systemctl status air_tx.service"
echo "Follow logs:    journalctl -u air_tx.service -f"
echo "Stop service:   sudo systemctl stop air_tx.service"
