"""Unit tests for formula context operations."""

import unittest

from src.logic import ctx, mtl, parser


class TestSplitFormula(unittest.TestCase):
    def test_deeply_nested_and_or(self) -> None:
        expected_context = ctx.AndLeft(
            ctx.OrRight(mtl.Prop("a"), ctx.Not(ctx.Hole())),
            mtl.Eventually(mtl.Prop("c")),
        )
        indices = ctx.get_de_bruijn(expected_context)
        self.assertEqual(indices, [0, 1, 0])
        expected_subf = parser.parse_mtl("G b")
        expected_f = parser.parse_mtl("(a | !G b) & F c")
        result_f = ctx.substitute(expected_context, expected_subf)
        self.assertEqual(expected_f, result_f)
        result_context, result_subf = ctx.split_formula(expected_f, [0, 1, 0])
        self.assertEqual(expected_context, result_context)
        self.assertEqual(expected_subf, result_subf)

    def test_deeply_nested_until_and(self) -> None:
        expected_context = ctx.UntilLeft(
            ctx.AndRight(mtl.Prop("a"), ctx.Hole()),
            mtl.Or(mtl.Prop("c"), mtl.Prop("d")),
            (0, 5),
        )
        indices = ctx.get_de_bruijn(expected_context)
        self.assertEqual(indices, [0, 1])
        expected_subf = parser.parse_mtl("(F b) U[0,3] e")
        expected_f = parser.parse_mtl("(a & ((F b) U[0,3] e)) U[0,5] (c | d)")
        result_f = ctx.substitute(expected_context, expected_subf)
        self.assertEqual(expected_f, result_f)
        context, subf = ctx.split_formula(result_f, indices)
        self.assertEqual(expected_context, context)
        self.assertEqual(expected_subf, subf)

    def test_deeply_nested_temporal_and_complex_subformula(self) -> None:
        expected_context = ctx.Eventually(
            ctx.AndLeft(
                ctx.UntilRight(mtl.Prop("a"), ctx.Hole(), (1, 3)),
                mtl.Or(mtl.Prop("b"), mtl.Prop("c")),
            ),
            (0, 5),
        )
        indices = ctx.get_de_bruijn(expected_context)
        self.assertEqual(indices, [0, 0, 1])
        expected_subf = parser.parse_mtl("G ((c U[2,4] F d) & (e | f))")
        expected_f = parser.parse_mtl(
            "F[0,5] ((a U[1,3] G ((c U[2,4] F d) & (e | f))) & (b | c))",
        )
        result_f = ctx.substitute(expected_context, expected_subf)
        self.assertEqual(expected_f, result_f)
        context, subf = ctx.split_formula(expected_f, indices)
        self.assertEqual(expected_context, context)
        self.assertEqual(expected_subf, subf)


class TestPartialNNFContext(unittest.TestCase):
    def test_complex_boolean_operators_nnf(self) -> None:
        """Test NNF conversion for complex nested boolean operators."""
        context = ctx.Not(
            ctx.OrRight(
                mtl.Prop("p"),
                ctx.AndLeft(ctx.Not(ctx.Hole()), mtl.Prop("q")),
            ),
        )
        expected_context = ctx.AndRight(
            mtl.Not(mtl.Prop("p")),
            ctx.OrLeft(ctx.Hole(), mtl.Not(mtl.Prop("q"))),
        )
        result_context, polarity = ctx.partial_nnf_ctx(context)
        self.assertEqual(result_context, expected_context)
        self.assertTrue(polarity)

    def test_complex_implication_nnf(self) -> None:
        """Test NNF conversion for nested implication contexts."""
        context = ctx.Not(
            ctx.Not(
                ctx.ImpliesLeft(
                    ctx.Eventually(ctx.Not(ctx.Hole()), (1, 5)),
                    mtl.Always(mtl.Prop("r")),
                ),
            ),
        )
        expected_context = ctx.OrLeft(
            ctx.Always(ctx.Hole(), (1, 5)),
            mtl.Always(mtl.Prop("r")),
        )
        result_context, polarity = ctx.partial_nnf_ctx(context)
        self.assertEqual(result_context, expected_context)
        self.assertTrue(polarity)

    def test_complex_temporal_operators_nnf(self) -> None:
        """Test NNF conversion for complex temporal operator combinations."""
        context = ctx.Not(
            ctx.Eventually(
                ctx.AndLeft(
                    ctx.Always(ctx.Hole(), (2, 8)),
                    mtl.Eventually(mtl.Prop("s"), (0, 3)),
                ),
                (0, None),
            ),
        )
        expected_context = ctx.Always(
            ctx.OrLeft(
                ctx.Eventually(ctx.Hole(), (2, 8)),
                mtl.Not(mtl.Eventually(mtl.Prop("s"), (0, 3))),
            ),
            (0, None),
        )
        result_context, polarity = ctx.partial_nnf_ctx(context)
        self.assertEqual(result_context, expected_context)
        self.assertFalse(polarity)


