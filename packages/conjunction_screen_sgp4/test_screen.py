# -*- coding: utf-8 -*-
"""Regressione dello screening SGP4 (S.T.A.R., 2026-10-03). Fissa le proprieta' verificate in EXP-C01/EXP-003:
(1) il rifinimento lineare e quello a griglia danno gli stessi eventi; (2) dimezzare il passo non cambia gli eventi
(convergenza); (3) il dump e' completo (niente taglio top-N). Fixture: TLE reali Iridium-33 + Cosmos-2251 (sha256 nel
manifest dei dati), finestra 2 h. Questi test FALLISCONO se il rifinimento o la ricerca grossolana regrediscono.
Verifies: R1, R2 (README)."""
from datetime import datetime, timezone
from pathlib import Path

from screen import screen

HERE = Path(__file__).resolve().parent

def resum(line):
    # well-formed TLE line: the screening now rejects bad checksums, so physically-bad test TLEs must be well formed
    return line[:68] + str(sum(int(c) if c.isdigit() else (1 if c == '-' else 0) for c in line[:68]) % 10)


D = HERE / "fixtures"
TLE = [str(D / "iridium_33_debris.tle"), str(D / "cosmos_2251_debris.tle")]
START = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def _keys(res):
    return {(e["a"], e["b"], round(datetime.fromisoformat(e["tca_utc"]).timestamp() / 300)): e["miss_km"] for e in res["events"]}


def test_linear_equals_grid_refinement():
    lin = screen(TLE, START, 2, 2, None, 5.0, refine="linear")
    grd = screen(TLE, START, 2, 2, None, 5.0, refine="grid")
    a, b = _keys(lin), _keys(grd)
    assert set(a) == set(b) and len(a) > 0
    assert max(abs(a[k] - b[k]) for k in a) < 0.01


def test_step_convergence():
    s2 = _keys(screen(TLE, START, 2, 2, None, 5.0))
    s10 = _keys(screen(TLE, START, 2, 10, None, 5.0))
    assert set(s2) == set(s10)


def test_full_dump_not_truncated():
    res = screen(TLE, START, 2, 2, None, 50.0)          # soglia larga: molti eventi
    assert len(res["events"]) == res["events_below_final_km"] > 200


def test_unpropagatable_tle_is_counted_not_hidden(tmp_path):
    good = [x for x in (D / "iridium_33_debris.tle").read_text(encoding="utf-8").splitlines() if x.strip()]
    l1, l2 = good[1], good[2]
    bad2 = l2[:26] + "9999999" + l2[33:]                  # eccentricity 0.9999999: perigee inside the Earth
    f = tmp_path / "bad.tle"
    f.write_text("\n".join([good[0], l1, l2, "BAD OBJECT", resum(l1[:2] + "99999" + l1[7:]), resum("2 99999" + bad2[7:])]) + "\n", encoding="utf-8")
    res = screen([str(f)], START, 2.0, 60.0, 50.0, 10.0)
    assert res["objects_with_sgp4_error"] >= 1 and "candidates_dropped_sgp4_error" in res


def test_empty_catalogue_is_an_explicit_error(tmp_path):
    import pytest as _pt
    f = tmp_path / "empty.tle"
    f.write_text("NOT A TLE\n", encoding="utf-8")
    with _pt.raises(ValueError, match="no valid TLE"):
        screen([str(f)], START, 1.0, 60.0, 50.0, 10.0)


def test_screening_is_deterministic():
    a = screen(TLE, START, 2.0, 60.0, 50.0, 10.0)
    b = screen(TLE, START, 2.0, 60.0, 50.0, 10.0)
    assert a["events"] == b["events"] and a["objects"] == b["objects"]


def test_screening_counts_are_consistent():
    r = screen(TLE, START, 2.0, 60.0, 50.0, 10.0)
    assert r["coarse_candidate_pairs"] >= 0 and r["coarse_encounters"] >= len(r["events"])
    assert r["formation_pairs_excluded"] >= 0 and r["objects_with_sgp4_error"] <= r["objects"]
