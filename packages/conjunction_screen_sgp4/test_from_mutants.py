"""Tests written from mutation survivors (12_EVIDENCE/mutation/screen_20261004.json, score 0.433): the grid refinement
path, 2-line TLE files, NORAD de-duplication, the default coarse radius and the event values were never exercised.
Verifies: R1 (README)."""
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sgp4.api import Satrec, jday

from screen import load_tles, screen

D = Path(__file__).resolve().parent / "fixtures"
TLE = [str(D / "iridium_33_debris.tle"), str(D / "cosmos_2251_debris.tle")]
START = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def _lines(p):
    return [x for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def test_two_line_files_without_names_and_norad_dedup(tmp_path):
    three = _lines(TLE[0])
    two = [x for x in three if x.startswith(("1 ", "2 "))]
    f2 = tmp_path / "two_line.tle"
    f2.write_text("\n".join(two) + "\n", encoding="utf-8")
    sats3, names3, ids3, _, _ = load_tles([TLE[0]])
    sats2, names2, ids2, _, _ = load_tles([str(f2)])
    assert ids2 == ids3 and names2 == ids2                       # no name line: the NORAD id is the name
    sats_d, _, ids_d, prov, groups = load_tles([TLE[0], str(f2)])
    assert ids_d == ids3 and len(prov) == 2 and set(groups) == {0}  # same objects twice -> counted once


def test_grid_and_linear_refinement_agree():
    lin = screen(TLE, START, 2.0, 60.0, 50.0, 10.0, refine="linear")
    grd = screen(TLE, START, 2.0, 60.0, 50.0, 10.0, refine="grid")
    key = lambda r: {(e["a"], e["b"]): e["miss_km"] for e in r["events"]}
    kl, kg = key(lin), key(grd)
    assert kl.keys() == kg.keys() and len(kl) > 0
    for k in kl:
        assert abs(kl[k] - kg[k]) < 0.05                        # two refinement methods, same encounters


def test_default_coarse_radius_is_derived_from_step():
    a = screen(TLE, START, 1.0, 60.0, None, 10.0)
    b = screen(TLE, START, 1.0, 60.0, 10.0 + 15.5 * 30 + 1.0, 10.0)
    assert [e["miss_km"] for e in a["events"]] == [e["miss_km"] for e in b["events"]]


def test_event_miss_distance_recomputed_independently_with_sgp4():
    r = screen(TLE, START, 2.0, 60.0, 50.0, 10.0)
    sats = {}
    for p in TLE:
        ls = _lines(p)
        for i in range(len(ls) - 1):
            if ls[i].startswith("1 ") and ls[i + 1].startswith("2 "):
                sats.setdefault(ls[i][2:7].strip(), Satrec.twoline2rv(ls[i], ls[i + 1]))
    assert r["events"]
    for e in r["events"][:5]:
        t = datetime.fromisoformat(e["tca_utc"])
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond / 1e6)
        _, ra, _ = sats[e["a"]].sgp4(jd, fr)
        _, rb, _ = sats[e["b"]].sgp4(jd, fr)
        assert abs(float(np.linalg.norm(np.subtract(ra, rb))) - e["miss_km"]) < 0.002
        assert e["miss_km"] <= 10.0 and e["older_tle_age_days"] >= 0
