# -*- coding: utf-8 -*-
"""The evidence bundle is tamper-evident: changing a recorded value must be detected by `star-xc verify-bundle`."""
import json

from star_crosscheck import Engine, crosscheck
from star_crosscheck.cli import main


def test_tampered_bundle_is_detected(tmp_path):
    b = crosscheck("x", {"k": 1}, [Engine("a", "L1", lambda i: 1.0), Engine("b", "L2", lambda i: 1.0)], 1e-9, "u")
    good, bad = tmp_path / "good.json", tmp_path / "bad.json"
    good.write_text(json.dumps([b]), encoding="utf-8")
    b2 = json.loads(json.dumps(b))
    b2["engines"][0]["value"] = [1.5]                     # someone edits a result after the fact
    bad.write_text(json.dumps([b2]), encoding="utf-8")
    assert main(["verify-bundle", str(good)]) == 0
    assert main(["verify-bundle", str(bad)]) == 1
