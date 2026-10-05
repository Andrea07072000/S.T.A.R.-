"""Shared guard of the star_audit auditors (S.T.A.R., 2026-10-05).

Found by a hostile probe: an implementation that returns NaN (without raising) for every epoch after 2000 was reported
by the GMST auditor as agreeing to "0.0 arcsec" with a correct one. Python's max(0.0, nan) returns 0.0, so a NaN
disappeared from every max-difference envelope, in every auditor built on that pattern. A value that is not a finite
number is not an answer: it is turned into an explicit error row, counted as a refusal, and an implementation with
refusals is not validated.
"""
import math
from typing import Dict, Iterable, List


def _finite(x) -> bool:
    if x is None:
        return True                       # None marks a documented "no value" (e.g. missing SGP4 epoch), kept as is
    if isinstance(x, bool):
        return False
    if isinstance(x, (int, float)):
        return math.isfinite(x)
    if isinstance(x, (list, tuple)):
        return all(_finite(v) for v in x)
    if isinstance(x, dict):
        return all(_finite(v) for v in x.values())
    return True                           # strings, codes: not numeric, compared by the auditor itself


def finite_rows(rows: List[Dict], keys: Iterable[str]) -> List[Dict]:
    """Replace every row whose numeric payload (under any of `keys`) is not finite by an error row."""
    keys = tuple(keys)
    out = []
    for row in rows:
        bad = [k for k in keys if k in row and not _finite(row[k])]
        out.append({"error": f"non-finite value returned for {bad[0]!r}: {row[bad[0]]!r}"[:120]} if bad else row)
    return out
