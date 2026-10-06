"""Shared guard of the star_audit auditors (S.T.A.R., 2026-10-05).

Found by a hostile probe: an implementation that returns NaN (without raising) for every epoch after 2000 was reported
by the GMST auditor as agreeing to "0.0 arcsec" with a correct one. Python's max(0.0, nan) returns 0.0, so a NaN
disappeared from every max-difference envelope, in every auditor built on that pattern. A value that is not a finite
number is not an answer: it is turned into an explicit error row, counted as a refusal, and an implementation with
refusals is not validated.
"""
import json
import math
from typing import Dict, Iterable, List


def driver_rows(stdout: str, n: int, row: type = dict) -> List:
    """The result rows a driver printed on its last output line: exactly `n` JSON values of type `row`.

    Found by a hostile probe (2026-10-06): a driver that answered 1 case out of 198 was VALIDATED by the TLE auditor,
    because zip() stopped at the shorter list and the totals were counted on what came back; an empty or non-JSON
    output surfaced as IndexError / JSONDecodeError / TypeError. Anything but one row per case is a failed run."""
    lines = stdout.strip().splitlines()
    try:
        rows = json.loads(lines[-1]) if lines else None
    except ValueError:
        rows = None
    if not isinstance(rows, list):
        raise RuntimeError(f"implementation run printed no result list ({n} cases)")
    if len(rows) != n or not all(isinstance(r, row) for r in rows):
        raise RuntimeError(f"implementation run did not return one {row.__name__} per case ({len(rows)} rows, {n} cases)")
    return rows


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