class TestPartialNNF(unittest.TestCase):
    def test_pnnf_subformula(self) -> None:
        context = ctx.Not(ctx.Hole())
        subformula = parser.parse_mtl("G[1,5] a")
        assert isinstance(subformula, mtl.Temporal)
        expected_subformula = parser.parse_mtl("F[1,5] !a")
        result_context, result_subformula = ctx.partial_nnf(context, subformula)
        self.assertEqual(result_subformula, expected_subformula)
        self.assertEqual(result_context, ctx.Hole())


class TestToString(unittest.TestCase):
    def test_hole(self) -> None:
        self.assertEqual(str(ctx.Hole()), "[-]")

    def test_not(self) -> None:
        self.assertEqual(str(ctx.Not(ctx.Hole())), "!([-])")

    def test_and_left(self) -> None:
        self.assertEqual(
            str(ctx.AndLeft(ctx.Hole(), mtl.Prop("b"))),
            "([-] & b)",
        )

    def test_and_right(self) -> None:
        self.assertEqual(
            str(ctx.AndRight(mtl.Prop("a"), ctx.Hole())),
            "(a & [-])",
        )

    def test_or_left(self) -> None:
        self.assertEqual(
            str(ctx.OrLeft(ctx.Hole(), mtl.Prop("b"))),
            "([-] | b)",
        )

    def test_or_right(self) -> None:
        self.assertEqual(
            str(ctx.OrRight(mtl.Prop("a"), ctx.Hole())),
            "(a | [-])",
        )

    def test_implies_left(self) -> None:
        self.assertEqual(
            str(ctx.ImpliesLeft(ctx.Hole(), mtl.Prop("b"))),
            "([-] -> b)",
        )

    def test_implies_right(self) -> None:
        self.assertEqual(
            str(ctx.ImpliesRight(mtl.Prop("a"), ctx.Hole())),
            "(a -> [-])",
        )

    def test_eventually(self) -> None:
        self.assertEqual(
            str(ctx.Eventually(ctx.Hole(), (1, 3))),
            "F[1, 3] ([-])",
        )

    def test_always_default_interval(self) -> None:
        # (0, None) with low=0 renders as empty string via fmt_interval
        self.assertEqual(str(ctx.Always(ctx.Hole(), (0, None))), "G ([-])")

    def test_always_bounded(self) -> None:
        self.assertEqual(str(ctx.Always(ctx.Hole(), (1, 5))), "G[1, 5] ([-])")

    def test_until_left(self) -> None:
        self.assertEqual(
            str(ctx.UntilLeft(ctx.Hole(), mtl.Prop("b"), (0, 5))),
            "([-] U[0, 5] b)",
        )

    def test_until_right(self) -> None:
        self.assertEqual(
            str(ctx.UntilRight(mtl.Prop("a"), ctx.Hole(), (0, 5))),
            "(a U[0, 5] [-])",
        )

    def test_release_left(self) -> None:
        self.assertEqual(
            str(ctx.ReleaseLeft(ctx.Hole(), mtl.Prop("b"), (1, 4))),
            "([-] R[1, 4] b)",
        )

    def test_release_right(self) -> None:
        self.assertEqual(
            str(ctx.ReleaseRight(mtl.Prop("a"), ctx.Hole(), (1, 4))),
            "(a R[1, 4] [-])",
        )

    def test_next(self) -> None:
        self.assertEqual(str(ctx.Next(ctx.Hole())), "X ([-])")

    def test_repr_matches_str(self) -> None:
        c = ctx.AndLeft(ctx.Not(ctx.Hole()), mtl.Prop("b"))
        self.assertEqual(repr(c), str(c))

    def test_nested(self) -> None:
        c = ctx.Always(ctx.OrLeft(ctx.Hole(), mtl.Prop("q")), (0, 2))
        self.assertEqual(str(c), "G[0, 2] (([-] | q))")


