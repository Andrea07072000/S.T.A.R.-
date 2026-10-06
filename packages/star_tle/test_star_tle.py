"""star_tle on published element sets.
Verifies: R1, R2, R3 (README).

Published: (a) the ISS element set used as the worked example of the two-line format (NASA Human Space Flight /
Space-Track documentation), epoch 2008 day 264.51782528; (b) the 29 well-formed element sets of the SGP4 verification
catalogue SGP4-VER.TLE distributed with Vallado, Crawford, Hujsak, Kelso, "Revisiting Spacetrack Report #3" (2006),
in fixtures/. The values asserted are the ones printed on the lines themselves.
The comparison of every field with python-sgp4 and Orekit is in crosscheck_tle.py."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import star_tle as tle

ISS1 = "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927"
ISS2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
FIXTURE = next(p for p in (Path(__file__).resolve().parent / "fixtures" / "SGP4-VER.TLE", Path.cwd() / "fixtures" / "SGP4-VER.TLE") if p.exists())


def catalogue():
    lines = [ln.rstrip() for ln in FIXTURE.read_text(encoding="utf-8", errors="replace").splitlines()]
    return [(lines[i][:69], lines[i + 1][:69]) for i in range(len(lines) - 1) if lines[i].startswith("1 ") and lines[i + 1].startswith("2 ")]


def test_published_iss_example_every_field():
    t = tle.parse(ISS1, ISS2)
    assert t == {"satnum": 25544, "classification": "U", "intl_designator": "98067A", "epoch_year": 2008, "epoch_day": 264.51782528,
                 "ndot_over_2": -0.00002182, "nddot_over_6": 0.0, "bstar": -0.11606e-4, "ephemeris_type": 0, "element_number": 292,
                 "inclination_deg": 51.6416, "raan_deg": 247.4627, "eccentricity": 0.0006703, "argp_deg": 130.5360,
                 "mean_anomaly_deg": 325.0288, "mean_motion_rev_day": 15.72125391, "rev_number": 56353}
    assert tle.checksum(ISS1) == 7 and tle.checksum(ISS2) == 7


def test_epoch_of_the_iss_example():
    # day 264.51782528 of 2008 (a leap year) is 20 September, 12:25:40.104 UTC
    e = tle.epoch_utc(tle.parse(ISS1, ISS2))
    assert e.tzinfo is timezone.utc and (e.year, e.month, e.day, e.hour, e.minute, e.second) == (2008, 9, 20, 12, 25, 40)
    assert abs((e - datetime(2008, 9, 20, 12, 25, 40, 104192, tzinfo=timezone.utc)).total_seconds()) < 1e-3
    assert e == datetime(2008, 1, 1, tzinfo=timezone.utc) + timedelta(days=263.51782528)


def test_every_element_set_of_the_sgp4_verification_catalogue_is_read_as_printed():
    pairs = sorted({p for p in catalogue() if len(p[0]) == 69 and len(p[1]) == 69})          # one set is listed twice
    read = 0
    for l1, l2 in pairs:
        try:
            t = tle.parse(l1, l2)
        except tle.TleError:
            continue                                   # the catalogue also carries deliberately broken sets
        read += 1
        assert t["satnum"] == int(l1[2:7]) == int(l2[2:7]) and t["inclination_deg"] == float(l2[8:16])
        assert t["raan_deg"] == float(l2[17:25]) and t["eccentricity"] == float("0." + l2[26:33])
        assert t["argp_deg"] == float(l2[34:42]) and t["mean_anomaly_deg"] == float(l2[43:51])
        assert t["mean_motion_rev_day"] == float(l2[52:63]) and t["epoch_day"] == float(l1[20:32])
        assert t["rev_number"] == int(l2[63:68]) and t["element_number"] == int(l1[64:68])
        assert 1957 <= t["epoch_year"] <= 2056 and t["epoch_year"] % 100 == int(l1[18:20])
    assert read == 29


def test_first_set_of_the_catalogue_vanguard_1():
    l1, l2 = catalogue()[0]
    t = tle.parse(l1, l2)
    assert (t["satnum"], t["intl_designator"], t["epoch_year"]) == (5, "58002B", 2000)
    assert (t["inclination_deg"], t["eccentricity"], t["mean_motion_rev_day"]) == (34.2682, 0.1859667, 10.82419157)
    assert t["bstar"] == pytest.approx(0.28098e-4, rel=1e-15) and t["ndot_over_2"] == 0.00000023 and t["nddot_over_6"] == 0.0


@pytest.mark.parametrize("field, value", [(" 00000-0", 0.0), (" 12345-3", 0.12345e-3), ("-11606-4", -0.11606e-4), ("+50000+1", 5.0),
                                          (" 00001-9", 1e-14), ("-99999+0", -0.99999)])
def test_implied_point_exponent_fields(field, value):
    assert tle._exponent(field, "x") == pytest.approx(value, rel=1e-14, abs=0.0)


@pytest.mark.parametrize("yy, year", [("57", 1957), ("99", 1999), ("00", 2000), ("24", 2024), ("56", 2056)])
def test_two_digit_year_window(yy, year):
    l1 = ISS1[:18] + yy + "001.00000000" + ISS1[32:68]
    l1 += str(tle.checksum(l1))
    assert tle.parse(l1, ISS2)["epoch_year"] == year


@pytest.mark.parametrize("text, number", [("00005", 5), ("99999", 99999), ("A0000", 100000), ("B1234", 111234), ("H0000", 170000),
                                          ("J0000", 180000), ("P0000", 230000), ("Z9999", 339999), ("    5", 5)])
def test_catalogue_numbers_including_alpha5(text, number):
    l1 = ISS1[:2] + text + ISS1[7:68]
    l2 = ISS2[:2] + text + ISS2[7:68]
    assert tle.parse(l1 + str(tle.checksum(l1)), l2 + str(tle.checksum(l2)))["satnum"] == number


def test_checksum_rule():
    assert tle.checksum("0" * 68) == 0 and tle.checksum("9" * 68) == 2 and tle.checksum("-" * 68) == 8        # '-' counts 1
    assert tle.checksum("1" + "A.+ " * 16 + "abc") == 1                                                    # letters, '.', '+', blanks count 0
    assert tle.checksum(ISS1) == int(ISS1[68]) and tle.checksum(ISS1[:68]) == 7 and tle.checksum(ISS1 + "trailing") == 7
