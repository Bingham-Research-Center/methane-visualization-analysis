# Raspberry Pi 5 Deployment Checklist (Doc-Aligned)

Use this once the Pi and RFD900ux hardware arrive.

## 1) Copy project to Pi

From your laptop (replace `<PI_IP>`):

```bash
scp -r "METHANE VISUALIZATION ANALYSIS NEW" pi@<PI_IP>:/home/pi/
```

## 2) Wire Pi5 to RFD900ux (air unit)

- Pin 8 `GPIO14 TXD` -> RFD `RX`
- Pin 10 `GPIO15 RXD` <- RFD `TX`
- Pin 2 or 4 `5V` -> RFD `+5V`
- Pin 6 `GND` -> RFD `GND`

Attach antenna(s) before powering radios.

## 3) Enable UART on Pi

```bash
sudo raspi-config
```

- Interface Options -> Serial Port
- Login shell over serial: `No`
- Serial port hardware enabled: `Yes`
- Reboot after saving

## 4) Install runtime deps on Pi (air side)

```bash
cd "/home/pi/METHANE VISUALIZATION ANALYSIS NEW"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-air.txt
```

## 5) Run air transmitter manually (first test)

```bash
cd "/home/pi/METHANE VISUALIZATION ANALYSIS NEW"
source .venv/bin/activate
python3 air_tx_pi5.py
```

Expected output files:
- `methane_log.csv` grows locally on Pi

## 6) Ground laptop viewer

On your laptop:

```bash
cd "METHANE VISUALIZATION ANALYSIS NEW"
python3 -m venv .venv-ground
source .venv-ground/bin/activate
pip install --upgrade pip
pip install -r requirements-ground.txt
python3 ground_viewer.py <PORT>
```

Examples for `<PORT>`:
- Windows: `COM7`
- Linux: `/dev/ttyUSB0`
- macOS: `/dev/tty.usbserial-XXXX`

## 7) Optional autostart service on Pi

```bash
cd "/home/pi/METHANE VISUALIZATION ANALYSIS NEW"
sudo cp services/air_tx.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now air_tx.service
```

Check status:

```bash
systemctl status air_tx.service
```

## 8) Quick troubleshooting

- If no telemetry appears, verify TX/RX are crossed correctly.
- Confirm Pi serial device exists (`/dev/serial0` by default in script).
- Keep both radios on same baud and radio params.
- Ensure antenna is connected before transmit.
