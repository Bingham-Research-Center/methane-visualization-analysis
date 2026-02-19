#!/usr/bin/env python3
"""
Ground-side viewer for RFD900ux telemetry.

Behavior matches the project docs:
- Opens the ground radio serial port
- Plots a live scrolling strip chart
- Mirrors incoming telemetry to local CSV
"""

import collections
import csv
import logging
import os
import signal
import sys
import time

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import serial

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ground_viewer")

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM7"
BAUD = int(os.environ.get("GROUNDBAUD", "57600"))
MIRROR_CSV = os.environ.get("GROUNDMIRROR", "ground_methane_log.csv")
WINDOW_SECONDS = int(os.environ.get("GROUNDWINDOWS", "300"))
METHANE_MIN = float(os.environ.get("METHANEVAL_MIN", "0"))
METHANE_MAX = float(os.environ.get("METHANEVAL_MAX", "10000"))


def main() -> None:
    def signal_handler(sig, frame):
        logger.info("Shutting down gracefully...")
        plt.close('all')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
    except serial.SerialException as e:
        logger.error("Cannot open serial port %s: %s", PORT, e)
        sys.exit(1)

    if not ser.is_open:
        logger.error("Serial port %s is not open after initialisation", PORT)
        ser.close()
        sys.exit(1)
    logger.info("Serial port %s opened successfully at %d baud", PORT, BAUD)

    file_is_new = not os.path.exists(MIRROR_CSV)
    with ser, open(MIRROR_CSV, "a", newline="", encoding="utf-8") as mirror:
        writer = csv.writer(mirror)

        if file_is_new:
            writer.writerow(["timestamp_s", "methane_value"])
            mirror.flush()

        data = collections.deque(maxlen=20000)
        t0 = None

        fig, ax = plt.subplots(figsize=(9, 4.5))
        (line,) = ax.plot([], [], lw=2)
        ax.set_title("Live Methane (strip chart)")
        ax.set_xlabel("Time (s, relative)")
        ax.set_ylabel("Methane (units)")

        def update(_frame):
            nonlocal t0

            # Drain available serial input each frame.
            try:
                while ser.in_waiting:
                    raw = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not raw:
                        continue

                    parts = raw.split(",")
                    if len(parts) != 2:
                        continue

                    try:
                        ts = float(parts[0])
                        val = float(parts[1])
                    except ValueError:
                        continue

                    if not (METHANE_MIN <= val <= METHANE_MAX):
                        logger.debug("Methane value out of expected range: %f", val)
                        continue

                    if t0 is None:
                        t0 = ts

                    data.append((ts - t0, val))
                    writer.writerow([f"{ts:.3f}", f"{val:.6f}"])
                    mirror.flush()
            except serial.SerialException as e:
                logger.warning("Serial read error (radio link may be interrupted): %s", e)

            if not data:
                return (line,)

            tmax = data[-1][0]
            while data and (tmax - data[0][0]) > WINDOW_SECONDS:
                data.popleft()

            xs = [p[0] for p in data]
            ys = [p[1] for p in data]
            if not ys:
                ax.set_ylim(-1, 1)
                return (line,)
            line.set_data(xs, ys)
            ax.set_xlim(max(0, tmax - WINDOW_SECONDS), tmax + 2)

            ymin, ymax = min(ys), max(ys)
            pad = max(1e-6, (ymax - ymin) * 0.1)
            ax.set_ylim(ymin - pad, ymax + pad)
            return (line,)

        animation.FuncAnimation(fig, update, interval=200)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()
