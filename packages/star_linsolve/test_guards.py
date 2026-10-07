"""Guard tests of star_linsolve written by the reviewer: an independent oracle (the determinant as a sum over
permutations in exact rationals, Cramer's rule and the adjugate: no elimination anywhere), exact identities, the
places where a row exchange or a rounding could go wrong unnoticed, the limits and every refusal by name."""
import itertools
import random
from fractions import Fraction

import pytest

import star_linsolve as sl


def leibniz(m):
    """Determinant as the signed sum over all permutations, exact."""
    n = len(m)
    total = Fraction(0)
    for perm in itertools.permutations(range(n)):
        inversions = sum(1 for i in range(n) for j in range(i + 1, n) if perm[i] > perm[j])
        term = Fraction(-1 if inversions % 2 else 1)
        for i in range(n):
            term *= Fraction(m[i][perm[i]])
        total += term
    return total


def random_matrix(rnd, n, zeros=False):
    return [[0.0 if zeros and rnd.random() < 0.35 else rnd.uniform(-9, 9) for _ in range(n)] for _ in range(n)]


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6])
def test_determinant_solution_and_inverse_against_permutation_sums(n):
    rnd = random.Random(40 + n)
    for trial in range(12):
        a = random_matrix(rnd, n, zeros=trial % 2 == 1)             # zeros force row exchanges
        b = [rnd.uniform(-9, 9) for _ in range(n)]
        d = leibniz(a)
        assert sl.det(a) == float(d)
        if d == 0:
            with pytest.raises(ValueError, match="singular"):
                sl.solve(a, b)
            continue
        cramer = tuple(float(leibniz([row[:k] + [b[i]] + row[k + 1:] for i, row in enumerate(a)]) / d) for k in range(n))
        assert sl.solve(a, b) == cramer
        if n > 1:
            adjugate = tuple(tuple(float((-1) ** (i + j) * leibniz([r[:i] + r[i + 1:] for k, r in enumerate(a) if k != j]) / d) for j in range(n)) for i in range(n))
            assert sl.inverse(a) == adjugate
        else:
            assert sl.inverse(a) == ((float(1 / Fraction(a[0][0])),),)


def test_small_cases_by_hand():
    assert sl.det([[3]]) == 3.0 and sl.solve([[5]], [10]) == (2.0,) and sl.inverse([[4]]) == ((0.25,),)
    assert sl.det([[1, 2], [3, 4]]) == -2.0 and sl.inverse([[1, 2], [3, 4]]) == ((-2.0, 1.0), (1.5, -0.5))
    assert sl.inverse([[4, 7], [2, 6]]) == ((0.6, -0.7), (-0.2, 0.4)) and sl.solve([[2, 1], [1, 3]], [3, 5]) == (0.8, 1.4)
    assert sl.det([[2, 0, 0], [0, 3, 0], [0, 0, 4]]) == 24.0 and sl.det([[2, 5, 7], [0, 3, 9], [0, 0, 4]]) == 24.0 and sl.det([[2, 0, 0], [5, 3, 0], [7, 9, 4]]) == 24.0
    assert sl.det([[1, 2, 3], [4, 5, 6], [7, 8, 10]]) == -3.0 and sl.solve([[1, 2, 3], [4, 5, 6], [7, 8, 10]], [6, 15, 25]) == (1.0, 1.0, 1.0)
    assert sl.inverse([[1, 2, 3], [4, 5, 6], [7, 8, 10]]) == ((-2 / 3, -4 / 3, 1.0), (-2 / 3, 11 / 3, -2.0), (1.0, -2.0, 1.0))
    second_difference = ((2, -1, 0), (-1, 2, -1), (0, -1, 2))                              # tuples are accepted
    assert sl.det(second_difference) == 4.0 and sl.inverse(second_difference) == ((0.75, 0.5, 0.25), (0.5, 1.0, 0.5), (0.25, 0.5, 0.75))
    assert sl.solve(second_difference, (1, 0, 1)) == (1.0, 1.0, 1.0)


