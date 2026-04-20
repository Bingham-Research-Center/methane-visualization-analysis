#!/usr/bin/env bash
#
# Air-side telemetry launcher (Raspberry Pi).
#
# Handles radio device auto-detection and env-var defaults, then execs the air
# transmitter under the venv populated by install_pi.sh. Invoked by the systemd
# service on boot AND safe to run manually from an SSH session for testing.
#
# The venv is expected to already exist (install_pi.sh creates it). Running
# this script does NOT do any pip install, so there is no network dependency
# at launch time.
#
# Any env var can be overridden at invocation time:
#   AIRSERIALPORT=/dev/ttyUSB1 ./run_air.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat <<'EOF'
Usage: ./run_air.sh

Launches the air-side methane transmitter. Must run on a Pi with the radio on
USB serial and the methane sensor on its own serial device. Prereqs:
  - sudo ./install_pi.sh has been run once (creates .venv, installs pyserial)
  - radio serial adapter plugged in (default expects /dev/ttyUSB0)
  - sensor on /dev/serial0 (default) or override via AIRSENSORPORT

Supported environment variables (all optional, with defaults):
  AIRSERIALPORT       Radio device (auto-detects /dev/ttyUSB* if unset)
  AIRBAUD             Radio baud rate                              [57600]
  AIRSENSORPORT       Sensor device                           [/dev/serial0]
  AIRSENSORBAUD       Sensor baud rate                              [9600]
  AIRSENSORTIMEOUT    Sensor read timeout in seconds                 [0.5]
  AIRPERIODS          Loop period in seconds                         [0.5]
  AIRLOGCSV           Local CSV log path                [methane_log.csv]
  AIRLOGMAXBYTES      Log rotation threshold in bytes         [10485760]
  METHANEVAL_MIN      Minimum accepted methane value                   [0]
  METHANEVAL_MAX      Maximum accepted methane value               [10000]

Example override:
  AIRSERIALPORT=/dev/ttyUSB1 AIRSENSORBAUD=19200 ./run_air.sh
EOF
    exit 0
fi

VENV_PY="$SCRIPT_DIR/.venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
    echo "Error: $VENV_PY not found. Run 'sudo ./install_pi.sh' first." >&2
    exit 1
fi

# Auto-detect radio device only when the user has not set AIRSERIALPORT.
if [[ -z "${AIRSERIALPORT:-}" ]]; then
    if [[ -e /dev/ttyUSB0 ]]; then
        AIRSERIALPORT=/dev/ttyUSB0
    else
        # Glob /dev/ttyUSB* and decide based on how many we find.
        shopt -s nullglob
        candidates=(/dev/ttyUSB*)
        shopt -u nullglob
        case ${#candidates[@]} in
            0)
                echo "Error: no /dev/ttyUSB* device found. Plug in the radio or set AIRSERIALPORT." >&2
                exit 1
                ;;
            1)
                AIRSERIALPORT="${candidates[0]}"
                echo "Auto-detected radio device: $AIRSERIALPORT"
                ;;
            *)
                echo "Error: multiple /dev/ttyUSB* devices found. Set AIRSERIALPORT to pick one:" >&2
                printf '  %s\n' "${candidates[@]}" >&2
                exit 1
                ;;
        esac
    fi
fi
export AIRSERIALPORT

# Defaults for everything else. User-supplied values win thanks to :- expansion.
export AIRSENSORPORT="${AIRSENSORPORT:-/dev/serial0}"
export AIRSENSORBAUD="${AIRSENSORBAUD:-9600}"
export AIRSENSORTIMEOUT="${AIRSENSORTIMEOUT:-0.5}"

# Hand control to Python; use exec so signals go straight to it.
exec "$VENV_PY" air_tx_pi5.py
