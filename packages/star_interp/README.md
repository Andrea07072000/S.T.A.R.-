# star_interp — Lagrange interpolation through tabulated points

The value, and the first derivative, of the polynomial through a few tabulated points: the way an ephemeris given
at fixed epochs (SP3, CCSDS OEM) is read between them. Standard library only.

```python
import star_interp as si
days, au = [7.0, 8.0, 9.0], [0.884226, 0.877366, 0.870531]       # distance of Mars, 1992 November 7-9 (Meeus)
si.lagrange(days, au, 8 + 4.35 / 24)                              # 0.876125 AU on November 8 at 4h 21m
si.lagrange_derivative(days, au, 8 + 4.35 / 24)                   # -0.006843 AU per day
```

## Requirements
- R1 `lagrange(xs, ys, x)`: the polynomial of degree len(xs) − 1 through the points, in barycentric form; nodes in
  any order and any spacing; at a node the tabulated value is returned exactly. Reproduces Meeus Example 3.a.
- R2 `lagrange_derivative(xs, ys, x)`: its first derivative, also at the nodes; `lagrange_weights(xs)`: the weights.
- R3 Measured on 600 tables of 2 to 11 jittered, unsorted nodes against EXACT rational arithmetic (SymPy): value
  within 7e-15 of the exact polynomial, relative to the largest tabulated value; derivative within 1e-13 (scaled).
  On the same tables SciPy's barycentric interpolator is within 1.2e-14 of the exact value and a NumPy polynomial
  fit within 7e-11.
- R4 Every function returns a finite float or raises `ValueError`: fewer than 2 or more than 20 points, lengths
  that differ, equal nodes, any non-finite or non-numeric element (booleans included), an x outside the range of the
  nodes (extrapolation is refused), nodes whose weights overflow.

## Evidence
- Published: Meeus, Astronomical Algorithms, Example 3.a. Polynomials reproduced exactly, weights, symmetries, by hand.
- `crosscheck_interp.py`: SymPy (exact), SciPy and NumPy, each in its own interpreter, each probed on the published example.

## What is NOT claimed
The accuracy stated is that of evaluating the polynomial, NOT of the interpolation: how well a polynomial through n
points represents an orbit depends on the spacing, the degree and where in the table x falls (the central interval
is the reliable one), and is the caller's to assess. No extrapolation, no Hermite interpolation (positions with
velocities), no splines, scalars only (interpolate each coordinate separately). With many points far from equally
spaced the polynomial itself oscillates; that is a property of the method, not checked here.
