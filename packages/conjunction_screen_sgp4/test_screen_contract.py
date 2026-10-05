"""Contract of the screening report, each field recomputed independently (mutation survivors 2026-10-04, score 0.502:
3-line name parsing, provenance, epoch range, ages, ordering, cross-only and the CLI were never checked).
Verifies: R1, R2, R3 (README)."""
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sgp4.api import Satrec

from screen import load_tles, main, screen

D = Path(__file__).resolve().parent / "fixtures"


def resum(line):
    # well-formed TLE line: the screening now rejects bad checksums, so physically-bad test TLEs must be well formed
    return line[:68] + str(sum(int(c) if c.isdigit() else (1 if c == "-" else 0) for c in line[:68]) % 10)
TLE = [str(D / "iridium_33_debris.tle"), str(D / "cosmos_2251_debris.tle")]
START = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
RUN = screen(TLE, START, 2.0, 60.0, 50.0, 10.0)


def _triples(p):
    ls = [x.rstrip() for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]
    return [(ls[i - 1].strip() if i and not ls[i - 1].startswith(("1 ", "2 ")) else None, ls[i], ls[i + 1])
            for i in range(len(ls) - 1) if ls[i].startswith("1 ") and ls[i + 1].startswith("2 ")]


def test_three_line_names_are_stripped_and_kept_in_order(tmp_path):
    f = tmp_path / "mix.tle"
    t = _triples(TLE[0])[:3]
    f.write_text(f"junk header\n{t[0][0]}   \n{t[0][1]}\n{t[0][2]}\n{t[1][1]}\n{t[1][2]}\nORPHAN NAME\n{t[2][0]}\n{t[2][1]}\n{t[2][2]}\n",
                 encoding="utf-8")
    sats, names, ids, prov, groups = load_tles([str(f)])
    assert names == [t[0][0], t[1][1][2:7].strip(), t[2][0]] and ids == [x[1][2:7].strip() for x in t]
    raw = f.read_bytes()
    assert prov == [{"file": str(f), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "rejected": {}}] and groups == [0, 0, 0]


def test_groups_follow_the_file_index():
    _, _, ids, prov, groups = load_tles(TLE)
    n0 = len({x[1][2:7].strip() for x in _triples(TLE[0])})
    assert groups[:n0] == [0] * n0 and set(groups[n0:]) == {1} and len(prov) == 2


def test_epoch_range_and_object_count_recomputed():
    eps = [Satrec.twoline2rv(a, b) for p in TLE for _, a, b in _triples(p)]
    jds = [s.jdsatepoch + s.jdsatepochF for s in eps]
    iso = lambda jd: datetime.fromtimestamp((jd - 2440587.5) * 86400, timezone.utc).isoformat(timespec="seconds")
    assert RUN["tle_epoch_range_utc"] == [iso(min(jds)), iso(max(jds))]
    assert RUN["objects"] == len({s.satnum for s in eps})


def test_events_sorted_inside_window_with_correct_ages():
    ev = RUN["events"]
    assert ev and [e["miss_km"] for e in ev] == sorted(e["miss_km"] for e in ev)
    assert all(e["miss_km"] <= 10.0 for e in ev) and RUN["events_below_final_km"] == len(ev)
    ep = {str(Satrec.twoline2rv(a, b).satnum): Satrec.twoline2rv(a, b) for p in TLE for _, a, b in _triples(p)}
    for e in ev:
        t = datetime.fromisoformat(e["tca_utc"])
        assert START - timedelta(minutes=2) <= t <= START + timedelta(hours=2, minutes=2)
        jd_t = t.timestamp() / 86400 + 2440587.5
        older = min(ep[e["a"]].jdsatepoch + ep[e["a"]].jdsatepochF, ep[e["b"]].jdsatepoch + ep[e["b"]].jdsatepochF)
        assert abs(e["older_tle_age_days"] - (jd_t - older)) < 0.05
        assert e["a"] != e["b"]


def test_counts_and_config_echo():
    assert RUN["config"] == {"start_utc": START.isoformat(), "hours": 2.0, "step_s": 60.0, "coarse_km": 50.0,
                             "final_km": 10.0, "cross_only": False, "refine": "linear"}
    # a pair can meet more than once in 2 h (87 encounters from 79 pairs on this fixture), so the valid relations are:
    assert RUN["coarse_encounters"] >= len(RUN["events"])
    assert RUN["coarse_candidate_pairs"] >= len({(e["a"], e["b"]) for e in RUN["events"]})
    import screen as _screen_module   # the IMPORTED module (installed or in-tree), not a file next to this test
    assert RUN["code_sha256"] == hashlib.sha256(Path(_screen_module.__file__).read_bytes()).hexdigest()
    assert set(RUN["runtime_s"]) == {"load", "coarse", "total"} and RUN["runtime_s"]["total"] >= RUN["runtime_s"]["load"]


