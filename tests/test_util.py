"""Unit tests for utility functions."""

import io
import sys
import unittest

from src import util


class TestStrToValue(unittest.TestCase):
    def test_true(self) -> None:
        self.assertIs(util.str_to_value("TRUE"), True)  # noqa: FBT003

    def test_false(self) -> None:
        self.assertIs(util.str_to_value("FALSE"), False)  # noqa: FBT003

    def test_integer(self) -> None:
        self.assertEqual(util.str_to_value("42"), 42)

    def test_string(self) -> None:
        self.assertEqual(util.str_to_value("resting"), "resting")


class TestIntervalToStr(unittest.TestCase):
    def test_finite(self) -> None:
        self.assertEqual(util.interval_to_str((0, 5)), "[0,5]")

    def test_unbounded(self) -> None:
        self.assertEqual(util.interval_to_str((1, None)), "[1,∞]")

    def test_zero_start(self) -> None:
        self.assertEqual(util.interval_to_str((0, 0)), "[0,0]")


class TestStrToInterval(unittest.TestCase):
    def test_finite(self) -> None:
        self.assertEqual(util.str_to_interval("[0,5]"), (0, 5))

    def test_unbounded(self) -> None:
        self.assertEqual(util.str_to_interval("[1,∞]"), (1, None))

    def test_with_spaces(self) -> None:
        self.assertEqual(util.str_to_interval("[0, 5]"), (0, 5))

    def test_roundtrip(self) -> None:
        interval = (3, 7)
        self.assertEqual(
            util.str_to_interval(util.interval_to_str(interval)),
            interval,
        )

    def test_roundtrip_unbounded(self) -> None:
        interval = (0, None)
        self.assertEqual(
            util.str_to_interval(util.interval_to_str(interval)),
            interval,
        )


class TestEprint(unittest.TestCase):
    def test_writes_to_stderr(self) -> None:
        captured = io.StringIO()
        original = sys.stderr
        sys.stderr = captured
        try:
            util.eprint("hello stderr")
        finally:
            sys.stderr = original
        self.assertEqual(captured.getvalue(), "hello stderr\n")


if __name__ == "__main__":
    unittest.main()
