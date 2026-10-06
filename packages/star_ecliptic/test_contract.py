"""Refusals of star_ecliptic with hostile inputs (NaN, inf, huge integers, booleans, text, values outside their ranges).
Verifies: R4 (README).

Every function returns finite floats in the documented ranges or raises ValueError: nothing is wrapped silently."""
import math
from fractions import Fraction

import pytest

import star_ecliptic as se

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "10", None, 1j, [10.0], (1.0,)]
G = (10.0, 20.0, 84381.406)


def test_the_hostile_set_is_pinned():
    assert len(BAD) == 14 and se.__version__ == "0.1.0"
    assert se.__all__ == ["mean_obliquity_arcsec", "equatorial_to_ecliptic", "ecliptic_to_equatorial"]
    assert (se.JD_MIN, se.JD_MAX) == (2086302.5, 2816787.5) and sorted(se.MODELS) == ["iau1980", "iau2006"]
    assert len(se.MODELS["iau1980"]) == 4 and len(se.MODELS["iau2006"]) == 6


@pytest.mark.parametrize("f", [se.equatorial_to_ecliptic, se.ecliptic_to_equatorial], ids=lambda f: f.__name__)
def test_every_argument_of_the_conversions_refuses_every_hostile_value(f):
    assert all(type(v) is float and math.isfinite(v) for v in f(*G))
    for bad in BAD:
        for i in range(3):
            args = list(G)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)


def test_the_date_refuses_every_hostile_value():
    assert type(se.mean_obliquity_arcsec(2460000.5, 0.5)) is float
    for bad in BAD:
        with pytest.raises(ValueError):
            se.mean_obliquity_arcsec(bad)
        with pytest.raises(ValueError):
            se.mean_obliquity_arcsec(2460000.5, bad)


@pytest.mark.parametrize("model", ["IAU2006", "iau2000", "", " iau2006", b"iau2006", None, 2006, 1980.0, ["iau2006"], True])
def test_unknown_models_are_refused(model):
    with pytest.raises(ValueError, match="model"):
        se.mean_obliquity_arcsec(2460000.5, 0.0, model)


@pytest.mark.parametrize("args, why", [((2086302.4,), "jd_day"), ((2816787.6,), "jd_day"), ((0.0,), "jd_day"), ((2460000.5, 1.0000001), "jd_frac"),
                                       ((2460000.5, -1.0000001), "jd_frac")])
def test_dates_out_of_range(args, why):
    with pytest.raises(ValueError, match=why):
        se.mean_obliquity_arcsec(*args)


@pytest.mark.parametrize("args, why", [((360.0000001, 0, 84381), "right ascension"), ((-360.0000001, 0, 84381), "right ascension"),
                                       ((0, 90.0000001, 84381), "declination"), ((0, -90.0000001, 84381), "declination"),
                                       ((0, 0, -1e-9), "obliquity"), ((0, 0, 324000.0000001), "obliquity")])
def test_angles_out_of_range(args, why):
    with pytest.raises(ValueError, match=why):
        se.equatorial_to_ecliptic(*args)
    with pytest.raises(ValueError, match={"right ascension": "longitude", "declination": "latitude"}.get(why, why)):
        se.ecliptic_to_equatorial(*args)


def test_limits_are_accepted_and_results_stay_in_range():
    for jd in (se.JD_MIN, se.JD_MAX):
        for model in ("iau1980", "iau2006"):
            assert 80000.0 < se.mean_obliquity_arcsec(jd, 0.0, model) < 89000.0
    assert se.mean_obliquity_arcsec(2460000, Fraction(1, 2)) == se.mean_obliquity_arcsec(2460000.5)
    for args in ((360, 90, 324000), (-360, -90, 0), (0, 0, 0), (Fraction(1, 2), 1, 2), (359.9999999999, 0.0, 0.0)):
        for f in (se.equatorial_to_ecliptic, se.ecliptic_to_equatorial):
            lon, lat = f(*args)
            assert 0.0 <= lon < 360.0 and -90.0 <= lat <= 90.0 and type(lon) is float and type(lat) is float