def test_cross_only_keeps_only_pairs_between_files():
    _, _, ids, _, groups = load_tles(TLE)
    g = dict(zip(ids, groups))
    r = screen(TLE, START, 2.0, 60.0, 50.0, 10.0, cross_only=True)
    assert all(g[e["a"]] != g[e["b"]] for e in r["events"])
    assert len(r["events"]) <= len(RUN["events"])


def test_cli_writes_the_full_report(tmp_path, capsys):
    out = tmp_path / "sub" / "r.json"
    rc = main(TLE + ["--start", "2026-10-02T12:00:00", "--hours", "2", "--step", "60", "--coarse-km", "50",
                     "--final-km", "10", "--out", str(out)])
    assert rc == 0 and out.exists()
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["events"] == RUN["events"] and rep["config"]["start_utc"] == START.isoformat()
    printed = capsys.readouterr().out
    assert '"objects": %d' % RUN["objects"] in printed and printed.rstrip().splitlines()[-1].startswith("prime 5:")


def test_default_coarse_radius_is_reported_with_its_formula():
    r = screen(TLE, START, 0.5, 30.0, None, 7.0)
    assert r["config"]["coarse_km"] == 7.0 + 15.5 * 30.0 / 2 + 1.0


def test_cli_file_format_and_summary_excludes_bulk_fields(tmp_path, capsys):
    out = tmp_path / "r.json"
    main(TLE + ["--start", "2026-10-02T12:00:00", "--hours", "0.5", "--step", "60", "--final-km", "10", "--out", str(out)])
    text = out.read_text(encoding="utf-8")
    assert text == json.dumps(json.loads(text), indent=1, ensure_ascii=False)
    printed = capsys.readouterr().out
    summary = json.loads(printed[: printed.index("prime 5:")])
    assert "events" not in summary and "inputs" not in summary and summary["config"]["coarse_km"] == 10 + 15.5 * 30 + 1
    first5 = json.loads(printed.split("prime 5:", 1)[1])
    assert first5 == json.loads(text)["events"][:5]


