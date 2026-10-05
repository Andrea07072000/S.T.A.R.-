"""Reproducible benchmark: re-run the Orekit CdmParser (WSL /root/orekit_venv, OpenJDK 17) on the corrected official
examples and compare 6 fields with star_cdm. Skips ONLY if the oracle runtime is absent (explicit reason); any
disagreement or oracle error is a failure.
Verifies: R3 (README)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from star_cdm import parse_cdm

HERE = Path(__file__).resolve().parent
FILES = [f"fixtures/corrected/example_{n}.kvn" for n in (1, 2, 3)]


def _wsl(p: Path) -> str:
    s = str(p).replace("\\", "/")
    return "/mnt/" + s[0].lower() + s[2:]


@pytest.fixture(scope="module")
def oracle():
    if not shutil.which("wsl.exe"):
        pytest.skip("WSL not available: Orekit oracle runtime absent")
    if subprocess.run(["wsl.exe", "-e", "test", "-x", "/root/orekit_venv/bin/python"]).returncode != 0:
        pytest.skip("Orekit oracle runtime /root/orekit_venv not installed")
    out = HERE / "orekit_oracle_output.json"
    cmd = f"cd '{_wsl(HERE)}' && /root/orekit_venv/bin/python orekit_probe.py {' '.join(FILES)} 2>/dev/null | tail -1 > '{_wsl(out)}'"
    r = subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def test_star_cdm_matches_orekit_on_official_examples(oracle):
    for f in FILES:
        o = oracle[f]
        assert o["ok"], o
        c = parse_cdm((HERE / f).read_text(encoding="utf-8"))
        assert c["header"]["MISS_DISTANCE"] == o["miss_m"]
        assert c["header"]["TCA"].isoformat()[:23] == o["tca"][:23]
        assert abs(c["object1"]["X"] * 1000 - o["o1_x_m"]) < 1e-6
        assert abs(c["object1"]["Z_DOT"] * 1000 - o["o1_zdot_ms"]) < 1e-9
        assert c["object1"]["CT_T"] == o["o1_ct_t"] and c["object2"]["OBJECT_NAME"] == o["o2_name"]
