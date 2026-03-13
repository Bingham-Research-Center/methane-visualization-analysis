#!/usr/bin/env python3
"""
Air-side methane telemetry transmitter for Raspberry Pi 5 + RFD900ux.

Behavior matches the project docs:
- Reads methane values from a dedicated serial-connected sensor
- Expects one numeric methane reading per sensor line
- Logs methane readings locally to CSV on the Pi
- Streams "timestamp_s,methane_value" over a separate serial radio link
"""

import csv
import logging
import os
import sys
import time

import serial

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("air_tx")

RADIO_SERIAL_PORT = os.environ.get("AIRSERIALPORT", "/dev/ttyUSB0")
RADIO_BAUD = int(os.environ.get("AIRBAUD", "57600"))
SENSOR_SERIAL_PORT = os.environ.get("AIRSENSORPORT")
SENSOR_BAUD = int(os.environ.get("AIRSENSORBAUD", "9600"))
LOG_CSV = os.environ.get("AIRLOGCSV", "methane_log.csv")
PERIOD_S = float(os.environ.get("AIRPERIODS", "0.5"))
SENSOR_TIMEOUT_S = float(os.environ.get("AIRSENSORTIMEOUT", str(PERIOD_S)))
METHANE_MIN = float(os.environ.get("METHANEVAL_MIN", "0"))
METHANE_MAX = float(os.environ.get("METHANEVAL_MAX", "10000"))


def open_serial(port: str, baud: int, timeout: float, label: str) -> serial.Serial:
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
    except serial.SerialException as e:
        logger.error("Cannot open %s serial port %s: %s", label.lower(), port, e)
        sys.exit(1)

    if not ser.is_open:
        logger.error("%s serial port %s is not open after initialisation", label, port)
        ser.close()
        sys.exit(1)

    logger.info("%s serial port %s opened successfully at %d baud", label, port, baud)
    return ser


def read_methane(sensor_ser: serial.Serial) -> float:
    raw = sensor_ser.readline()
    if not raw:
        raise TimeoutError("Sensor read timed out")

    text = raw.decode("utf-8", errors="ignore").strip()
    if not text:
        raise ValueError("Empty sensor line")

    try:
        return float(text)
    except ValueError as e:
        raise ValueError(f"Malformed sensor value: {text!r}") from e


def main() -> None:
    if not SENSOR_SERIAL_PORT:
        logger.error("AIRSENSORPORT is required so air_tx_pi5.py can read a real methane sensor")
        sys.exit(1)
    if SENSOR_SERIAL_PORT == RADIO_SERIAL_PORT:
        logger.error("AIRSERIALPORT and AIRSENSORPORT must point to different serial devices")
        sys.exit(1)

    radio_ser = open_serial(RADIO_SERIAL_PORT, RADIO_BAUD, 1.0, "Radio")
    sensor_ser = open_serial(SENSOR_SERIAL_PORT, SENSOR_BAUD, SENSOR_TIMEOUT_S, "Sensor")

    file_is_new = not os.path.exists(LOG_CSV)
    with radio_ser, sensor_ser, open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if file_is_new:
            writer.writerow(["timestamp_s", "methane_value"])
            f.flush()

        try:
            next_reading = time.time()
            while True:
                try:
                    val = read_methane(sensor_ser)
                except TimeoutError:
                    next_reading += PERIOD_S
                    time.sleep(max(0, next_reading - time.time()))
                    continue
                except serial.SerialException as e:
                    logger.warning("Sensor serial read failed, skipping iteration: %s", e)
                    next_reading += PERIOD_S
                    time.sleep(max(0, next_reading - time.time()))
                    continue
                except (ValueError, OSError) as e:
                    logger.warning("Sensor read failed, skipping iteration: %s", e)
                    next_reading += PERIOD_S
                    time.sleep(max(0, next_reading - time.time()))
                    continue

                ts = time.time()
                if not (METHANE_MIN <= val <= METHANE_MAX):
                    logger.debug("Methane value out of expected range: %f", val)
                else:
                    writer.writerow([f"{ts:.3f}", f"{val:.6f}"])
                    f.flush()
                    line = f"{ts:.3f},{val:.6f}\n"
                    try:
                        radio_ser.write(line.encode("utf-8"))
                        radio_ser.flush()
                    except serial.SerialException as e:
                        logger.warning("Serial write failed (radio link may be down): %s", e)

                next_reading += PERIOD_S
                time.sleep(max(0, next_reading - time.time()))
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
