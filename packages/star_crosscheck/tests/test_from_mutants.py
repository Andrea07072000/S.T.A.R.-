"""Tests written from mutation survivors (12_EVIDENCE/mutation/star_crosscheck_core_20261005.json, score 0.6136):
the tolerance boundary, norm mode, isolated-runner parsing and error tails, timings, environment and hash
canonicalisation were not pinned."""
import math
import platform
import sys

import pytest

from star_crosscheck import AGREE, DISAGREE, Engine, crosscheck
from star_crosscheck.core import _diff, _run_isolated, bundle_sha256


def const(name, lineage, v):
    return Engine(name, lineage, func=lambda _i: v)


def test_tolerance_is_inclusive_for_engines_and_reference():
    b = crosscheck("q", {}, [const("a", "L1", 1.0), const("b", "L2", 1.5)], tolerance=0.5, unit="u")
    assert b["verdict"] == AGREE and b["pairs"][0]["diff"] == 0.5 and b["pairs"][0]["within_tol"]
    r = crosscheck("q", {}, [const("a", "L1", 1.0), const("b", "L2", 1.0)], 0.5, "u", reference={"value": 1.5})
    assert r["reference"]["within_tol"] and r["verdict"] == AGREE
    r2 = crosscheck("q", {}, [const("a", "L1", 1.0), const("b", "L2", 1.0)], 0.5, "u", reference={"value": 1.75})
    assert not r2["reference"]["within_tol"] and r2["verdict"] == DISAGREE


def test_norm_mode_is_euclidean_distance():
    assert _diff([1.0, 2.0, 2.0], [0.0, 0.0, 0.0], "norm") == 3.0
    assert _diff([3.0, 4.0], [0.0, 0.0], "norm") == 5.0 and _diff([3.0, 4.0], [0.0, 0.0], "max_abs") == 4.0
    assert _diff([1.0], [1.0, 2.0], "norm") == math.inf


def test_isolated_runner_parses_the_last_marker_and_reports_stderr_tail():
    code = "import sys\nVERSION='9'\ndef compute(i):\n    sys.stdout.write('@@STAR_XC@@noise')\n    return i['x'] * 2\n"
    assert _run_isolated(sys.executable, code, {"x": 21}, 60) == (42, "9")
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        _run_isolated(sys.executable, f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(3)\n", {}, 60)
    assert str(e.value).endswith(msg[-300:]) and "A" not in str(e.value).split("rc=3): ", 1)[1]


def test_engine_defaults_and_timings():
    e = const("a", "L", 2.0)
    assert e.timeout_s == 120.0 and e.version == "unknown"
    r = e.run({})
    assert r["value"] == [2.0] and 0.0 <= r["elapsed_s"] < 5.0 and round(r["elapsed_s"], 4) == r["elapsed_s"]
    f = Engine("bad", "L", func=lambda _i: 1 / 0).run({})
    assert f["state"] == "FAILED" and 0.0 <= f["elapsed_s"] < 5.0 and round(f["elapsed_s"], 4) == f["elapsed_s"]


def test_environment_and_hash_canonicalisation():
    b = crosscheck("q", {"k": 1, "j": 2}, [const("a", "L1", 1.0), const("b", "L2", 1.0)], 0.1, "u")
    assert b["environment"]["python"] == platform.python_version()
    permuted = {k: b[k] for k in reversed(list(b))}
    permuted["inputs"] = {"j": 2, "k": 1}
    assert bundle_sha256(permuted) == bundle_sha256(b) == b["sha256"]
