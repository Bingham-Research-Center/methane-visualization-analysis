#!/usr/bin/env bash
#
# Ground-side viewer launcher for Linux and macOS.
#
# Bootstraps a .venv-ground virtualenv on first run, installs the ground-side
# dependencies quietly, then launches the live matplotlib viewer. Subsequent
# runs reuse the existing venv and exit pip quickly if nothing has changed.
#
# Usage:
#   ./run_ground.sh                    # defaults PORT to /dev/ttyUSB0
#   ./run_ground.sh /dev/tty.usb-XYZ   # explicit port
#   ./run_ground.sh --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat <<'EOF'
Usage: ./run_ground.sh [PORT]

Launches the ground-side telemetry viewer. PORT defaults to /dev/ttyUSB0.

Supported environment variables (all optional, with defaults):
  GROUNDBAUD          Serial baud rate                             [57600]
  GROUNDMIRROR        Mirror CSV path           [ground_methane_log.csv]
  GROUNDWINDOWS       Plot window width in seconds                   [300]
  GROUNDFLUSHSEC      CSV flush interval in seconds                  [1.0]
  METHANEVAL_MIN      Minimum accepted methane value                   [0]
  METHANEVAL_MAX      Maximum accepted methane value               [10000]

Example:
  GROUNDWINDOWS=120 ./run_ground.sh /dev/tty.usbserial-14130
EOF
    exit 0
fi

PORT="${1:-/dev/ttyUSB0}"

VENV_DIR="$SCRIPT_DIR/.venv-ground"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtualenv at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

# Install / update deps from PyPI (laptop is assumed to have network).
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements-ground.txt"

exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/ground_viewer.py" "$PORT"
