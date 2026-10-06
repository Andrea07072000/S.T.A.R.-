"""Refusals of star_tle: every way an element set can be malformed gives TleError with a reason, never a half-read set.
Verifies: R4 (README).

The malformed sets are derived from the published ISS example by changing one thing and, where the change would be
caught by the checksum alone, recomputing the checksum: the reader must find the defect itself."""
import pytest

import star_tle as tle

L1 = "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927"
L2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"


def resum(line):
    return line[:68] + str(tle.checksum(line))


def put(line, start, text):
    """The line with `text` written at 1-based column `start`, checksum recomputed."""
    return resum(line[:start - 1] + text + line[start - 1 + len(text):])


def reason(l1, l2):
    with pytest.raises(tle.TleError) as e:
        tle.parse(l1, l2)
    assert str(e.value).startswith(e.value.reason + ": ") and isinstance(e.value, ValueError)
    return e.value.reason


def test_the_reference_set_is_accepted_and_the_helpers_work():
    assert tle.parse(L1, L2)["satnum"] == 25544 and resum(L1) == L1 and put(L1, 3, "25544") == L1
    assert tle.__all__ == ["parse", "checksum", "epoch_utc", "TleError"] and tle.__version__ == "0.1.0"
    assert tle.ALPHA5 == "ABCDEFGHJKLMNPQRSTUVWXYZ" and len(tle.ALPHA5) == 24


@pytest.mark.parametrize("l1, l2, expected", [
    (L1[:68], L2, "length"), (L1 + " ", L2, "length"), (L1, L2[:68], "length"), ("", L2, "length"), (L1, "", "length"),
    (None, L2, "length"), (L1, 5, "length"), (L1.encode(), L2, "length"), ([L1], L2, "length"),
    (L1[:30] + "\t" + L1[31:], L2, "charset"), (L1[:30] + "é" + L1[31:], L2, "charset"), (L1, L2[:10] + "\x00" + L2[11:], "charset"),
    (L1[:10] + "１" + L1[11:], L2, "charset"),
    (resum("2" + L1[1:]), L2, "line_number"), (L1, resum("1" + L2[1:]), "line_number"), (resum("1U" + L1[2:]), L2, "line_number"),
    (L2, L1, "line_number"), (resum(" " + L1[1:]), L2, "line_number"),
    (L1[:68] + "8", L2, "checksum"), (L1, L2[:68] + "0", "checksum"), (L1[:68] + " ", L2, "checksum"), (L1[:68] + "X", L2, "checksum"),
    (L1[:40] + "3" + L1[41:], L2, "checksum"),
    (put(L1, 3, "25545"), L2, "satnum_mismatch"), (L1, put(L2, 3, "00005"), "satnum_mismatch"), (put(L1, 3, "A5544"), L2, "satnum_mismatch")])
def test_structural_defects(l1, l2, expected):
    assert reason(l1, l2) == expected