class TestSubstituteAdditional(unittest.TestCase):
    """Cover substitute branches not exercised by TestSplitFormula."""

    def test_or_left(self) -> None:
        f = mtl.Prop("x")
        result = ctx.substitute(ctx.OrLeft(ctx.Hole(), mtl.Prop("b")), f)
        self.assertEqual(result, mtl.Or(f, mtl.Prop("b")))

    def test_implies_left(self) -> None:
        f = mtl.Prop("x")
        result = ctx.substitute(ctx.ImpliesLeft(ctx.Hole(), mtl.Prop("b")), f)
        self.assertEqual(result, mtl.Implies(f, mtl.Prop("b")))

    def test_implies_right(self) -> None:
        f = mtl.Prop("x")
        result = ctx.substitute(ctx.ImpliesRight(mtl.Prop("a"), ctx.Hole()), f)
        self.assertEqual(result, mtl.Implies(mtl.Prop("a"), f))

    def test_next(self) -> None:
        f = mtl.Prop("x")
        result = ctx.substitute(ctx.Next(ctx.Hole()), f)
        self.assertEqual(result, mtl.Next(f))

    def test_always(self) -> None:
        f = mtl.Prop("x")
        result = ctx.substitute(ctx.Always(ctx.Hole(), (0, 3)), f)
        self.assertEqual(result, mtl.Always(f, (0, 3)))

    def test_release_left(self) -> None:
        f = mtl.Prop("x")
        result = ctx.substitute(
            ctx.ReleaseLeft(ctx.Hole(), mtl.Prop("b"), (0, 2)),
            f,
        )
        self.assertEqual(result, mtl.Release(f, mtl.Prop("b"), (0, 2)))

    def test_release_right(self) -> None:
        f = mtl.Prop("x")
        result = ctx.substitute(
            ctx.ReleaseRight(mtl.Prop("a"), ctx.Hole(), (0, 2)),
            f,
        )
        self.assertEqual(result, mtl.Release(mtl.Prop("a"), f, (0, 2)))


class TestSplitFormulaAdditional(unittest.TestCase):
    """Cover split_formula branches not exercised by TestSplitFormula."""

    def test_implies_left(self) -> None:
        formula = parser.parse_mtl("(F a) -> G b")
        result_ctx, result_subf = ctx.split_formula(formula, [0])
        self.assertIsInstance(result_ctx, ctx.ImpliesLeft)
        self.assertIsInstance(result_subf, mtl.Eventually)

    def test_implies_right(self) -> None:
        formula = parser.parse_mtl("G a -> (F b)")
        result_ctx, result_subf = ctx.split_formula(formula, [1])
        self.assertIsInstance(result_ctx, ctx.ImpliesRight)
        self.assertIsInstance(result_subf, mtl.Eventually)

    def test_release_left(self) -> None:
        formula = parser.parse_mtl("(F a) R[0,3] b")
        result_ctx, result_subf = ctx.split_formula(formula, [0])
        self.assertIsInstance(result_ctx, ctx.ReleaseLeft)
        self.assertIsInstance(result_subf, mtl.Eventually)

    def test_release_right(self) -> None:
        formula = parser.parse_mtl("a R[0,3] (G b)")
        result_ctx, result_subf = ctx.split_formula(formula, [1])
        self.assertIsInstance(result_ctx, ctx.ReleaseRight)
        self.assertIsInstance(result_subf, mtl.Always)

    def test_or_left(self) -> None:
        formula = parser.parse_mtl("(F a) | G b")
        result_ctx, result_subf = ctx.split_formula(formula, [0])
        self.assertIsInstance(result_ctx, ctx.OrLeft)
        self.assertIsInstance(result_subf, mtl.Eventually)

    def test_index_into_prop_raises(self) -> None:
        formula = parser.parse_mtl("a")
        with self.assertRaises(mtl.DeBruijnIndexError):
            ctx.split_formula(formula, [0])

    def test_not_wrong_index_raises(self) -> None:
        formula = parser.parse_mtl("! F a")
        with self.assertRaises(mtl.DeBruijnIndexError):
            ctx.split_formula(formula, [1])

    def test_and_invalid_index_raises(self) -> None:
        formula = parser.parse_mtl("F a & G b")
        with self.assertRaises(mtl.DeBruijnIndexError):
            ctx.split_formula(formula, [2])

    def test_eventually_wrong_index_raises(self) -> None:
        formula = parser.parse_mtl("F a")
        with self.assertRaises(mtl.DeBruijnIndexError):
            ctx.split_formula(formula, [1])

    def test_always_wrong_index_raises(self) -> None:
        formula = parser.parse_mtl("G a")
        with self.assertRaises(mtl.DeBruijnIndexError):
            ctx.split_formula(formula, [1])

    def test_until_wrong_index_raises(self) -> None:
        formula = parser.parse_mtl("a U b")
        with self.assertRaises(mtl.DeBruijnIndexError):
            ctx.split_formula(formula, [2])

    def test_release_wrong_index_raises(self) -> None:
        formula = parser.parse_mtl("a R b")
        with self.assertRaises(mtl.DeBruijnIndexError):
            ctx.split_formula(formula, [2])


