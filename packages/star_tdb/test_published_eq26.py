"""R1 against the primary source, term by term.
Verifies: R1 (README).

The ERFA comparison (test_star_tdb.py) cannot see a wrong SMALL term: terms of 2-22 microseconds sit inside its
10-microsecond tolerance. This test re-reads eq. 2.6 from the published text and checks every one of the 7 terms.

Source: G. H. Kaplan, USNO Circular 179 (2005), eq. 2.6, as distributed on arXiv (astro-ph/0602086; PDF sha256
112b1664402a6d72b746303e87e5f340bd0984930cddf34236b42cfb1f414885, 1 074 572 bytes). Transcribed 2026-10-05 from
`pdftotext -layout` of that PDF (equation block on lines 1198-1204 of the text), NOT from star_tdb.py:

    TDB - TT = 0.001657 sin (628.3076 T + 6.2401) + 0.000022 sin (575.3385 T + 4.2970)
             + 0.000014 sin (1256.6152 T + 6.1969) + 0.000005 sin (606.9777 T + 4.0212)
             + 0.000005 sin (52.9691 T + 0.4444)   + 0.000002 sin (21.3299 T + 5.5431)
             + 0.000010 T sin (628.3076 T + 4.2490)
    T = (JD(TT) - 2451545.0) / 36525 ; coefficients in seconds, arguments in radians."""
import math

import pytest

from star_tdb import tdb_minus_tt

PUBLISHED = [  # (amplitude s, frequency rad/century, phase rad, multiplied by T)
    (0.001657, 628.3076, 6.2401, False), (0.000022, 575.3385, 4.2970, False), (0.000014, 1256.6152, 6.1969, False),
    (0.000005, 606.9777, 4.0212, False), (0.000005, 52.9691, 0.4444, False), (0.000002, 21.3299, 5.5431, False),
    (0.000010, 628.3076, 4.2490, True),
]


def published(jd_tt, drop=None):
    T = (jd_tt - 2451545.0) / 36525.0
    return sum(a * (T if t else 1.0) * math.sin(f * T + p) for i, (a, f, p, t) in enumerate(PUBLISHED) if i != drop)


EPOCHS = [2451545.0 + k * 3652.5 * 1.1 for k in range(-36, 19)]  # 1604-2198, every 11 years


def test_equals_published_equation_2_6():
    for jd in EPOCHS:
        assert abs(tdb_minus_tt(jd) - published(jd)) < 1e-15, jd


@pytest.mark.parametrize("term", range(7))
def test_every_published_term_is_present(term):
    # removing any single term of the published series must change the result by more than rounding: each of the
    # 7 terms is really in the implementation (a missing or zeroed term would make this difference ~0)
    worst = max(abs(tdb_minus_tt(jd) - published(jd, drop=term)) for jd in EPOCHS)
    assert worst > 1e-7, (term, worst)
