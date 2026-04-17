"""Tests for core parsing and validation logic in air_tx_pi5 and ground_viewer."""

import unittest
from unittest.mock import MagicMock

from air_tx_pi5 import read_methane


class TestReadMethane(unittest.TestCase):
    def _make_sensor(self, line: bytes):
        sensor = MagicMock()
        sensor.readline.return_value = line
        return sensor

    def test_valid_integer(self):
        self.assertEqual(read_methane(self._make_sensor(b"42\n")), 42.0)

    def test_valid_float(self):
        self.assertAlmostEqual(read_methane(self._make_sensor(b"3.14\n")), 3.14)

    def test_valid_with_whitespace(self):
        self.assertEqual(read_methane(self._make_sensor(b"  100  \r\n")), 100.0)

    def test_timeout_empty_bytes(self):
        with self.assertRaises(TimeoutError):
            read_methane(self._make_sensor(b""))

    def test_empty_line(self):
        with self.assertRaises(ValueError):
            read_methane(self._make_sensor(b"  \n"))

    def test_malformed_non_numeric(self):
        with self.assertRaises(ValueError):
            read_methane(self._make_sensor(b"abc\n"))

    def test_malformed_partial(self):
        with self.assertRaises(ValueError):
            read_methane(self._make_sensor(b"12.3.4\n"))


class TestRangeValidation(unittest.TestCase):
    """Range check logic used by both air and ground scripts."""

    def _in_range(self, val, lo=0.0, hi=10000.0):
        return lo <= val <= hi

    def test_within_range(self):
        self.assertTrue(self._in_range(500))

    def test_at_min_boundary(self):
        self.assertTrue(self._in_range(0))

    def test_at_max_boundary(self):
        self.assertTrue(self._in_range(10000))

    def test_below_min(self):
        self.assertFalse(self._in_range(-1))

    def test_above_max(self):
        self.assertFalse(self._in_range(10001))


class TestPacketParsing(unittest.TestCase):
    """Packet parsing logic as used by ground_viewer.py."""

    def _parse_packet(self, raw: str):
        """Replicate ground_viewer's inline parsing logic."""
        parts = raw.split(",")
        if len(parts) != 2:
            return None
        try:
            ts = float(parts[0])
            val = float(parts[1])
        except ValueError:
            return None
        return ts, val

    def test_valid_packet(self):
        result = self._parse_packet("1713400000.123,42.500000")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result[0], 1713400000.123)
        self.assertAlmostEqual(result[1], 42.5)

    def test_too_few_fields(self):
        self.assertIsNone(self._parse_packet("42.0"))

    def test_too_many_fields(self):
        self.assertIsNone(self._parse_packet("1.0,2.0,3.0"))

    def test_empty_string(self):
        self.assertIsNone(self._parse_packet(""))

    def test_non_numeric_timestamp(self):
        self.assertIsNone(self._parse_packet("abc,42.0"))

    def test_non_numeric_value(self):
        self.assertIsNone(self._parse_packet("1.0,xyz"))


if __name__ == "__main__":
    unittest.main()
