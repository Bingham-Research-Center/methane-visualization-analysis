# Methane Visualization Analysis

Air-to-ground methane telemetry pipeline for Raspberry Pi 5 + RFD900ux radios.

## What This Repository Does

1. `air_tx_pi5.py` (air side, Raspberry Pi):
- reads methane values from a dedicated serial-connected sensor,
- expects one numeric methane value per line from that sensor,
- logs each reading locally to CSV,
- transmits `timestamp_s,methane_value` packets over a separate serial radio link.
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
| `services/airtx.service` | Deprecated compatibility shim for legacy install scripts |
| `DEPLOY_CHECKLIST_PI5.md` | Supplemental deployment checklist |
| `docs/` | Wiring and quick-start reference files |

## Prerequisites

### Hardware

- Raspberry Pi 5 (air side)
- RFDesign `BUNDLE-RFD900ux-US` kit or equivalent RFD900ux air/ground radio pair
- Proper antennas attached before powering radios
- Methane sensor connected to the Pi over its own serial interface
- Two separate serial device paths on the Pi: one for the radio and one for the sensor

### Software

- Python 3.9+ recommended
- `pip` and `venv`
- Desktop environment on ground machine for `matplotlib` live plot window

## Quick Start

1. Connect the air radio to the Pi over USB serial.
2. Connect the methane sensor to the Pi UART.
3. Install air-side dependencies and run `air_tx_pi5.py`.
4. Install ground-side dependencies and run `ground_viewer.py <PORT>`.
5. Confirm the live plot updates and both CSV logs grow.

## Air Side (Pi) Setup and Run

### 1) Connect air-side serial devices

- For `BUNDLE-RFD900ux-US`, connect the air radio to the Pi with the included FTDI USB cable so it enumerates as a USB serial device.
- Connect the methane sensor to the Pi UART.
- Do not place both devices on the same serial path.

Check what the Pi sees:

```bash
ls /dev/ttyUSB* /dev/ttyACM* /dev/serial* 2>/dev/null
```

Recommended operational mapping:

- Radio: `/dev/ttyUSB0`
- Sensor: `/dev/serial0`

Expected sensor input format:

```text
1.234
```

The air script expects one numeric methane reading per line.

If your device paths differ, override them with environment variables when you run the script or in the `systemd` unit.

### 2) Enable UART on the Pi if the sensor uses `/dev/serial0`

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
AIRSERIALPORT=/dev/ttyUSB0 AIRSENSORPORT=/dev/serial0 AIRSENSORBAUD=9600 AIRSENSORTIMEOUT=0.5 python3 air_tx_pi5.py
```

This is the current intended setup:

- air radio on USB: `/dev/ttyUSB0`
- methane sensor on Pi UART: `/dev/serial0`

Expected startup log:

```text
Radio serial port /dev/ttyUSB0 opened successfully at 57600 baud
Sensor serial port /dev/serial0 opened successfully at 9600 baud
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

The ground viewer should open a live line chart and mirror valid packets into `ground_methane_log.csv`.

Expected startup log:

```text
Serial port <PORT> opened successfully at 57600 baud
```

Default ground-side output file:

- `ground_methane_log.csv` in current working directory

Press `Ctrl+C` in the viewer terminal to shut down gracefully.

## Optional: Auto-Start Air Script with systemd

Use `services/air_tx.service` as the canonical unit file.
`services/airtx.service` is retained as a deprecated compatibility filename.

1) Copy service file:

```bash
sudo cp services/air_tx.service /etc/systemd/system/air_tx.service
```

2) Edit service paths if needed:

- `WorkingDirectory=/home/pi`
- `ExecStart=/usr/bin/python3 /home/pi/air_tx_pi5.py`
- `Environment=AIRSERIALPORT=...`
- `Environment=AIRSENSORPORT=...`
- `Environment=AIRSENSORBAUD=...`

The checked-in service defaults already match the current setup:

- `AIRSERIALPORT=/dev/ttyUSB0`
- `AIRSENSORPORT=/dev/serial0`

If your deployment path or device paths differ, update those values before enabling the service.

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
| `AIRSERIALPORT` | `/dev/ttyUSB0` | Serial device used for the radio telemetry link |
| `AIRBAUD` | `57600` | Serial baud rate |
| `AIRSENSORPORT` | required | Serial device used for the methane sensor input |
| `AIRSENSORBAUD` | `9600` | Methane sensor serial baud rate |
| `AIRSENSORTIMEOUT` | `AIRPERIODS` | Sensor serial read timeout in seconds |
| `AIRLOGCSV` | `methane_log.csv` | Local air-side CSV log path |
| `AIRPERIODS` | `0.5` | Read/transmit loop period in seconds |
| `METHANEVAL_MIN` | `0` | Minimum accepted methane value |
| `METHANEVAL_MAX` | `10000` | Maximum accepted methane value |

Example override:

```bash
AIRSERIALPORT=/dev/ttyUSB0 AIRBAUD=57600 AIRSENSORPORT=/dev/serial0 AIRSENSORBAUD=9600 AIRSENSORTIMEOUT=0.5 AIRPERIODS=0.5 python3 air_tx_pi5.py
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
| `GROUNDFLUSHSEC` | `1.0` | Periodic mirror CSV flush interval in seconds (`<=0` disables periodic flush) |
| `METHANEVAL_MIN` | `0` | Minimum accepted methane value |
| `METHANEVAL_MAX` | `10000` | Maximum accepted methane value |

Example override:

```bash
GROUNDBAUD=57600 GROUNDWINDOWS=120 GROUNDFLUSHSEC=0.5 GROUNDMIRROR=/tmp/ground.csv python3 ground_viewer.py /dev/ttyUSB0
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
- each row is flushed immediately to disk on air side
- ground side flushes periodically (default every `1.0s`, configurable via `GROUNDFLUSHSEC`)

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

Ground writes may appear in short batches based on `GROUNDFLUSHSEC`.

5. Verify values are within expected range and timestamps advance steadily.

## Troubleshooting

No data appears in viewer:

- verify the air radio is connected on the expected serial device
- verify both radios share matching serial/radio settings
- confirm correct ground serial port is used

`Cannot open serial port` error:

- ensure both the radio port and sensor port exist (`/dev/serial0`, `/dev/ttyUSB0`, `COMx`, etc.)
- ensure no other process is holding the port
- check permissions on Linux (`dialout` group may be required)

Plot opens but no points appear:

- packets may be malformed or filtered by min/max bounds
- confirm radio link quality and antenna connection
- confirm the methane sensor is sending one numeric value per line

Service fails to start:

- check `systemctl status air_tx.service`
- inspect logs `journalctl -u air_tx.service -e`
- verify `ExecStart` path and Python environment on Pi
- verify `AIRSERIALPORT` and `AIRSENSORPORT` point at the correct devices

## Supplemental Documentation

- Use `DEPLOY_CHECKLIST_PI5.md` for a concise deployment checklist.
- `docs/` contains wiring and quick-start reference documents.