def test_hilbert_matrix_of_order_3_scaled_to_integers():
    a = [[60, 30, 20], [30, 20, 15], [20, 15, 12]]
    assert sl.det(a) == 100.0                                                              # 60^3 / 2160
    assert sl.inverse(a) == ((0.15, -0.6, 0.5), (-0.6, 3.2, -3.0), (0.5, -3.0, 3.0))       # the published integer inverse / 60
    assert sl.solve(a, [110, 65, 47]) == (1.0, 1.0, 1.0)
    floats = [[1 / (i + j + 1) for j in range(3)] for i in range(3)]
    assert sl.det(floats) == pytest.approx(1 / 2160, rel=1e-13)
    published = ((9, -36, 30), (-36, 192, -180), (30, -180, 180))
    assert all(got == pytest.approx(want, rel=1e-12) for row, ref in zip(sl.inverse(floats), published) for got, want in zip(row, ref))
    order4 = [[1 / (i + j + 1) for j in range(4)] for i in range(4)]
    assert sl.det(order4) == pytest.approx(1 / 6048000, rel=1e-11)


def test_row_exchanges_keep_the_sign_right():
    assert sl.det([[0, 1], [1, 0]]) == -1.0 and sl.det([[0, 2], [3, 0]]) == -6.0 and sl.solve([[0, 2], [3, 0]], [4, 9]) == (3.0, 2.0)
    assert sl.inverse([[0, 2], [3, 0]]) == ((0.0, 1 / 3), (0.5, 0.0))
    cyclic = [[0, 1, 0], [0, 0, 1], [1, 0, 0]]                                              # an even permutation: two exchanges
    assert sl.det(cyclic) == 1.0 and sl.inverse(cyclic) == ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) and sl.solve(cyclic, [7, 8, 9]) == (9.0, 7.0, 8.0)
    reversal = [[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]]                     # two exchanges as well
    assert sl.det(reversal) == 1.0 and sl.det(reversal[:3] + [[2, 0, 0, 0]]) == 2.0 and sl.det([reversal[1], reversal[0]] + reversal[2:]) == -1.0
    rnd = random.Random(8)
    a = random_matrix(rnd, 5)
    d = sl.det(a)
    assert sl.det([a[1], a[0]] + a[2:]) == -d and sl.det([a[4]] + a[1:4] + [a[0]]) == -d
    assert sl.det([[2.0 * v for v in a[0]]] + a[1:]) == 2.0 * d                            # doubling a row is exact
    assert sl.det([list(col) for col in zip(*a)]) == d                                     # the transpose
    assert sl.det([a[0], a[0]] + a[2:]) == 0.0 and sl.det(a[:4] + [[x + y for x, y in zip(a[0], a[1])]]) == pytest.approx(0.0, abs=1e-9)


def test_singular_is_decided_exactly():
    for a in ([[1, 2], [2, 4]], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[0.1, 0.2], [0.3, 0.6]], [[0]], [[0, 0], [0, 0]], [[1, 2], [0, 0]], [[1, 0], [1, 0]]):
        assert sl.det(a) == 0.0
        with pytest.raises(ValueError, match="the matrix is singular"):
            sl.solve(a, [1] * len(a))
        with pytest.raises(ValueError, match="the matrix is singular"):
            sl.inverse(a)
    e = 2.0 ** -52
    near = [[1, 1], [1, 1 + e]]
    assert sl.det(near) == e and sl.solve(near, [2, 2]) == (2.0, 0.0) and sl.solve(near, [2, 2 + 2 * e]) == (0.0, 2.0)
    assert sl.inverse(near) == ((2.0 ** 52 + 1, -2.0 ** 52), (-2.0 ** 52, 2.0 ** 52))
    assert sl.det([[1e-200, 0], [0, 1e-200]]) == 0.0                                       # 1e-400 underflows ...
    regular = sl.inverse([[1e-200, 0], [0, 1e-200]])                                       # ... but the matrix is regular
    assert regular[0][0] == pytest.approx(1e200, rel=1e-15) and regular[0][1] == 0.0 and regular[1][1] == regular[0][0]
    assert sl.solve([[1e-200, 0], [0, 1e-200]], [1e-200, 3e-200]) == (1.0, 3.0)


