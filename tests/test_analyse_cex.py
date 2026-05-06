"""Unit tests for counterexample analysis."""

import io
import pathlib
import sys
import tempfile
import unittest

from src import analyse_cex, custom_args, marking, util
from src.logic import parser

# Trace: a=F,F,F,T,T with loop_start=0. Used with formula "F G[0,2] a",
# de_bruijn=[0]. Known result from test_weaken: weakened interval is (0,1).
_TRACE_FILE = pathlib.Path("tests/test_data/trace_bool.xml")

# Minimal trace where "G F[0,4] a" has no weakening (a stays False after t=0).
_NO_WEAKENING_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<counter-example type="0" id="1" desc="BMC Counterexample">
    <node>
        <state id='1'>
            <value variable="a">TRUE</value>
        </state>
    </node>
    <node>
        <state id='2'>
            <value variable="a">FALSE</value>
        </state>
    </node>
    <loops> 1 </loops>
</counter-example>
"""


def _make_analysis(
    formula_str: str = "F G[0,2] a",
    de_bruijn: list[int] | None = None,
    trace_file: pathlib.Path = _TRACE_FILE,
    model_checker: custom_args.ModelChecker = custom_args.ModelChecker.NUXMV,
) -> analyse_cex.AnalyseCex:
    if de_bruijn is None:
        de_bruijn = [0]
    return analyse_cex.AnalyseCex(
        parser.parse_mtl(formula_str),
        de_bruijn,
        trace_file,
        model_checker,
    )


class TestParseArgs(unittest.TestCase):
    def test_defaults(self) -> None:
        args = analyse_cex.parse_args(
            ["--mtl", "G a", "--de-bruijn", "0", "some_file"],
        )
        self.assertEqual(args.mtl, "G a")
        self.assertEqual(args.de_bruijn, [0])
        self.assertFalse(args.show_markings)
        self.assertEqual(args.model_checker, custom_args.ModelChecker.NUXMV)

    def test_show_markings_flag(self) -> None:
        args = analyse_cex.parse_args(
            ["--mtl", "F a", "--de-bruijn", "0", "--show-markings", "f"],
        )
        self.assertTrue(args.show_markings)

    def test_model_checker_spin(self) -> None:
        args = analyse_cex.parse_args(
            [
                "--mtl",
                "F a",
                "--de-bruijn",
                "0",
                "--model-checker",
                "SPIN",
                "f",
            ],
        )
        self.assertEqual(args.model_checker, custom_args.ModelChecker.SPIN)

    def test_multi_index_de_bruijn(self) -> None:
        args = analyse_cex.parse_args(
            ["--mtl", "G F a", "--de-bruijn", "0,0", "f"],
        )
        self.assertEqual(args.de_bruijn, [0, 0])


class TestReadTraceInput(unittest.TestCase):
    def test_reads_from_file(self) -> None:
        lines = analyse_cex.read_trace_input(_TRACE_FILE)
        self.assertTrue(any("FALSE" in line for line in lines))

    def test_reads_from_stdin(self) -> None:
        fake_input = "line one\nline two\n"
        original = sys.stdin
        sys.stdin = io.StringIO(fake_input)
        try:
            lines = analyse_cex.read_trace_input(None)
        finally:
            sys.stdin = original
        self.assertEqual(lines, ["line one\n", "line two\n"])


class TestGetCexTrace(unittest.TestCase):
    def test_nuxmv_format(self) -> None:
        xml = _TRACE_FILE.read_text(encoding="utf-8")
        lines = xml.splitlines(keepends=True)
        trace = analyse_cex.get_cex_trace(custom_args.ModelChecker.NUXMV, lines)
        self.assertIsInstance(trace, marking.Trace)
        self.assertEqual(len(trace.trace), 5)

    def test_spin_format(self) -> None:
        spin_lines = [
            '{"a": 0}',
            '{"a": 1}',
        ]
        trace = analyse_cex.get_cex_trace(
            custom_args.ModelChecker.SPIN,
            spin_lines,
        )
        self.assertIsInstance(trace, marking.Trace)
        self.assertEqual(len(trace.trace), 2)


class TestAnalyseCex(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = _make_analysis()

    def test_get_weakened_interval(self) -> None:
        result = self.analysis.get_weakened_interval()
        self.assertEqual(result, (0, 1))

    def test_does_formula_hold_false(self) -> None:
        # The original formula "F G[0,2] a" does not hold on the trace
        formula = parser.parse_mtl("F G[0,2] a")
        self.assertFalse(self.analysis.does_formula_hold(formula))

    def test_does_formula_hold_true(self) -> None:
        # Prop("a") holds at positions 3 and 4; markings[Prop("a")][0] = False
        # but the weakened G[0,1] within F does hold at some point
        interval = self.analysis.get_weakened_interval()
        assert interval is not None
        weakened = parser.parse_mtl(f"F G[{interval[0]},{interval[1]}] a")
        self.assertTrue(self.analysis.does_formula_hold(weakened))

    def test_get_markings_returns_marking(self) -> None:
        m = self.analysis.get_markings()
        self.assertIsInstance(m, marking.Marking)

    def test_get_weakening_type_always_is_contraction(self) -> None:
        # Subformula is G[0,2] a (Always) → CONTRACTION
        self.assertEqual(
            self.analysis.get_weakening_type(),
            analyse_cex.WeakeningType.CONTRACTION,
        )

    def test_get_weakening_type_eventually_is_extension(self) -> None:
        analysis = _make_analysis("G F[0,2] a", [0])
        self.assertEqual(
            analysis.get_weakening_type(),
            analyse_cex.WeakeningType.EXTENSION,
        )

    def test_get_weakening_type_until_is_extension(self) -> None:
        # Use only 'a' so it appears in the trace
        analysis = _make_analysis("G (a U[0,2] a)", [0])
        self.assertEqual(
            analysis.get_weakening_type(),
            analyse_cex.WeakeningType.EXTENSION,
        )

    def test_get_weakening_type_release_is_contraction(self) -> None:
        analysis = _make_analysis("G (a R[0,2] a)", [0])
        self.assertEqual(
            analysis.get_weakening_type(),
            analyse_cex.WeakeningType.CONTRACTION,
        )

    def test_choose_weakest_interval_extension_picks_max(self) -> None:
        # Subformula F[0,2] a → EXTENSION → choose interval with largest upper bound
        analysis = _make_analysis("G F[0,2] a", [0])
        result = analysis.choose_weakest_interval([(0, 1), (0, 5), (0, 3)])
        self.assertEqual(result, (0, 5))

    def test_choose_weakest_interval_contraction_picks_min(self) -> None:
        # Subformula G[0,2] a → CONTRACTION → choose interval with smallest upper bound
        result = self.analysis.choose_weakest_interval([(0, 1), (0, 5), (0, 3)])
        self.assertEqual(result, (0, 1))


class TestMain(unittest.TestCase):
    def _run_main(self, args: analyse_cex.Namespace) -> str:
        captured = io.StringIO()
        original = sys.stdout
        sys.stdout = captured
        try:
            analyse_cex.main(args)
        finally:
            sys.stdout = original
        return captured.getvalue().strip()

    def _make_args(
        self,
        formula: str = "F G[0,2] a",
        de_bruijn: list[int] | None = None,
        trace_file: pathlib.Path = _TRACE_FILE,
        show_markings: bool = False,
        model_checker: custom_args.ModelChecker = custom_args.ModelChecker.NUXMV,
    ) -> analyse_cex.Namespace:
        if de_bruijn is None:
            de_bruijn = [0]
        args = analyse_cex.Namespace()
        args.mtl = formula
        args.de_bruijn = de_bruijn
        args.trace_file = trace_file
        args.show_markings = show_markings
        args.model_checker = model_checker
        return args

    def test_main_prints_weakened_interval(self) -> None:
        output = self._run_main(self._make_args())
        self.assertEqual(output, "[0,1]")

    def test_main_no_weakening_prints_message(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".xml",
            delete=False,
        ) as f:
            f.write(_NO_WEAKENING_XML)
            tmp = pathlib.Path(f.name)
        try:
            args = self._make_args("G F[0,4] a", [0], tmp)
            output = self._run_main(args)
            self.assertEqual(output, util.NO_WEAKENING_EXISTS_STR)
        finally:
            tmp.unlink()

    def test_main_show_markings_prints_markings(self) -> None:
        output = self._run_main(self._make_args(show_markings=True))
        # The marking output precedes the interval line
        self.assertIn("[0,1]", output)


if __name__ == "__main__":
    unittest.main()
