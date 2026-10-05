"""Input contract of screen(), from a probe with hostile inputs (2026-10-05).
Verifies: R1 (README).

Found by the probe, each one a SILENT wrong answer: final_km NaN or negative returned 0 events; coarse_km < final_km
returned 0 events (the coarse filter discarded every encounter); a start with a +02:00 offset was read as UTC wall
time, shifting the window by two hours; a naive start was propagated as UTC but its TCA computed in local time.
For a screening, "nothing close" on a bad input is the worst possible output: these inputs are now refused, and the
same instant expressed in two time zones must give the same events."""
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from screen import screen

HERE = Path(__file__).parent
P = [str(HERE / "fixtures" / "cosmos_2251_debris.tle"), str(HERE / "fixtures" / "iridium_33_debris.tle")]
UTC0 = datetime(2009, 2, 10, tzinfo=timezone.utc)


def run(**kw):
    a = dict(paths=P, start=UTC0, hours=1.0, step=10.0, coarse_km=None, final_km=5.0)
    a.update(kw)
    return screen(**a)


@pytest.mark.parametrize("kw", [
    dict(final_km=math.nan), dict(final_km=-1.0), dict(final_km=0.0), dict(coarse_km=1.0, final_km=5.0),
    dict(coarse_km=math.nan), dict(step=0.0), dict(step=-10.0), dict(step=math.inf), dict(hours=-1.0),
    dict(hours=math.nan), dict(start=datetime(2009, 2, 10)),
])
def test_bad_input_is_refused_not_answered_with_no_events(kw):
    with pytest.raises(ValueError):
        run(**kw)


def test_same_instant_in_two_time_zones_gives_the_same_events():
    utc = run()
    plus2 = run(start=UTC0.astimezone(timezone(timedelta(hours=2))))
    key = lambda r: sorted((e["a"], e["b"], e["tca_utc"], round(e["miss_km"], 6)) for e in r["events"])
    assert utc["events_below_final_km"] == plus2["events_below_final_km"] > 0
    assert utc["coarse_encounters"] == plus2["coarse_encounters"]
    assert key(utc) == key(plus2)


def test_zero_hours_is_a_single_epoch_not_an_error():
    r = run(hours=0.0)
    assert r["events_below_final_km"] >= 0
