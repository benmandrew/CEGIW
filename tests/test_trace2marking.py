"""Unit tests for the trace2marking CLI module."""

import io
import pathlib
import sys
import unittest

from src import trace2marking, util

_TRACE_FILE = pathlib.Path("tests/test_data/trace_valid.xml")
_NO_LOOP_FILE = pathlib.Path("tests/test_data/trace_no_loop.xml")


class TestReadTraceInput(unittest.TestCase):
    def test_reads_from_file(self) -> None:
        lines = trace2marking.read_trace_input(_TRACE_FILE)
        self.assertTrue(any("timer" in line for line in lines))
        self.assertIsInstance(lines, list)

    def test_reads_from_stdin(self) -> None:
        fake = "<foo/>"
        original = sys.stdin
        sys.stdin = io.StringIO(fake)
        try:
            lines = trace2marking.read_trace_input(None)
        finally:
            sys.stdin = original
        self.assertEqual(lines, ["<foo/>"])


class TestGetCexTrace(unittest.TestCase):
    def test_parses_xml_trace(self) -> None:
        xml = _TRACE_FILE.read_text(encoding="utf-8")
        lines = xml.splitlines(keepends=True)
        trace = trace2marking.get_cex_trace(lines)
        self.assertEqual(len(trace.trace), 3)
        self.assertEqual(trace.loop_start, 1)


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.addTypeEqualityFunc(str, self.assertMultiLineEqual)

    def test_main_with_loop(self) -> None:
        result = util.format_expect(trace2marking.main(_TRACE_FILE))
        expected = util.format_expect(
            """
                   0 1 2
        timer     │0│1│0│
        =Lasso=      └─┘
            """,
        )
        self.assertEqual(result, expected)

    def test_main_no_loop(self) -> None:
        result = util.format_expect(trace2marking.main(_NO_LOOP_FILE))
        expected = util.format_expect(
            """
                   0 1 2
        timer     │0│1│0│
            """,
        )
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