class TestPartialNNFCtxAdditional(unittest.TestCase):
    """Cover partial_nnf_ctx branches for Right-variant and additional contexts."""

    def test_and_right(self) -> None:
        c = ctx.AndRight(mtl.Prop("a"), ctx.Hole())
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(result, ctx.AndRight(mtl.Prop("a"), ctx.Hole()))
        self.assertTrue(polarity)

    def test_or_right(self) -> None:
        c = ctx.OrRight(mtl.Prop("a"), ctx.Hole())
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(result, ctx.OrRight(mtl.Prop("a"), ctx.Hole()))
        self.assertTrue(polarity)

    def test_implies_right_becomes_or_right(self) -> None:
        c = ctx.ImpliesRight(mtl.Prop("a"), ctx.Hole())
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(
            result,
            ctx.OrRight(mtl.Not(mtl.Prop("a")), ctx.Hole()),
        )
        self.assertTrue(polarity)

    def test_until_right(self) -> None:
        c = ctx.UntilRight(mtl.Prop("a"), ctx.Hole(), (0, 3))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(
            result,
            ctx.UntilRight(mtl.Prop("a"), ctx.Hole(), (0, 3)),
        )
        self.assertTrue(polarity)

    def test_release_left(self) -> None:
        c = ctx.ReleaseLeft(ctx.Hole(), mtl.Prop("b"), (0, 3))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(
            result,
            ctx.ReleaseLeft(ctx.Hole(), mtl.Prop("b"), (0, 3)),
        )
        self.assertTrue(polarity)

    def test_release_right(self) -> None:
        c = ctx.ReleaseRight(mtl.Prop("a"), ctx.Hole(), (0, 3))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(
            result,
            ctx.ReleaseRight(mtl.Prop("a"), ctx.Hole(), (0, 3)),
        )
        self.assertTrue(polarity)

    def test_next(self) -> None:
        c = ctx.Next(ctx.Hole())
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(result, ctx.Next(ctx.Hole()))
        self.assertTrue(polarity)

    def test_eventually(self) -> None:
        c = ctx.Eventually(ctx.Hole(), (1, 5))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(result, ctx.Eventually(ctx.Hole(), (1, 5)))
        self.assertTrue(polarity)

    def test_always(self) -> None:
        c = ctx.Always(ctx.Hole(), (0, 2))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(result, ctx.Always(ctx.Hole(), (0, 2)))
        self.assertTrue(polarity)


