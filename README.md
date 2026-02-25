# Methane Visualization Analysis

Air-to-ground methane telemetry pipeline for Raspberry Pi 5 + RFD900ux radios.

## What This Repository Does

1. `air_tx_pi5.py` (air side, Raspberry Pi):
- reads methane values (currently a placeholder generator in `read_methane()`),
- logs each reading locally to CSV,
- transmits `timestamp_s,methane_value` packets over UART.
2. `ground_viewer.py` (ground side, laptop):
- reads incoming serial packets from the ground radio,
- plots a live scrolling strip chart,
- mirrors valid packets to a local CSV.

## Repository Contents

| Path | Purpose |
|---|---|
| `air_tx_pi5.py` | Air-side transmitter/logger script for Pi |
| `ground_viewer.py` | Ground-side live viewer + mirror logger |
| `requirements-air.txt` | Air-side Python dependencies |
| `requirements-ground.txt` | Ground-side Python dependencies |
| `services/air_tx.service` | Example `systemd` service for auto-start on Pi |
| `services/airtx.service` | Duplicate legacy service file (same content) |
| `DEPLOY_CHECKLIST_PI5.md` | Supplemental deployment checklist |
| `docs/` | Wiring and quick-start reference files |

## Prerequisites

### Hardware

- Raspberry Pi 5 (air side)
- Two RFD900ux radios (air + ground)
- Proper antennas attached before powering radios
- Methane sensor integration on Pi (future; script currently uses placeholder readings)

### Software

- Python 3.9+ recommended
- `pip` and `venv`
- Desktop environment on ground machine for `matplotlib` live plot window

## Quick Start

1. Wire Pi UART to the air radio.
2. Enable UART on the Pi.
3. Install air-side dependencies and run `air_tx_pi5.py`.
4. Install ground-side dependencies and run `ground_viewer.py <PORT>`.
5. Confirm the live plot updates and both CSV logs grow.

## Air Side (Pi) Setup and Run

### 1) Wire Pi 5 to RFD900ux (air radio)

- Pin 8 `GPIO14 TXD` -> radio `RX`
- Pin 10 `GPIO15 RXD` <- radio `TX`
- Pin 2 or 4 `5V` -> radio `+5V`
- Pin 6 `GND` -> radio `GND`

### 2) Enable UART on the Pi

```bash
sudo raspi-config
```

Set:

- Interface Options -> Serial Port
- Login shell over serial: `No`
- Serial hardware enabled: `Yes`

Then reboot.

### 3) Install dependencies

```bash
cd /path/to/methane-visualization-analysis
python3 -m venv .venv-air
source .venv-air/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-air.txt
```

### 4) Run air transmitter

```bash
cd /path/to/methane-visualization-analysis
source .venv-air/bin/activate
python3 air_tx_pi5.py
```

Expected startup log:

```text
Serial port /dev/serial0 opened successfully at 57600 baud
```

Default air-side output file:

- `methane_log.csv` in current working directory

## Ground Side (Viewer) Setup and Run

`ground_viewer.py` requires a serial port argument or it defaults to `COM7`.

### Find the serial port

Windows PowerShell:

```powershell
Get-CimInstance Win32_SerialPort | Select-Object DeviceID, Name
```

Linux/macOS:

```bash
ls /dev/ttyUSB* /dev/ttyACM* /dev/tty.usbserial* 2>/dev/null
```

### Windows (PowerShell)

```powershell
cd C:\path\to\methane-visualization-analysis
py -3 -m venv .venv-ground
.venv-ground\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-ground.txt
python .\ground_viewer.py COM7
```

### macOS/Linux

```bash
cd /path/to/methane-visualization-analysis
python3 -m venv .venv-ground
source .venv-ground/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-ground.txt
python3 ground_viewer.py /dev/ttyUSB0
```

Expected startup log:

```text
Serial port <PORT> opened successfully at 57600 baud
```

Default ground-side output file:

- `ground_methane_log.csv` in current working directory

Press `Ctrl+C` in the viewer terminal to shut down gracefully.