@pytest.mark.parametrize("line, col, text, expected", [
    (1, 3, "2554X", "field:satnum"), (1, 3, "I0000", "field:satnum"), (1, 3, "O0000", "field:satnum"), (1, 3, "a0000", "field:satnum"),
    (1, 3, "5    ", "field:satnum"), (1, 3, "     ", "field:satnum"), (1, 3, "-5544", "field:satnum"),
    (1, 8, "u", "field:classification"), (1, 8, " ", "field:classification"), (1, 8, "X", "field:classification"),
    (1, 19, "0A", "field:epoch_year"), (1, 19, "  ", "field:epoch_year"), (1, 19, "8 ", "field:epoch_year"),
    (1, 21, "264.5178252X", "field:epoch_day"), (1, 21, "nan         ", "field:epoch_day"), (1, 21, "2.645178e+02", "field:epoch_day"),
    (1, 21, "264 51782528", "field:epoch_day"), (1, 21, "26451782528 ", "field:epoch_day"), (1, 21, "inf         ", "field:epoch_day"),
    (1, 21, "000.99999999", "range:epoch_day"), (1, 21, "367.00000000", "range:epoch_day"), (1, 21, "999.00000000", "range:epoch_day"),
    (1, 34, " .0000218X", "field:ndot_over_2"), (1, 34, " 00002182 ", "field:ndot_over_2"), (1, 34, "--.0000218", "field:ndot_over_2"),
    (1, 45, " 0000000", "field:nddot_over_6"), (1, 45, " 00000 0", "field:nddot_over_6"), (1, 45, "*00000-0", "field:nddot_over_6"),
    (1, 54, "-1160604", "field:bstar"), (1, 54, "-1160-4 ", "field:bstar"), (1, 54, "-11606-X", "field:bstar"), (1, 54, " nan  -4", "field:bstar"),
    (1, 63, "X", "field:ephemeris_type"), (1, 63, "-", "field:ephemeris_type"),
    (1, 65, " 2X2", "field:element_number"), (1, 65, "292 ", "field:element_number"), (1, 65, "    ", "field:element_number"),
    (2, 9, " 51.641X", "field:inclination"), (2, 9, "     nan", "field:inclination"), (2, 9, " 51 6416", "field:inclination"),
    (2, 9, "180.0001", "range:inclination"), (2, 9, "999.9999", "range:inclination"),
    (2, 18, "360.0000", "range:raan"), (2, 18, "947.4627", "range:raan"), (2, 18, "247.462X", "field:raan"),
    (2, 27, "00067 3", "field:eccentricity"), (2, 27, "000670X", "field:eccentricity"), (2, 27, ".006703", "field:eccentricity"),
    (2, 35, "360.0000", "range:argp"), (2, 35, "13 .5360", "field:argp"),
    (2, 44, "360.0000", "range:mean_anomaly"), (2, 44, "325.028 ", "field:mean_anomaly"),
    (2, 53, "00.00000000", "range:mean_motion"), (2, 53, "15.7212539X", "field:mean_motion"), (2, 53, "1.572125e+1", "field:mean_motion"),
    (2, 64, "5635X", "field:rev_number"), (2, 64, "56 53", "field:rev_number"), (2, 64, "     ", "field:rev_number")])
def test_field_defects_found_even_with_a_correct_checksum(line, col, text, expected):
    l1, l2 = (put(L1, col, text), L2) if line == 1 else (L1, put(L2, col, text))
    if line == 2 and col == 3:
        l1 = put(L1, col, text)
    if col == 3:
        l1, l2 = put(L1, col, text), put(L2, col, text)
    assert reason(l1, l2) == expected


def test_limits_that_are_accepted():
    assert tle.parse(L1, put(L2, 9, "180.0000"))["inclination_deg"] == 180.0 and tle.parse(L1, put(L2, 9, "  0.0000"))["inclination_deg"] == 0.0
    assert tle.parse(L1, put(L2, 18, "359.9999"))["raan_deg"] == 359.9999 and tle.parse(L1, put(L2, 27, "9999999"))["eccentricity"] == 0.9999999
    assert tle.parse(put(L1, 21, "366.99999999"), L2)["epoch_day"] == 366.99999999                    # 2008 is a leap year
    assert tle.parse(put(L1, 21, "001.00000000"), L2)["epoch_day"] == 1.0
    not_leap = put(put(L1, 19, "09"), 21, "365.99999999")
    assert tle.parse(not_leap, L2)["epoch_year"] == 2009
    assert reason(put(put(L1, 19, "09"), 21, "366.00000000"), L2) == "range:epoch_day"                # day 366 does not exist in 2009
    assert tle.parse(put(put(L1, 19, "00"), 21, "366.50000000"), L2)["epoch_year"] == 2000            # 2000 was a leap year
    assert tle.parse(put(L1, 63, " "), L2)["ephemeris_type"] == 0 and tle.parse(put(L1, 63, "4"), L2)["ephemeris_type"] == 4
    for c in "CS":
        assert tle.parse(put(L1, 8, c), L2)["classification"] == c


def test_checksum_and_epoch_refuse_what_they_cannot_use():
    for bad in (None, 5, b"x" * 69, "short", "x" * 67, ["1"] * 69):
        with pytest.raises(tle.TleError):
            tle.checksum(bad)
    for bad in (None, {}, {"epoch_year": 2008}, "tle", 5):
        with pytest.raises(tle.TleError):
            tle.epoch_utc(bad)
