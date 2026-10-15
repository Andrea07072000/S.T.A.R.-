# -*- coding: utf-8 -*-
"""star_tdb — TDB - TT (S.T.A.R., 2026-10-04). Standard library only.

Model: the 7-term series of USNO Circular 179 (Kaplan 2005), eq. 2.6, stated accuracy ~10 microseconds over
1600-2200 against the full Fairhead & Bretagnon (1990) series. This is an APPROXIMATION and is declared as such:
it is verified against ERFA's full dtdb series (a different method), not against itself.
"""
from __future__ import annotations

import math

VALID_YEARS = (1600, 2200)
_TERMS = ((0.001657, 628.3076, 6.2401), (0.000022, 575.3385, 4.2970), (0.000014, 1256.6152, 6.1969),
          (0.000005, 606.9777, 4.0212), (0.000005, 52.9691, 0.4444), (0.000002, 21.3299, 5.5431))


def tdb_minus_tt(jd_tt: float) -> float:
    """TDB - TT in seconds for a TT Julian date. Raises ValueError outside 1600-2200 (stated validity)."""
    T = (jd_tt - 2451545.0) / 36525.0
    year = 2000.0 + 100.0 * T
    if not VALID_YEARS[0] <= year <= VALID_YEARS[1]:
        raise ValueError(f"TDB-TT series valid {VALID_YEARS[0]}-{VALID_YEARS[1]}, got year {year:.1f}")
    s = sum(a * math.sin(f * T + p) for a, f, p in _TERMS)
    return s + 0.000010 * T * math.sin(628.3076 * T + 4.2490)
