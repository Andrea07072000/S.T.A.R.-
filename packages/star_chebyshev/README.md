# star_chebyshev — Chebyshev series with their derivative

Value and first derivative of a Chebyshev series, on [-1, 1] or on an interval given by midpoint and radius, the
form in which planetary and spacecraft ephemerides store positions. Standard library only.

```python
import star_chebyshev as sc
sc.evaluate([1, 2, 3], 0.5)                              # (0.5, 8.0): 1 + 2 T_1 + 3 T_2 and its derivative
sc.evaluate_on([1, 3, 0.5, 1, 0.5, -1, 1], 1, 0.5, 3)    # (-0.3408779..., 0.3827160...): the NAIF example
```

## Requirements
- R1 `evaluate(coefficients, x)` returns the sum of c_k T_k(x) and its derivative for x in [-1, 1], c_0 first, by
  Clenshaw's recurrence (the polynomials T_k are never formed).
- R2 `evaluate_on(coefficients, t, mid, radius)` evaluates the same series at x = (t - mid) / radius and returns the
  derivative with respect to t. A t outside the interval is refused; one that leaves it by rounding alone (at most
  two units in the last place) is taken as the end.
- R3 Measured on 600 series of 1 to 40 terms at points of random intervals, ends included: value and derivative
  agree with CSPICE `chbval`/`chbder` and NumPy within 1e-14, and with mpmath at 40 digits within 5e-14, of the
  natural scale of the sum (sum of |c_k|; sum of k² |c_k| / radius).
- R4 Every function returns two floats or raises `ValueError`: a malformed coefficient list (1 to 200 finite numbers
  within 1e100, booleans refused), x outside [-1, 1], t outside the interval, a midpoint or radius out of range.

## Evidence
- Published: the example of the NAIF documentation of `chbval_c` and `chbder_c` (-0.340878 and 0.382716). The first
  five Chebyshev polynomials and the end values T_k(±1), T_k'(±1), by hand.
- `crosscheck_chebyshev.py`: CSPICE, NumPy and mpmath, each in its own interpreter.

## What is NOT claimed
Evaluation only: no fitting of coefficients, no reading of ephemeris files, no second or higher derivatives, no
integration of the series. The error of the result is that of Clenshaw's recurrence in double precision, about
1e-15 of the sum of |c_k| (more for the derivative, by the factor k²): when the terms cancel, the relative error of
a small result is larger and is not bounded here. For an ephemeris, the accuracy of a position is that of its
coefficients, which this module cannot judge.
