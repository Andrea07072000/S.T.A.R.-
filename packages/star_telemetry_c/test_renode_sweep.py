"""Sweep stage: unchanged star_aos.c bare-metal on 13 more Renode-simulated STM32 microcontrollers
(Cortex-M0, M0+, M3, M4, M7, M33), one test per microcontroller, plus two negative controls that prove the check can fail.
Skips ONLY if Renode or arm-none-eabi-gcc is absent. Simulated models: no physical hardware, no timing claimed.
Verifies: R5 (README)."""
import shutil

import pytest

import sweep_renode_stm32 as sweep


def _tools():
    return bool(shutil.which("wsl.exe")) and sweep.wsl("command -v renode && command -v arm-none-eabi-gcc").returncode == 0


@pytest.fixture(scope="module")
def ref():
    if not _tools():
        pytest.skip("Renode or arm-none-eabi-gcc not installed")
    return sweep.reference()


def test_the_target_table_is_pinned():
    assert len(sweep.TARGETS) == 13
    assert sorted({t[1] for t in sweep.TARGETS.values()}) == ["cortex-m0", "cortex-m0plus", "cortex-m3", "cortex-m33", "cortex-m4", "cortex-m7"]
    assert all(t[0].startswith("platforms/cpus/stm32") and t[4] in (0, 1) and t[5] == 0x08000000 for t in sweep.TARGETS.values())
    assert not {"stm32f4", "stm32f103", "stm32f746"} & set(sweep.TARGETS)          # covered by their own tests


@pytest.mark.parametrize("name", sorted(sweep.TARGETS))
def test_firmware_on_simulated_stm32_matches_python(ref, name):
    raw, expected = ref
    r = sweep.run_target(name, raw, expected)
    assert r["status"] == "PASS", r
    assert r["mismatching_frames"] == [] and r["corrupted_frame_rejected"] is True and len(r["output_sha256"]) == 16


def test_negative_controls_the_check_can_fail(ref, monkeypatch):
    raw, expected = ref
    # firmware built for USART2 while USART1 is captured: nothing must come out, and that must not pass
    monkeypatch.setitem(sweep.TARGETS, "neg_wrong_uart", ("platforms/cpus/stm32f429.repl", "cortex-m4", "usart1", 0x40004400, 0, 0x08000000))
    r = sweep.run_target("neg_wrong_uart", raw, expected)
    assert r["status"] == "NO_OUTPUT" and r["lines"] == 0 and r["done"] is False
    # a reference that differs in one field of one frame must be reported with the frame index
    altered = [dict(e) for e in expected]
    altered[2]["vcfc"] += 1
    r = sweep.run_target("stm32f429", raw, altered)
    assert r["status"] == "MISMATCH" and r["mismatching_frames"] == [2]
