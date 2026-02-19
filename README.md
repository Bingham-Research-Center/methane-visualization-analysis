# Ground Viewer

Real-time methane telemetry viewer for RFD900ux radio links.

## Overview

`ground_viewer.py` reads CSV-formatted `timestamp,value` packets from a serial port (typically an RFD900ux ground radio), displays a live scrolling matplotlib strip chart, and mirrors every valid reading to a local CSV log file.

## Requirements

- Python 3
- `pyserial` >= 3.5
- `matplotlib` >= 3.7

Install with:

```bash
pip install -r requirements-ground.txt
```

## Usage

```bash
python ground_viewer.py [PORT]
```

`PORT` defaults to `COM7` if omitted. On macOS/Linux this will typically be a `/dev/tty*` path.

Press **Ctrl+C** to shut down gracefully.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROUNDBAUD` | `57600` | Serial baud rate |
| `GROUNDMIRROR` | `ground_methane_log.csv` | Path for the mirror CSV log |
| `GROUNDWINDOWS` | `300` | Strip-chart window width in seconds |
| `METHANEVAL_MIN` | `0` | Minimum valid methane reading (packets below this are dropped) |
| `METHANEVAL_MAX` | `10000` | Maximum valid methane reading (packets above this are dropped) |

## Packet Format

The viewer expects each serial line to be a two-field CSV:

```
timestamp_s,methane_value
```

Both fields must parse as floats. Lines that are malformed, contain non-numeric values, or have a methane value outside the `METHANEVAL_MIN`–`METHANEVAL_MAX` range are silently dropped (logged at debug level).

## CSV Output

Valid readings are appended to the mirror CSV file (`GROUNDMIRROR`). If the file does not already exist, a header row is written first:

```
timestamp_s,methane_value
```

Timestamps are written with millisecond precision (`%.3f`) and methane values with six decimal places (`%.6f`). The file is flushed after every row so data is preserved even on an unexpected exit.

## Troubleshooting / Debug Logging

By default the viewer logs at `INFO` level. To see dropped-packet diagnostics, set the log level to `DEBUG` by changing the `basicConfig` call in the script:

```python
logging.basicConfig(
    level=logging.DEBUG,
    ...
)
```

Or set the `LOGLEVEL` environment variable if you add support for it:

```python
level=getattr(logging, os.environ.get("LOGLEVEL", "INFO").upper(), logging.INFO),
```
