"""Numeric-field contract of parse_cdm, from a probe of R2 with hostile values (2026-10-05).
Verifies: R1, R2 (README).

Found by the probe: Python's float() accepted 'NaN', 'inf', '-Infinity', '1_000' (underscore digit grouping) and
overflowed '1e400' to inf, so such CDMs were parsed and their consistency report contained nan/inf distances. None is
a KVN number. A negative MISS_DISTANCE or RELATIVE_SPEED and a COLLISION_PROBABILITY outside [0, 1] were accepted too.
All are now CdmFormatError. Negative variances are NOT rejected here: they are reported by deep_consistency (R3)."""
import re
from pathlib import Path

import pytest

from star_cdm import CdmFormatError, parse_cdm

BASE = (Path(__file__).parent / "fixtures" / "corrected" / "example_3.kvn").read_text(encoding="utf-8")


def with_value(key, value):
    out, n = re.subn(rf"^(\s*{key}\s*=\s*)(\S+)", lambda m: m.group(1) + value, BASE, count=1, flags=re.M)
    assert n == 1, key
    return out


@pytest.mark.parametrize("key,value", [
    ("X", "NaN"), ("X", "nan"), ("X", "inf"), ("X", "-Infinity"), ("X", "1e400"), ("X", "1_000"), ("X", "0x10"),
    ("X", "1e"), ("X", "."), ("MISS_DISTANCE", "nan"), ("MISS_DISTANCE", "-5"), ("RELATIVE_SPEED", "-0.1"),
    ("COLLISION_PROBABILITY", "2.0"), ("COLLISION_PROBABILITY", "-1e-9"),
])
def test_non_numbers_and_impossible_values_are_format_errors(key, value):
    with pytest.raises(CdmFormatError):
        parse_cdm(with_value(key, value))


@pytest.mark.parametrize("value,expected", [("2570.097065", 2570.097065), ("+1.5", 1.5), ("-1.5E+03", -1500.0),
                                            (".5", 0.5), ("7.", 7.0), ("12", 12.0)])
def test_valid_kvn_numbers_still_parse(value, expected):
    assert parse_cdm(with_value("X", value))["object1"]["X"] == expected


def test_boundary_values_are_accepted():
    cdm = parse_cdm(with_value("COLLISION_PROBABILITY", "1.0"))
    assert cdm["header"]["COLLISION_PROBABILITY"] == 1.0
    assert parse_cdm(with_value("MISS_DISTANCE", "0"))["header"]["MISS_DISTANCE"] == 0.0
