# Raspberry Pi 5 Deployment Checklist (Doc-Aligned)

Use this once the Pi and RFD900ux hardware arrive.

## 1) Copy project to Pi

From your laptop (replace `<PI_USER>` and `<PI_IP>`):

```bash
scp -r methane-visualization-analysis <PI_USER>@<PI_IP>:/home/<PI_USER>/
```

The Pi does not need network access after this point.

## 2) Connect the air-side serial devices

- For `BUNDLE-RFD900ux-US`, connect the RFD900ux air radio to the Pi with the included FTDI USB cable.
- Connect the methane sensor to the Pi UART.
- Keep the radio and sensor on separate device paths.

Attach antenna(s) before powering radios.

Check what the Pi sees:

```bash
ls /dev/ttyUSB* /dev/ttyACM* /dev/serial* 2>/dev/null
```

Recommended mapping:
- Radio: `/dev/ttyUSB0` (auto-detected if absent)
- Sensor: `/dev/serial0`

Expected sensor input format:

```text
1.234
```

## 3) Enable UART on Pi if the sensor uses `/dev/serial0`

```bash
sudo raspi-config
```

- Interface Options -> Serial Port
- Login shell over serial: `No`
- Serial port hardware enabled: `Yes`
- Reboot after saving

## 4) Install and auto-start the air service

Run the installer once. It creates the venv, installs `pyserial` from the vendored wheels in `vendor/wheels/` (fully offline), registers the systemd service, and starts it:

```bash
cd /home/<PI_USER>/methane-visualization-analysis
sudo ./install_pi.sh
```

Every subsequent reboot auto-runs the air transmitter with no manual steps. Check status at any time:

```bash
systemctl status air_tx.service
journalctl -u air_tx.service -f
```

To override a serial port or baud rate, use `sudo systemctl edit air_tx.service` and add a drop-in `[Service]` section with the `Environment=` lines you need.

## 5) Ground laptop viewer

On your laptop:

**Linux/macOS:**

```bash
cd methane-visualization-analysis
./run_ground.sh /dev/ttyUSB0
```

**Windows PowerShell:**

```powershell
cd methane-visualization-analysis
.\run_ground.ps1 -Port COM7
```

First run creates `.venv-ground` and installs matplotlib + pyserial from PyPI.

Examples for `<PORT>`:
- Windows: `COM7`
- Linux: `/dev/ttyUSB0`
- macOS: `/dev/tty.usbserial-XXXX`

## 6) Quick troubleshooting

- If no telemetry appears, verify the radio is connected on the expected USB serial device.
- Confirm both the radio and sensor serial devices exist.
- Keep both radios on same baud and radio params.
- Ensure antenna is connected before transmit.
- If `install_pi.sh` reports missing wheels, re-copy the repo from a workstation that has `vendor/wheels/pyserial-*.whl` committed.
