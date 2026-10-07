# -*- coding: utf-8 -*-
"""Guard tests added by the reviewer on 2026-10-07, after the corrected mutation runner measured core.py at 0.82, below
the present 0.85 gate. The Euclidean distance of the 'norm' mode had no test that a wrong sign would fail: for a tool
whose job is to compare numbers, that is the first thing to pin."""
import math

import pytest

from star_crosscheck import AGREE, DISAGREE, Engine, crosscheck
from star_crosscheck import core
from star_crosscheck.core import _diff


def const(name, lineage, value):
    return Engine(name=name, lineage=lineage, func=lambda inputs: value)


def test_distance_between_two_vectors_by_hand():
    assert _diff([1.0, 2.0], [4.0, 6.0], "norm") == 5.0                      # (3, 4)
    assert _diff([1.0, -2.0], [4.0, 2.0], "norm") == 5.0
    assert _diff([0.0, 0.0, 0.0], [2.0, 3.0, 6.0], "norm") == 7.0
    assert _diff([5.0], [2.0], "norm") == 3.0 and _diff([2.0], [5.0], "norm") == 3.0
    assert _diff([1.0, 2.0], [4.0, 6.0], "max_abs") == 4.0 and _diff([1.0, 9.0], [4.0, 6.0], "max_abs") == 3.0
    assert _diff([7.0, 7.0], [7.0, 7.0], "norm") == 0.0 and _diff([7.0, 7.0], [7.0, 7.0], "max_abs") == 0.0
    assert _diff([1.0, 2.0], [1.0, 2.0, 3.0], "norm") == math.inf and _diff([1.0], [1.0, 2.0], "max_abs") == math.inf


def test_norm_mode_decides_the_verdict_at_the_distance():
    engines = [const("a", "one", [1.0, 2.0]), const("b", "two", [4.0, 6.0])]     # 5 apart as vectors, 4 apart component by component
    assert crosscheck("q", {}, engines, 5.0, "m", diff_mode="norm")["verdict"] == AGREE
    assert crosscheck("q", {}, engines, 4.999, "m", diff_mode="norm")["verdict"] == DISAGREE
    assert crosscheck("q", {}, engines, 4.5, "m", diff_mode="max_abs")["verdict"] == AGREE
    assert crosscheck("q", {}, engines, 4.5, "m", diff_mode="norm")["pairs"][0]["diff"] == 5.0


def test_zero_tolerance_is_a_valid_request_for_identical_results():
    engines = [const("a", "one", 1.5), const("b", "two", 1.5)]
    out = crosscheck("q", {}, engines, 0, "m")
    assert out["verdict"] == AGREE and out["pairs"][0]["within_tol"] is True
    assert crosscheck("q", {}, [const("a", "one", 1.5), const("b", "two", math.nextafter(1.5, 2.0))], 0.0, "m")["verdict"] == DISAGREE
    for bad in (-1e-300, -1.0):
        with pytest.raises(ValueError, match="tolerance must be finite"):
            crosscheck("q", {}, engines, bad, "m")


def test_a_reference_without_its_own_tolerance_is_held_to_the_engine_tolerance():
    engines = [const("a", "one", 1.0), const("b", "two", 1.0)]
    out = crosscheck("q", {}, engines, 1e-9, "m", reference={"value": 1.5, "source": "a printed table"})
    assert out["reference"]["ref_tolerance"] == 1e-9 and out["reference"]["within_tol"] is False and out["verdict"] == DISAGREE
    assert out["reference"]["max_dev"] == 0.5
    out = crosscheck("q", {}, engines, 1e-9, "m", reference={"value": 1.0, "source": "a printed table"})
    assert out["reference"]["within_tol"] is True and out["verdict"] == AGREE
    out = crosscheck("q", {}, engines, 1e-9, "m", reference={"value": 1.4, "source": "a printed table", "tolerance": 0.5})
    assert out["reference"]["ref_tolerance"] == 0.5 and out["reference"]["within_tol"] is True
    with pytest.raises(ValueError, match="reference tolerance"):
        crosscheck("q", {}, engines, 1e-9, "m", reference={"value": 1.0, "source": "x", "tolerance": -0.5})


def test_error_text_is_kept_up_to_400_characters():
    def fails(inputs):
        raise ValueError("x" * 1000)

    r = Engine(name="e", lineage="one", func=fails).run({})
    assert r["state"] == "FAILED" and len(r["error"]) == 400 and r["error"].startswith("ValueError: xxx") and "value" not in r

    def short(inputs):
        raise KeyError("missing")

    assert Engine(name="e", lineage="one", func=short).run({})["error"] == "KeyError: 'missing'"


def test_elapsed_time_is_recorded_to_four_decimals(monkeypatch):
    ticks = iter([10.0, 11.23456789, 20.0, 20.98765432])
    monkeypatch.setattr(core.time, "perf_counter", lambda: next(ticks))
    assert Engine(name="e", lineage="one", func=lambda inputs: 1.0).run({})["elapsed_s"] == 1.2346

    def fails(inputs):
        raise ValueError("no")

    assert Engine(name="e", lineage="one", func=fails).run({})["elapsed_s"] == 0.9877
