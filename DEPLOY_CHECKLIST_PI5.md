# Raspberry Pi 5 Deployment Checklist (Doc-Aligned)

Use this once the Pi and RFD900ux hardware arrive.

## 1) Copy project to Pi

From your laptop (replace `<PI_IP>`):

```bash
scp -r "METHANE VISUALIZATION ANALYSIS NEW" pi@<PI_IP>:/home/pi/
```

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
- Radio: `/dev/ttyUSB0`
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

## 4) Install runtime deps on Pi (air side)

```bash
cd "/home/pi/METHANE VISUALIZATION ANALYSIS NEW"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-air.txt
```

## 5) Run air transmitter manually

```bash
cd "/home/pi/METHANE VISUALIZATION ANALYSIS NEW"
source .venv/bin/activate
AIRSERIALPORT=/dev/ttyUSB0 AIRSENSORPORT=/dev/serial0 AIRSENSORBAUD=9600 AIRSENSORTIMEOUT=0.5 python3 air_tx_pi5.py
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

- If no telemetry appears, verify the radio is connected on the expected USB serial device.
- Confirm both the radio and sensor serial devices exist.
- Keep both radios on same baud and radio params.
- Ensure antenna is connected before transmit.
