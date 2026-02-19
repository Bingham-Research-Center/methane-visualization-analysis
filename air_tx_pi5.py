#!/usr/bin/env python3
"""
Air-side methane telemetry transmitter for Raspberry Pi 5 + RFD900ux.

Behavior matches the project docs:
- Logs methane readings locally to CSV on the Pi
- Streams "timestamp_s,methane_value" over UART to the radio
"""

import csv
import logging
import math
import os
import random
import sys
import time

import serial

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("air_tx")

SERIAL_PORT = os.environ.get("AIRSERIALPORT", "/dev/serial0")
BAUD = int(os.environ.get("AIRBAUD", "57600"))
LOG_CSV = os.environ.get("AIRLOGCSV", "methane_log.csv")
PERIOD_S = float(os.environ.get("AIRPERIODS", "0.5"))
METHANE_MIN = float(os.environ.get("METHANEVAL_MIN", "0"))
METHANE_MAX = float(os.environ.get("METHANEVAL_MAX", "10000"))


def read_methane() -> float:
    """
    Placeholder methane value source.
    Replace this with real sensor acquisition when integrating hardware.
    """
    t = time.time()
    return 2.0 + 0.35 * math.sin(t / 8.0) + random.uniform(-0.05, 0.05)


def main() -> None:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
    except serial.SerialException as e:
        logger.error("Cannot open serial port %s: %s", SERIAL_PORT, e)
        sys.exit(1)

    if not ser.is_open:
        logger.error("Serial port %s is not open after initialisation", SERIAL_PORT)
        ser.close()
        sys.exit(1)
    logger.info("Serial port %s opened successfully at %d baud", SERIAL_PORT, BAUD)

    file_is_new = not os.path.exists(LOG_CSV)
    with ser, open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if file_is_new:
            writer.writerow(["timestamp_s", "methane_value"])
            f.flush()

        try:
            next_reading = time.time()
            while True:
                ts = time.time()
                try:
                    val = read_methane()
                except (ValueError, OSError) as e:
                    logger.warning("Sensor read failed, skipping iteration: %s", e)
                    next_reading += PERIOD_S
                    time.sleep(max(0, next_reading - time.time()))
                    continue

                if not (METHANE_MIN <= val <= METHANE_MAX):
                    logger.debug("Methane value out of expected range: %f", val)
                    next_reading += PERIOD_S
                    time.sleep(max(0, next_reading - time.time()))
                    continue

                # 1) Local authoritative log
                writer.writerow([f"{ts:.3f}", f"{val:.6f}"])
                f.flush()

                # 2) Live stream over telemetry link
                line = f"{ts:.3f},{val:.6f}\n"
                try:
                    ser.write(line.encode("utf-8"))
                    ser.flush()
                except serial.SerialException as e:
                    logger.warning("Serial write failed (radio link may be down): %s", e)

                next_reading += PERIOD_S
                time.sleep(max(0, next_reading - time.time()))
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
