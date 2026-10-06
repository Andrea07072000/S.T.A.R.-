"""star_tle - a strict reader of NORAD two-line element sets (S.T.A.R., 2026-10-06). Standard library only.

  parse(line1, line2) -> dict with every field of the two lines, in the units printed in the TLE
  checksum(line) -> int: modulo-10 checksum of the first 68 columns (digits count as themselves, '-' counts 1)
  epoch_utc(tle) -> timezone-aware datetime of the epoch
Why strict: three of four widely used readers accept element sets with a wrong checksum, a wrong line number or two
different satellite numbers (S.T.A.R. TLE audit, 2026-10-05). Here a line that breaks the format is refused with
TleError and a machine-readable `reason`, never repaired or half-read:
  length, charset, line_number, checksum, satnum_mismatch, field:<name> (not a number in the expected form),
  range:<name> (inclination outside [0, 180], an angle outside [0, 360), mean motion <= 0, epoch day outside the year).
Supported: catalogue numbers in Alpha-5 form (a letter in the first column for numbers above 99999).
Not interpreted: the element set is returned as printed (mean elements of the SGP4 theory, TEME frame); converting
them to a position requires SGP4, which this module does not contain.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict

__all__ = ["parse", "checksum", "epoch_utc", "TleError"]
__version__ = "0.1.0"
ALPHA5 = "ABCDEFGHJKLMNPQRSTUVWXYZ"          # I and O are not used


class TleError(ValueError):
    """The two lines are not a well-formed element set. `reason` says which rule failed."""

    def __init__(self, reason: str, message: str):
        super().__init__(f"{reason}: {message}")
        self.reason = reason


def checksum(line: str) -> int:
    if not isinstance(line, str) or len(line) < 68:
        raise TleError("length", "a checksum needs at least 68 columns")
    return sum(int(c) if c in "0123456789" else (1 if c == "-" else 0) for c in line[:68]) % 10


def _satnum(text: str) -> int:
    if len(text) == 5 and text[0] in ALPHA5 and text[1:].isdigit() and text[1:].isascii():
        return (10 + ALPHA5.index(text[0])) * 10000 + int(text[1:])
    if not (text.strip().isdigit() and text.strip().isascii()) or text != text.strip().rjust(5):
        raise TleError("field:satnum", f"{text!r} is not a catalogue number")
    return int(text)


def _digits(text: str, name: str) -> int:
    t = text.strip()
    if not t or not (t.isdigit() and t.isascii()) or text != t.rjust(len(text)):
        raise TleError(f"field:{name}", f"{text!r} is not an unsigned integer, right-aligned")
    return int(t)


def _decimal(text: str, name: str, signed: bool = False) -> float:
    """Fixed-point number as printed: optional sign, digits, one point, digits. No exponent, no inf/nan words."""
    t = text.strip()
    body = t[1:] if signed and t[:1] in "+-" else t
    whole, dot, frac = body.partition(".")
    if dot != "." or not frac.isdigit() or not (whole == "" or whole.isdigit()) or not body.isascii() or " " in t or text != text.rstrip():
        raise TleError(f"field:{name}", f"{text!r} is not a decimal number")
    return float(t)


def _exponent(text: str, name: str) -> float:
    """Implied-point form ' NNNNN-N': sign or blank, five digits, exponent sign, one digit = +-0.NNNNN x 10^(+-N)."""
    if len(text) != 8 or text[0] not in " +-" or not (text[1:6].isdigit() and text[1:6].isascii()) or text[6] not in "+-" \
            or text[7] not in "0123456789":
        raise TleError(f"field:{name}", f"{text!r} is not in the form ' NNNNN-N'")
    # built as text and converted once: the nearest double of the printed number (digits * 1e-5 * 10**n is not)
    return float(f"{'-' if text[0] == '-' else ''}0.{text[1:6]}e{text[6:8]}")


def _eccentricity(text: str) -> float:
    """Seven digits with an implied leading '0.'."""
    if not (text.isdigit() and text.isascii()):
        raise TleError("field:eccentricity", f"{text!r} is not seven digits")
    return float("0." + text)


def _angle(text: str, name: str, upper: float, closed: bool) -> float:
    v = _decimal(text, name)
    if not (0.0 <= v <= upper if closed else 0.0 <= v < upper):
        raise TleError(f"range:{name}", f"{v} is outside [0, {upper}{']' if closed else ')'}")
    return v


def parse(line1: str, line2: str) -> Dict:
    for n, line in ((1, line1), (2, line2)):
        if not isinstance(line, str):
            raise TleError("length", f"line {n} is not text")
        if len(line) != 69:
            raise TleError("length", f"line {n} has {len(line)} columns, not 69")
        if not line.isascii() or any(ord(c) < 32 or ord(c) > 126 for c in line):
            raise TleError("charset", f"line {n} contains characters outside printable ASCII")
        if line[0] != str(n) or line[1] != " ":
            raise TleError("line_number", f"line {n} does not start with '{n} '")
        if line[68] not in "0123456789" or checksum(line) != int(line[68]):
            raise TleError("checksum", f"line {n}: computed {checksum(line)}, printed {line[68]!r}")
    if line1[2:7] != line2[2:7]:
        raise TleError("satnum_mismatch", f"{line1[2:7]!r} on line 1, {line2[2:7]!r} on line 2")
    yy = _digits(line1[18:20], "epoch_year")
    year = 2000 + yy if yy < 57 else 1900 + yy
    day = _decimal(line1[20:32], "epoch_day")
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    if not 1.0 <= day < (367.0 if leap else 366.0):
        raise TleError("range:epoch_day", f"day {day} does not exist in {year}")
    classification = line1[7]
    if classification not in "UCS":
        raise TleError("field:classification", f"{classification!r} is not U, C or S")
    ephemeris = line1[62]
    if ephemeris not in " 0123456789":
        raise TleError("field:ephemeris_type", f"{ephemeris!r} is not a digit")
    mean_motion = _decimal(line2[52:63], "mean_motion")
    if mean_motion <= 0.0:
        raise TleError("range:mean_motion", "mean motion must be positive")
    return {
        "satnum": _satnum(line1[2:7]),
        "classification": classification,
        "intl_designator": line1[9:17].strip(),
        "epoch_year": year,
        "epoch_day": day,
        "ndot_over_2": _decimal(line1[33:43], "ndot_over_2", signed=True),              # rev/day^2
        "nddot_over_6": _exponent(line1[44:52], "nddot_over_6"),                        # rev/day^3
        "bstar": _exponent(line1[53:61], "bstar"),                                      # 1/earth radii
        "ephemeris_type": 0 if ephemeris == " " else int(ephemeris),
        "element_number": _digits(line1[64:68], "element_number"),
        "inclination_deg": _angle(line2[8:16], "inclination", 180.0, closed=True),
        "raan_deg": _angle(line2[17:25], "raan", 360.0, closed=False),
        "eccentricity": _eccentricity(line2[26:33]),
        "argp_deg": _angle(line2[34:42], "argp", 360.0, closed=False),
        "mean_anomaly_deg": _angle(line2[43:51], "mean_anomaly", 360.0, closed=False),
        "mean_motion_rev_day": mean_motion,
        "rev_number": _digits(line2[63:68], "rev_number"),
    }


def epoch_utc(tle: Dict) -> datetime:
    if not isinstance(tle, dict) or "epoch_year" not in tle or "epoch_day" not in tle:
        raise TleError("field:epoch", "not a parsed element set")
    return datetime(tle["epoch_year"], 1, 1, tzinfo=timezone.utc) + timedelta(days=tle["epoch_day"] - 1.0)
