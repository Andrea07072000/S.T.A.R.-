"""star_interp - polynomial (Lagrange) interpolation through tabulated points (S.T.A.R., 2026-10-06).
Standard library only.

  lagrange(xs, ys, x)             value at x of the polynomial of degree len(xs) - 1 through the points (xs[i], ys[i])
  lagrange_derivative(xs, ys, x)  its first derivative at x
  lagrange_weights(xs)            the barycentric weights of the nodes (reusable, mostly for inspection)
This is how tabulated ephemerides are read between their epochs (SP3 and CCSDS OEM files are interpolated with
Lagrange polynomials of a few points around the epoch wanted). The barycentric form is used: it is stable where the
textbook product formula is not, and at a node it returns the tabulated value exactly.
The nodes need not be equally spaced or sorted. Interpolation only: an x outside [min(xs), max(xs)] is refused,
because a polynomial through n points says nothing reliable outside them.
Refusals (ValueError): xs or ys not a list or tuple; fewer than 2 or more than 20 points; lengths that differ; any
element or x that is not a finite real number (booleans included) or exceeds 1e150 in absolute value; two equal
nodes; x outside the range of the nodes.
"""
from __future__ import annotations

import math
import numbers
from typing import List, Sequence, Tuple

__all__ = ["lagrange", "lagrange_derivative", "lagrange_weights"]
__version__ = "0.1.0"

MIN_POINTS, MAX_POINTS = 2, 20
BIG = 1e150


def _real(v, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -BIG <= float(v) <= BIG       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number within +-1e150")
    return float(v)


def _nodes(xs) -> List[float]:
    if not isinstance(xs, (list, tuple)) or not MIN_POINTS <= len(xs) <= MAX_POINTS:
        raise ValueError("xs must be a list or tuple of 2 to 20 nodes")
    nodes = [_real(v, "a node") for v in xs]
    if len(set(nodes)) != len(nodes):
        raise ValueError("the nodes must be distinct")
    return nodes


def _table(xs, ys, x) -> Tuple[List[float], List[float], float]:
    nodes = _nodes(xs)
    if not isinstance(ys, (list, tuple)) or len(ys) != len(nodes):
        raise ValueError("ys must be a list or tuple with one value per node")
    values = [_real(v, "a value") for v in ys]
    at = _real(x, "x")
    if not min(nodes) <= at <= max(nodes):
        raise ValueError("x is outside the range of the nodes: extrapolation is refused")
    return nodes, values, at


def _weights(nodes: Sequence[float]) -> List[float]:
    out = []
    for j, xj in enumerate(nodes):
        w = 1.0
        for k, xk in enumerate(nodes):
            if k != j:
                w *= xj - xk
        out.append(1.0 / w)
    return out


def lagrange_weights(xs: Sequence[float]) -> List[float]:
    w = _weights(_nodes(xs))
    if not all(math.isfinite(v) for v in w):
        raise ValueError("the nodes are too close or too far apart for double precision")
    return w


def _value(nodes, values, w, at) -> float:
    num = den = 0.0
    for xj, yj, wj in zip(nodes, values, w):
        if at == xj:
            return yj
        c = wj / (at - xj)
        num += c * yj
        den += c
    return num / den


def lagrange(xs: Sequence[float], ys: Sequence[float], x: float) -> float:
    nodes, values, at = _table(xs, ys, x)
    out = _value(nodes, values, lagrange_weights(nodes), at)
    if not math.isfinite(out):
        raise ValueError("the result overflows a float")
    return out


def lagrange_derivative(xs: Sequence[float], ys: Sequence[float], x: float) -> float:
    nodes, values, at = _table(xs, ys, x)
    w = lagrange_weights(nodes)
    if at in nodes:                                         # row of the barycentric differentiation matrix
        i = nodes.index(at)
        out = sum(w[j] / w[i] * (values[j] - values[i]) / (at - nodes[j]) for j in range(len(nodes)) if j != i)
    else:
        p = _value(nodes, values, w, at)
        num = den = 0.0
        for xj, yj, wj in zip(nodes, values, w):
            c = wj / (at - xj)
            num += c * (p - yj) / (at - xj)
            den += c
        out = num / den
    if not math.isfinite(out):
        raise ValueError("the result overflows a float")
    return out