## Optional: Auto-Start Air Script with systemd

Use `services/air_tx.service` as the canonical unit file.

1) Copy service file:

```bash
sudo cp services/air_tx.service /etc/systemd/system/air_tx.service
```

2) Edit service paths if needed:

- `WorkingDirectory=/home/pi`
- `ExecStart=/usr/bin/python3 /home/pi/air_tx_pi5.py`

If your deployment path differs, update both values.

3) Reload and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now air_tx.service
```

4) Service lifecycle commands:

```bash
systemctl status air_tx.service
journalctl -u air_tx.service -f
sudo systemctl restart air_tx.service
sudo systemctl stop air_tx.service
sudo systemctl disable air_tx.service
```

## Script Interface Reference

### `air_tx_pi5.py`

CLI arguments:

- none

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `AIRSERIALPORT` | `/dev/serial0` | UART device to transmit telemetry |
| `AIRBAUD` | `57600` | Serial baud rate |
| `AIRLOGCSV` | `methane_log.csv` | Local air-side CSV log path |
| `AIRPERIODS` | `0.5` | Sampling/transmit period in seconds |
| `METHANEVAL_MIN` | `0` | Minimum accepted methane value |
| `METHANEVAL_MAX` | `10000` | Maximum accepted methane value |

Example override:

```bash
AIRSERIALPORT=/dev/ttyAMA0 AIRBAUD=57600 AIRPERIODS=1.0 python3 air_tx_pi5.py
```

### `ground_viewer.py`

CLI arguments:

- `PORT` (optional): serial device (defaults to `COM7` if omitted)

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `GROUNDBAUD` | `57600` | Serial baud rate |
| `GROUNDMIRROR` | `ground_methane_log.csv` | Ground-side mirror CSV path |
| `GROUNDWINDOWS` | `300` | Plot window width in seconds |
| `METHANEVAL_MIN` | `0` | Minimum accepted methane value |
| `METHANEVAL_MAX` | `10000` | Maximum accepted methane value |

Example override:

```bash
GROUNDBAUD=57600 GROUNDWINDOWS=120 GROUNDMIRROR=/tmp/ground.csv python3 ground_viewer.py /dev/ttyUSB0
```

## Packet Format and CSV Outputs

Transmitted packet format:

```text
timestamp_s,methane_value
```

Acceptance rules (ground script):

- exactly two comma-separated fields
- both fields must parse as floats
- methane value must be within `METHANEVAL_MIN` to `METHANEVAL_MAX`

CSV format for both outputs:

- header row (created once if file is new):

```text
timestamp_s,methane_value
```

- row formatting:
- timestamp: `%.3f`
- methane value: `%.6f`
- each row is flushed immediately to disk

## Smoke Tests (Recommended)

1. Start `air_tx_pi5.py` on Pi and verify serial-open success log.
2. Confirm `methane_log.csv` is growing:

```bash
tail -f methane_log.csv
```

3. Start `ground_viewer.py <PORT>` and confirm plot window opens.
4. Confirm `ground_methane_log.csv` is growing:

```bash
tail -f ground_methane_log.csv
```

5. Verify values are within expected range and timestamps advance steadily.

## Troubleshooting

No data appears in viewer:

- verify TX/RX wiring is crossed correctly
- verify both radios share matching serial/radio settings
- confirm correct ground serial port is used

`Cannot open serial port` error:

- ensure port exists (`/dev/serial0`, `/dev/ttyUSB0`, `COMx`, etc.)
- ensure no other process is holding the port
- check permissions on Linux (`dialout` group may be required)

Plot opens but no points appear:

- packets may be malformed or filtered by min/max bounds
- confirm radio link quality and antenna connection

Service fails to start:

- check `systemctl status air_tx.service`
- inspect logs `journalctl -u air_tx.service -e`
- verify `ExecStart` path and Python environment on Pi

## Supplemental Documentation

- Use `DEPLOY_CHECKLIST_PI5.md` for a concise deployment checklist.
- `docs/` contains wiring and quick-start reference documents.