def test_refine_tca_on_slow_exactly_linear_motion():
    # |dv| = 0.5 km/s (|dv|^2 < 1): closest approach of r(t) = (100 - 0.5 t, 3, 0) at t* = 200 s, clipped to +-step
    from screen import refine_tca

    def st(t):
        return ((100.0 - 0.5 * t, 3.0, 0.0), (-0.5, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    t, miss = refine_tca(st, step=500.0)
    assert abs(t - 200.0) < 1e-9 and abs(miss - 3.0) < 1e-9
    t2, miss2 = refine_tca(st, step=60.0)                       # clipped: minimum not reachable inside +-60 s
    assert t2 == 60.0 and abs(miss2 - math.hypot(70.0, 3.0)) < 1e-9
    assert refine_tca(lambda t: None, 60.0) is None


def test_reported_precision_on_both_refinements():
    for mode in ("linear", "grid"):
        r = screen(TLE, START, 1.0, 60.0, 50.0, 10.0, refine=mode)
        assert r["events"]
        for e in r["events"]:
            assert round(e["miss_km"], 3) == e["miss_km"] and round(e["older_tle_age_days"], 2) == e["older_tle_age_days"]


def test_cli_defaults_reach_screen(monkeypatch, tmp_path):
    import screen as S
    seen = {}

    def fake(paths, start, hours, step, coarse_km, final_km, cross_only, refine):
        seen.update(paths=paths, start=start, hours=hours, step=step, coarse_km=coarse_km, final_km=final_km,
                    cross_only=cross_only, refine=refine)
        return {"events": [], "inputs": [], "objects": 0}
    monkeypatch.setattr(S, "screen", fake)
    assert S.main(["a.tle", "b.tle", "--start", "2026-10-02T12:00:00", "--out", str(tmp_path / "o.json")]) == 0
    assert seen == {"paths": ["a.tle", "b.tle"], "start": START, "hours": 24.0, "step": 60.0, "coarse_km": None,
                    "final_km": 5.0, "cross_only": False, "refine": "linear"}
    S.main(["a.tle", "--start", "2026-10-02T12:00:00", "--out", str(tmp_path / "o.json"), "--cross-only", "--refine", "grid"])
    assert seen["cross_only"] is True and seen["refine"] == "grid" and seen["start"].tzinfo == timezone.utc


def test_runtime_is_reported_in_hundredths():
    assert all(round(v, 2) == v for v in RUN["runtime_s"].values())


def test_co_located_twin_is_a_formation_not_an_event(tmp_path):
    # the same orbit under two NORAD numbers: close on every sample -> excluded as formation, never reported
    name, l1, l2 = _triples(TLE[0])[0]
    twin1, twin2 = l1[:2] + "99999" + l1[7:], l2[:2] + "99999" + l2[7:]
    f = tmp_path / "twin.tle"
    f.write_text(f"{name}\n{l1}\n{l2}\nTWIN\n{twin1}\n{twin2}\n", encoding="utf-8")
    r = screen([str(f)], START, 1.0, 60.0, 50.0, 10.0)
    assert r["formation_pairs_excluded"] == 1 and r["events"] == [] and r["coarse_candidate_pairs"] == 1


def test_grid_refinement_reports_tca_inside_window_and_correct_ages():
    r = screen(TLE, START, 1.0, 60.0, 50.0, 10.0, refine="grid")
    ep = {str(Satrec.twoline2rv(a, b).satnum): Satrec.twoline2rv(a, b) for p in TLE for _, a, b in _triples(p)}
    assert r["events"]
    for e in r["events"]:
        t = datetime.fromisoformat(e["tca_utc"])
        assert START - timedelta(minutes=1) <= t <= START + timedelta(hours=1, minutes=1)
        jd_t = t.timestamp() / 86400 + 2440587.5
        older = min(ep[e["a"]].jdsatepoch + ep[e["a"]].jdsatepochF, ep[e["b"]].jdsatepoch + ep[e["b"]].jdsatepochF)
        assert abs(e["older_tle_age_days"] - (jd_t - older)) < 0.01


def test_loader_survives_dangling_and_trailing_lines(tmp_path):
    name, l1, l2 = _triples(TLE[0])[0]
    for text in (f"{name}\n{l1}\n{l2}\nTRAILING JUNK\n", f"{l1}\n{l2}\nNAME ONLY\n{l1[:2]}99998{l1[7:]}\n",
                 f"{name}\n{l1}\n{l2}\n{name}\n{l1}\n", f"{l1}\n{l2}\n"):
        f = tmp_path / "t.tle"
        f.write_text(text, encoding="utf-8")
        sats, names, ids, _, _ = load_tles([str(f)])
        assert ids == [l1[2:7].strip()], text


def test_cli_requires_start_and_out(tmp_path):
    import pytest
    for args in ([TLE[0], "--out", str(tmp_path / "x.json")], [TLE[0], "--start", "2026-10-02T12:00:00"]):
        with pytest.raises(SystemExit):
            main(args)


def test_cli_nested_output_rerun_and_non_ascii_names(tmp_path, capsys):
    name, l1, l2 = _triples(TLE[0])[0]
    f = tmp_path / "n.tle"
    f.write_text(f"ÉCLAIR-Δ\n{l1}\n{l2}\n" + "".join(f"{n}\n{a}\n{b}\n" for n, a, b in _triples(TLE[1])[:40]), encoding="utf-8")
    out = tmp_path / "a" / "b" / "r.json"
    args = [str(f), "--start", "2026-10-02T12:00:00", "--hours", "0.5", "--final-km", "2000", "--out", str(out)]
    assert main(args) == 0 and main(args) == 0           # nested dirs created; re-run into the same dir is allowed
    text = out.read_text(encoding="utf-8")
    assert "ÉCLAIR-Δ" in text and chr(92) + "u00c9" not in text      # no escaped form: ensure_ascii=False
    printed = capsys.readouterr().out
    assert "ÉCLAIR-Δ" in printed and printed.count('\n "') >= 5   # indented summary, non-ASCII kept


def test_an_unpropagatable_object_does_not_change_the_other_events(tmp_path):
    # coarse samples with an SGP4 error are masked per object: adding a broken object must leave every event unchanged
    name, l1, l2 = _triples(TLE[0])[0]
    bad2 = l2[:26] + "9999999" + l2[33:]                # eccentricity 0.9999999: perigee inside the Earth
    src = "".join(f"{n}\n{a}\n{b}\n" for p in TLE for n, a, b in _triples(p))
    f0, f1 = tmp_path / "base.tle", tmp_path / "with_bad.tle"
    f0.write_text(src, encoding="utf-8")
    bad_l1, bad_l2 = resum(l1[:2] + "99999" + l1[7:]), resum("2 99999" + bad2[7:])
    f1.write_text(src + f"BAD\n{bad_l1}\n{bad_l2}\n", encoding="utf-8")
    a = screen([str(f0)], START, 1.0, 60.0, 50.0, 10.0)
    b = screen([str(f1)], START, 1.0, 60.0, 50.0, 10.0)
    assert b["objects_with_sgp4_error"] == 1 and a["objects_with_sgp4_error"] == 0
    assert b["events"] == a["events"] and b["events"]


def test_loader_terminates_on_every_layout(tmp_path):
    # an index that does not advance would loop forever: run the loader in a child process with a hard timeout
    import subprocess
    import sys
    name, l1, l2 = _triples(TLE[0])[0]
    f = tmp_path / "l.tle"
    f.write_text(f"{l1}\n{l2}\n{name}\n{l1}\n{l2}\njunk\n", encoding="utf-8")
    code = f"import sys; sys.path.insert(0, {str(Path(__file__).parent)!r}); from screen import load_tles; print(len(load_tles([{str(f)!r}])[0]))"
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and r.stdout.strip() == "1", r.stderr[-300:]


def test_environment_records_the_running_python():
    import platform
    assert RUN["environment"]["python"] == platform.python_version()


def test_refine_tca_iteration_count_and_zero_offset():
    from screen import refine_tca
    # Mutants line 68 (iterations=3 mutated to 4/2) and line 72 (tsec=0.0 mutated to 1.0)
    # A case that needs exactly 3 iterations to converge below 1e-4 from tsec=0.0:
    calls = []
    def st_curved(t):
        calls.append(t)
        # quadratic trajectory r(t) = (t - 15.0)^2 + 2.0
        # dr = (t - 15.0)^2 + 2.0, dv = 2*(t - 15.0)
        dt_val = t - 15.0
        r = [dt_val * dt_val + 2.0, 0.0, 0.0]
        v = [2.0 * dt_val, 0.0, 0.0]
        return (r, v, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0])

    res = refine_tca(st_curved, step=30.0, iterations=1)
    assert res is not None
    # If starting from tsec != 0.0, the first evaluated offset is not 0.0:
    assert abs(calls[0] - 0.0) < 1e-12

    # Line 81 mutant: break when abs(dt) < 1e-4
    # On an already perfect TCA at t=0, dt is 0 -> loop breaks immediately with 1 call before final eval
    calls.clear()
    def st_exact_min(t):
        calls.append(t)
        return ([2.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
    res_exact = refine_tca(st_exact_min, step=10.0, iterations=5)
    assert res_exact is not None and abs(res_exact[0]) < 1e-9
    # Exactly 2 calls (1 inside loop which breaks due to dt=0 < 1e-4, 1 final state_at call):
    assert len(calls) == 2


def test_grid_refinement_subtraction_and_selection():
    # Kills line 196 (argmin), line 198 (replacement comparison), line 206 (t_total = time.perf_counter() - t0)
    res = screen(TLE, START, 1.0, 60.0, 50.0, 10.0, refine="grid")
    assert res["runtime_s"]["total"] >= res["runtime_s"]["coarse"]
    assert res["events"]
    # Check that grid miss distances are non-negative and strictly within 10 km
    for e in res["events"]:
        assert 0.0 <= e["miss_km"] <= 10.0


def test_screening_discretization_and_counters():
    # Line 103 mutant: nt = int(hours * 3600 / step) + 1
    # For hours=1.0, step=60.0, nt must be exactly 61
    r = screen(TLE, START, 1.0, 60.0, 50.0, 10.0)
    assert r["candidates_dropped_sgp4_error"] == 0
    # Line 146: coarse runtime must be non-negative and less than or equal to total runtime
    assert 0.0 <= r["runtime_s"]["coarse"] <= r["runtime_s"]["total"]
    assert r["runtime_s"]["load"] >= 0.0




def test_malformed_tles_are_rejected_and_counted_by_reason(tmp_path):
    from screen import tle_problem
    t = _triples(TLE[0])[:4]
    (n0, a0, b0), (n1, a1, b1), (n2, a2, b2), (n3, a3, b3) = t
    bad_ck = b1[:68] + str((int(b1[68]) + 1) % 10)                       # checksum broken
    mism = resum(b2[:2] + f"{(int(b2[2:7]) + 1) % 100000:05d}" + b2[7:])     # satnum differs from line 1
    short = b3[:68]                                                    # 68 characters
    f = tmp_path / "m.tle"
    f.write_text(f"{n0}\n{a0}\n{b0}\n{n1}\n{a1}\n{bad_ck}\n{n2}\n{a2}\n{mism}\n{n3}\n{a3}\n{short}\n", encoding="utf-8")
    sats, names, ids, prov, _ = load_tles([str(f)])
    assert ids == [a0[2:7].strip()] and prov[0]["rejected"] == {"checksum": 1, "satnum_mismatch": 1, "length": 1}
    assert tle_problem(a0, b0) is None and tle_problem(a1, bad_ck) == "checksum"
    assert tle_problem(a2, mism) == "satnum_mismatch" and tle_problem(a3, short) == "length"
    r = screen([str(f)], START, 0.5, 60.0, 50.0, 10.0)
    assert r["tles_rejected_malformed"] == 3 and r["objects"] == 1 and RUN["tles_rejected_malformed"] == 0
