"""Unit tests for iterative weakening pure helper functions."""

import unittest

from src import iterative_weaken
from src.logic import ctx, mtl, parser


class TestSubstituteInterval(unittest.TestCase):
    def test_always(self) -> None:
        formula = parser.parse_mtl("G[0,5] a")
        assert isinstance(formula, mtl.Always)
        result = iterative_weaken.substitute_interval(formula, (0, 10))
        self.assertEqual(result, mtl.Always(mtl.Prop("a"), (0, 10)))

    def test_eventually(self) -> None:
        formula = parser.parse_mtl("F[0,5] a")
        assert isinstance(formula, mtl.Eventually)
        result = iterative_weaken.substitute_interval(formula, (0, 10))
        self.assertEqual(result, mtl.Eventually(mtl.Prop("a"), (0, 10)))

    def test_until(self) -> None:
        formula = parser.parse_mtl("a U[0,5] b")
        assert isinstance(formula, mtl.Until)
        result = iterative_weaken.substitute_interval(formula, (0, 10))
        self.assertEqual(
            result,
            mtl.Until(mtl.Prop("a"), mtl.Prop("b"), (0, 10)),
        )

    def test_release(self) -> None:
        formula = parser.parse_mtl("a R[0,5] b")
        assert isinstance(formula, mtl.Release)
        result = iterative_weaken.substitute_interval(formula, (0, 10))
        self.assertEqual(
            result,
            mtl.Release(mtl.Prop("a"), mtl.Prop("b"), (0, 10)),
        )

    def test_preserves_operand(self) -> None:
        formula = parser.parse_mtl("G[0,5] (a & b)")
        assert isinstance(formula, mtl.Always)
        result = iterative_weaken.substitute_interval(formula, (2, 8))
        assert isinstance(result, mtl.Always)
        self.assertEqual(result.operand, formula.operand)
        self.assertEqual(result.interval, (2, 8))

    def test_invalid_formula_raises(self) -> None:
        with self.assertRaises(ValueError):
            iterative_weaken.substitute_interval(
                mtl.Prop("a"),  # type: ignore[arg-type]
                (0, 10),
            )


class TestGetInitialBound(unittest.TestCase):
    def test_unbounded_returns_bound_min(self) -> None:
        self.assertEqual(
            iterative_weaken.get_initial_bound((0, None)),
            iterative_weaken.BOUND_MIN,
        )

    def test_small_interval_returns_bound_min(self) -> None:
        # 5 * 1.5 = 7.5, which is less than BOUND_MIN (20)
        self.assertEqual(
            iterative_weaken.get_initial_bound((0, 5)),
            iterative_weaken.BOUND_MIN,
        )

    def test_large_interval_returns_scaled(self) -> None:
        # 100 * 1.5 = 150, which exceeds BOUND_MIN
        self.assertEqual(iterative_weaken.get_initial_bound((0, 100)), 150)

    def test_exactly_at_bound_min_threshold(self) -> None:
        # ceil(BOUND_MIN / 1.5) = 14; 14 * 1.5 = 21 > BOUND_MIN
        threshold = int(iterative_weaken.BOUND_MIN / 1.5) + 1
        result = iterative_weaken.get_initial_bound((0, threshold))
        self.assertGreater(result, iterative_weaken.BOUND_MIN)


class TestGetContextAndSubformula(unittest.TestCase):
    def test_top_level_always(self) -> None:
        context, subformula = iterative_weaken.get_context_and_subformula(
            "G[0,5] a",
            [],
        )
        self.assertIsInstance(context, ctx.Hole)
        self.assertIsInstance(subformula, mtl.Always)
        assert isinstance(subformula, mtl.Always)
        self.assertEqual(subformula.interval, (0, 5))

    def test_nested_eventually(self) -> None:
        _context, subformula = iterative_weaken.get_context_and_subformula(
            "G F[1,3] a",
            [0],
        )
        self.assertIsInstance(subformula, mtl.Eventually)
        assert isinstance(subformula, mtl.Eventually)
        self.assertEqual(subformula.interval, (1, 3))

    def test_negated_context_flips_operator(self) -> None:
        # !G[0,1] a → after partial_nnf, subformula becomes F[0,1] !a
        _context, subformula = iterative_weaken.get_context_and_subformula(
            "! G[0,1] a",
            [0],
        )
        self.assertIsInstance(subformula, mtl.Eventually)


if __name__ == "__main__":
    unittest.main()
