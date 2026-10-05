"""Tests written from mutation survivors (12_EVIDENCE/mutation/star_cdm_20261004.json, score 0.710). One survivor
group was dead code (a units table overwritten on the next line): removed, not tested."""
from pathlib import Path

from star_cdm import UNITS, consistency_report, parse_cdm

F = Path(__file__).resolve().parent / "fixtures"
EX1 = (F / "ccsds508_example_1.kvn").read_text(encoding="utf-8")


def test_covariance_units_by_number_of_rate_terms():
    assert UNITS["CR_R"] == "m**2" and UNITS["CRDOT_R"] == "m**2/s" and UNITS["CNDOT_NDOT"] == "m**2/s**2"


def test_day_of_year_dates_are_accepted():
    c = parse_cdm(EX1.replace("2010-03-13T22:37:52.618", "2010-072T22:37:52.618"))
    assert c["header"]["TCA"].isoformat() == "2010-03-13T22:37:52.618000"


def test_minus_normalisation_reports_the_count():
    c = parse_cdm(EX1)
    assert any(w.startswith(f"normalised {EX1.count(chr(0x2212))} ") for w in c["warnings"])
    assert EX1.count(chr(0x2212)) == 19


def test_default_tolerance_is_one_metre():
    c = parse_cdm(EX1)                                      # states give 715.75 m, declared 715 m: within 1 m
    assert consistency_report(c)["flags"] == []
    c["header"]["MISS_DISTANCE"] = 714.5                    # 1.25 m off: flagged with the default tolerance
    assert "STATES_INCONSISTENT_WITH_MISS_DISTANCE" in consistency_report(c)["flags"]
    assert consistency_report(c, tol_m=2.0)["flags"] == []


def test_consistent_rtn_is_not_flagged():
    c = parse_cdm(EX1)
    c["header"].update({"RELATIVE_POSITION_R": 3.0, "RELATIVE_POSITION_T": 4.0, "RELATIVE_POSITION_N": 0.0, "MISS_DISTANCE": 5.0})
    r = consistency_report(c)
    assert r["from_rtn_m"] == 5.0 and "RTN_INCONSISTENT_WITH_MISS_DISTANCE" not in r["flags"]