class TestPartialNNFCtxNegRightVariants(unittest.TestCase):
    """Cover _partial_nnf_ctx_neg for Right-variant contexts via Not wrapping."""

    def test_not_and_right(self) -> None:
        c = ctx.Not(ctx.AndRight(mtl.Prop("a"), ctx.Hole()))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(
            result,
            ctx.OrRight(mtl.Not(mtl.Prop("a")), ctx.Hole()),
        )
        self.assertFalse(polarity)

    def test_not_or_right(self) -> None:
        c = ctx.Not(ctx.OrRight(mtl.Prop("a"), ctx.Hole()))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(
            result,
            ctx.AndRight(mtl.Not(mtl.Prop("a")), ctx.Hole()),
        )
        self.assertFalse(polarity)

    def test_not_implies_right(self) -> None:
        c = ctx.Not(ctx.ImpliesRight(mtl.Prop("a"), ctx.Hole()))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(result, ctx.AndRight(mtl.Prop("a"), ctx.Hole()))
        self.assertFalse(polarity)

    def test_not_until_right(self) -> None:
        c = ctx.Not(ctx.UntilRight(mtl.Prop("a"), ctx.Hole(), (0, 3)))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(
            result,
            ctx.ReleaseRight(mtl.Not(mtl.Prop("a")), ctx.Hole(), (0, 3)),
        )
        self.assertFalse(polarity)

    def test_not_release_left(self) -> None:
        c = ctx.Not(ctx.ReleaseLeft(ctx.Hole(), mtl.Prop("b"), (0, 3)))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(
            result,
            ctx.UntilLeft(ctx.Hole(), mtl.Not(mtl.Prop("b")), (0, 3)),
        )
        self.assertFalse(polarity)

    def test_not_release_right(self) -> None:
        c = ctx.Not(ctx.ReleaseRight(mtl.Prop("a"), ctx.Hole(), (0, 3)))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(
            result,
            ctx.UntilRight(mtl.Not(mtl.Prop("a")), ctx.Hole(), (0, 3)),
        )
        self.assertFalse(polarity)

    def test_not_next(self) -> None:
        c = ctx.Not(ctx.Next(ctx.Hole()))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(result, ctx.Next(ctx.Hole()))
        self.assertFalse(polarity)

    def test_not_eventually_becomes_always(self) -> None:
        c = ctx.Not(ctx.Eventually(ctx.Hole(), (1, 5)))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(result, ctx.Always(ctx.Hole(), (1, 5)))
        self.assertFalse(polarity)

    def test_not_always_becomes_eventually(self) -> None:
        c = ctx.Not(ctx.Always(ctx.Hole(), (0, 2)))
        result, polarity = ctx.partial_nnf_ctx(c)
        self.assertEqual(result, ctx.Eventually(ctx.Hole(), (0, 2)))
        self.assertFalse(polarity)


class TestPartialNNFAdditional(unittest.TestCase):
    """Cover partial_nnf paths not exercised by TestPartialNNF."""

    def test_positive_polarity_returns_subformula_unchanged(self) -> None:
        subformula = parser.parse_mtl("F[0,3] a")
        assert isinstance(subformula, mtl.Temporal)
        result_ctx, result_subf = ctx.partial_nnf(ctx.Hole(), subformula)
        self.assertEqual(result_ctx, ctx.Hole())
        self.assertEqual(result_subf, subformula)

    def test_negative_polarity_until_becomes_release(self) -> None:
        subformula = parser.parse_mtl("a U[1,4] b")
        assert isinstance(subformula, mtl.Temporal)
        _result_ctx, result_subf = ctx.partial_nnf(
            ctx.Not(ctx.Hole()),
            subformula,
        )
        expected = mtl.Release(
            mtl.Not(mtl.Prop("a")),
            mtl.Not(mtl.Prop("b")),
            (1, 4),
        )
        self.assertEqual(result_subf, expected)

    def test_negative_polarity_release_becomes_until(self) -> None:
        subformula = parser.parse_mtl("a R[1,4] b")
        assert isinstance(subformula, mtl.Temporal)
        _result_ctx, result_subf = ctx.partial_nnf(
            ctx.Not(ctx.Hole()),
            subformula,
        )
        expected = mtl.Until(
            mtl.Not(mtl.Prop("a")),
            mtl.Not(mtl.Prop("b")),
            (1, 4),
        )
        self.assertEqual(result_subf, expected)

    def test_negative_polarity_eventually_becomes_always(self) -> None:
        subformula = parser.parse_mtl("F[2,5] a")
        assert isinstance(subformula, mtl.Temporal)
        _result_ctx, result_subf = ctx.partial_nnf(
            ctx.Not(ctx.Hole()),
            subformula,
        )
        expected = mtl.Always(mtl.Not(mtl.Prop("a")), (2, 5))
        self.assertEqual(result_subf, expected)


if __name__ == "__main__":
    unittest.main()
