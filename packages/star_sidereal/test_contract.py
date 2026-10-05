"""Non-finite input contract, from a probe of R3 (2026-10-05).
Verifies: R2, R3 (README).

Found by the probe: lst_deg with a NaN or infinite longitude returned nan instead of raising ValueError (R3 says
non-finite input raises). gmst82_deg already refused non-finite dates; both functions are checked here."""
import math

import pytest

from star_sidereal import gmst82_deg, lst_deg


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_lst_rejects_non_finite_longitude(bad):
    with pytest.raises(ValueError):
        lst_deg(2451545.0, 0.0, bad)


@pytest.mark.parametrize("args", [(math.nan, 0.0), (2451545.0, math.nan), (math.inf, 0.0), (2451545.0, -math.inf)])
def test_gmst_and_lst_reject_non_finite_dates(args):
    with pytest.raises(ValueError):
        gmst82_deg(*args)
    with pytest.raises(ValueError):
        lst_deg(*args, 10.0)