def test_results_are_the_nearest_floats_and_identities_hold():
    third = sl.solve([[3]], [1])
    assert third == (1 / 3,) and sl.inverse([[3]]) == ((1 / 3,),) and sl.inverse([[0.1]]) == ((float(1 / Fraction(0.1)),),)
    assert sl.det([[0.1, 0.2], [0.3, 0.4]]) == float(Fraction(0.1) * Fraction(0.4) - Fraction(0.2) * Fraction(0.3))
    assert sl.det([[1e100, 0], [0, 1e100]]) == 1e200 and sl.det([[1e100, 1e100], [1e100, 1e100]]) == 0.0
    assert sl.det([[1 + 2.0 ** -30, 1], [1, 1 - 2.0 ** -30]]) == -(2.0 ** -60)             # floats: 1 - 2^-60 rounds to 1, and the float product gives 0
    identity = [[float(i == j) for j in range(sl.MAX_SIZE)] for i in range(sl.MAX_SIZE)]
    assert sl.det(identity) == 1.0 and sl.inverse(identity) == tuple(tuple(row) for row in identity) and sl.solve(identity, list(range(20))) == tuple(float(k) for k in range(20))
    rnd = random.Random(21)
    a = random_matrix(rnd, 7)
    for i in range(7):
        a[i][i] += 30.0
    b = [rnd.uniform(-9, 9) for _ in range(7)]
    x = sl.solve(a, b)
    assert all(sum(p * q for p, q in zip(row, x)) == pytest.approx(v, abs=1e-12) for row, v in zip(a, b))
    inv = sl.inverse(a)
    assert all(sum(a[i][k] * inv[k][j] for k in range(7)) == pytest.approx(float(i == j), abs=1e-13) for i in range(7) for j in range(7))
    assert all(got == pytest.approx(want, rel=1e-12) for row, ref in zip(sl.inverse(inv), a) for got, want in zip(row, ref))
    assert x == pytest.approx(tuple(sum(p * q for p, q in zip(row, b)) for row in inv), rel=1e-12)
    assert all(isinstance(v, float) for v in x) and isinstance(sl.det([[1]]), float) and isinstance(inv, tuple) and isinstance(inv[0], tuple) and isinstance(x, tuple)


def test_limits():
    assert (sl.MAX_SIZE, sl.BIG, sl.__version__, sl.__all__) == (20, 1e100, "0.1.0", ["det", "solve", "inverse"])
    too_big = [[float(i == j) for j in range(21)] for i in range(21)]
    for call in (lambda: sl.det(too_big), lambda: sl.inverse(too_big), lambda: sl.solve(too_big, [0.0] * 21), lambda: sl.det([]), lambda: sl.det(())):
        with pytest.raises(ValueError, match="a must be a list or tuple of 1 to 20 rows"):
            call()
    assert sl.det([[1e100]]) == 1e100 and sl.det([[-1e100]]) == -1e100 and sl.solve([[1]], [1e100]) == (1e100,)
    for call in (lambda: sl.det([[1e100 if i == j else 0.0 for j in range(4)] for i in range(4)]), lambda: sl.solve([[1e-300]], [1e100]), lambda: sl.inverse([[5e-324]])):
        with pytest.raises(ValueError, match="too large for a float"):
            call()


def test_refusals_name_the_argument():
    for bad in ("ab", None, 3.0, {1.0}, iter([[1.0]])):
        with pytest.raises(ValueError, match="a must be a list or tuple of 1 to 20 rows"):
            sl.det(bad)
    for bad in ([1.0, 2.0], [[1.0, 2.0], [3.0]], [[1.0, 2.0], "ab"], [[1.0, 2.0], [3.0, 4.0, 5.0]], [[1.0, 2.0]], [[1.0], [2.0]], [[1.0, 2.0], None]):
        with pytest.raises(ValueError, match="a must be square"):
            sl.inverse(bad)
    for bad in (True, False, "1", None, 1j, float("nan"), float("inf"), float("-inf"), 1.0000001e100, -1.0000001e100, 10 ** 400):
        with pytest.raises(ValueError, match="a must hold finite real numbers"):
            sl.det([[1.0, bad], [0.0, 1.0]])
        with pytest.raises(ValueError, match="b must hold finite real numbers"):
            sl.solve([[1.0, 0.0], [0.0, 1.0]], [1.0, bad])
    for bad in ([1.0], [1.0, 2.0, 3.0], "ab", None, 2.0, []):
        with pytest.raises(ValueError, match="b must be a list or tuple of 2 numbers"):
            sl.solve([[1.0, 0.0], [0.0, 1.0]], bad)
