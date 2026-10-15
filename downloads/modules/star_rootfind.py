"""star_rootfind - bracketed roots of a real function, to the last float (S.T.A.R., 2026-10-07).
Standard library only.

  find_root(f, a, b)            the point of [a, b], a < b, where f changes sign
  find_roots(f, a, b, pieces)   every change of sign found by splitting [a, b] into equal pieces: a sorted tuple
`find_root` needs f(a) and f(b) of opposite sign (or one of them zero). It bisects over the FLOATS, not over the
reals: the interval is halved in the number of floats it contains, so after at most 64 evaluations the two ends are
neighbouring floats (or f is exactly zero at one point) and nothing closer exists. There is no tolerance to choose
and no way to stop early or to run forever. The end returned is the one where |f| is smaller (the lower on a tie).
What is found is a change of sign of f AS COMPUTED: a true root for a continuous function, a jump for a
discontinuous one (a step function); at a pole such as 1/x the values overflow and the search ends in a refusal.
The result is within one float of where the computed f changes sign, which for an f evaluated with rounding
error e is within about e / |f'| of the true root: x*x - 2 on [0, 2] gives 1.414213562373095, the float below
sqrt(2) rounded, because x*x - 2 has the same size and opposite signs on the two neighbours.
Refusals (ValueError): f not callable; a or b not a finite real number within +-1e300 (booleans refused); a >= b;
pieces not an integer from 1 to 100000; f(a) and f(b) of the same sign; a value of f that is not a finite real number.
An exception raised by f itself is not caught: it reaches the caller unchanged.
"""
from __future__ import annotations

import math
import numbers
import struct
from typing import Callable, Tuple

__all__ = ["find_root", "find_roots"]
__version__ = "0.1.0"

BIG = 1e300
MAX_PIECES = 100000


def _real(v, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -BIG <= float(v) <= BIG      # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number within +-1e300")
    return float(v)


def _ends(f, a, b) -> Tuple[float, float]:
    if not callable(f):
        raise ValueError("f must be callable")
    lo, hi = _real(a, "a"), _real(b, "b")
    if not lo < hi:
        raise ValueError("a must be smaller than b")
    return lo, hi


def _at(f: Callable[[float], float], x: float) -> float:
    y = f(x)
    if isinstance(y, bool) or not isinstance(y, numbers.Real) or not math.isfinite(y):
        raise ValueError("f must return a finite real number")
    return float(y)


def _rank(x: float) -> int:
    """Position of a float among all floats, in increasing order (-0.0 and 0.0 share a position)."""
    n = struct.unpack("<q", struct.pack("<d", x))[0]
    return n if n >= 0 else -(n & 0x7FFFFFFFFFFFFFFF)


def _unrank(n: int) -> float:
    return struct.unpack("<d", struct.pack("<q", n))[0] if n >= 0 else -struct.unpack("<d", struct.pack("<q", -n))[0]


def _positive(y: float) -> bool:
    return y > 0.0


def _bisect(f: Callable[[float], float], lo: float, hi: float, flo: float, fhi: float) -> float:
    """lo < hi with flo and fhi of opposite sign, neither zero."""
    a, b = _rank(lo), _rank(hi)
    while b - a > 1:
        mid = (a + b) // 2
        fm = _at(f, _unrank(mid))
        if fm == 0.0:
            return _unrank(mid)
        if _positive(fm) == _positive(flo):
            a, flo = mid, fm
        else:
            b, fhi = mid, fm
    return _unrank(a) if abs(flo) <= abs(fhi) else _unrank(b)          # _unrank never returns -0.0


def find_root(f: Callable[[float], float], a: float, b: float) -> float:
    lo, hi = _ends(f, a, b)
    flo = _at(f, lo)
    if flo == 0.0:
        return lo + 0.0
    fhi = _at(f, hi)
    if fhi == 0.0:
        return hi + 0.0
    if _positive(flo) == _positive(fhi):
        raise ValueError("f(a) and f(b) have the same sign: no change of sign is bracketed")
    return _bisect(f, lo, hi, flo, fhi)


def find_roots(f: Callable[[float], float], a: float, b: float, pieces: int) -> Tuple[float, ...]:
    lo, hi = _ends(f, a, b)
    if isinstance(pieces, bool) or not isinstance(pieces, numbers.Integral) or not 1 <= pieces <= MAX_PIECES:
        raise ValueError("pieces must be an integer from 1 to 100000")
    n = int(pieces)
    edges = sorted({lo + (hi - lo) * (k / n) for k in range(n)} | {hi})         # distinct: a tiny interval has fewer floats than pieces
    values = [_at(f, x) for x in edges]
    found = []
    for k, (x, y) in enumerate(zip(edges, values)):
        if y == 0.0:
            found.append(x + 0.0)
        elif k + 1 < len(edges) and values[k + 1] != 0.0 and _positive(y) != _positive(values[k + 1]):
            found.append(_bisect(f, x, edges[k + 1], y, values[k + 1]))
    return tuple(found)
