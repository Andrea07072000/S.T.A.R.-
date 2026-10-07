"""Refusals and range limits for star_wahba.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_wahba as sw

HOSTILE = [None, "x", True, False, float("nan"), float("inf"), -float("inf")]
BAD_VECTORS = [None, "x", (1, 2), (1, 2, 3, 4), (1, True, 3), (1, "2", 3), (1, float("nan"), 3), (1, float("inf"), 3), (0, 0, 0)]


def test_pinned_constants_and_exports():
    assert sw.__version__ == "0.1.0"
    assert sw.__all__ == ["triad", "q_method", "rotation_matrix", "wahba_loss"]
    assert sw.MAX_PAIRS == 1000
    assert sw.PARALLEL == pytest.approx(1e-12, abs=0.0)


@pytest.mark.parametrize("v", BAD_VECTORS)
def test_triad_refuses_bad_vectors(v):
    with pytest.raises(ValueError):
        sw.triad(v, (0, 1, 0), (1, 0, 0), (0, 1, 0))
    with pytest.raises(ValueError):
        sw.triad((1, 0, 0), v, (1, 0, 0), (0, 1, 0))
    with pytest.raises(ValueError):
        sw.triad((1, 0, 0), (0, 1, 0), v, (0, 1, 0))
    with pytest.raises(ValueError):
        sw.triad((1, 0, 0), (0, 1, 0), (1, 0, 0), v)


def test_triad_parallel_and_limit_inside_outside():
    # size of cross = eps for these unit vectors; branch is size < PARALLEL.
    eps_in = sw.PARALLEL * 1.1
    eps_out = sw.PARALLEL * 0.9
    sw.triad((1, 0, 0), (1, eps_in, 0), (0, 1, 0), (0, 1, eps_in))
    with pytest.raises(ValueError, match="parallel"):
        sw.triad((1, 0, 0), (1, eps_out, 0), (0, 1, 0), (0, 1, eps_in))
    with pytest.raises(ValueError, match="parallel"):
        sw.triad((1, 0, 0), (1, eps_in, 0), (0, 1, 0), (0, 1, eps_out))


def test_q_method_and_wahba_loss_contract_on_lists_lengths_counts_weights_q():
    good_refs = [(1, 0, 0), (0, 1, 0)]
    good_bods = [(1, 0, 0), (0, 1, 0)]

    with pytest.raises(ValueError, match="same length"):
        sw.q_method("not-list", good_bods)
    with pytest.raises(ValueError, match="same length"):
        sw.wahba_loss((1, 0, 0, 0), good_refs, "not-list")
    with pytest.raises(ValueError, match="same length"):
        sw.q_method([(1, 0, 0)], good_bods)

    with pytest.raises(ValueError, match="between 2 and 1000"):
        sw.q_method([(1, 0, 0)], [(1, 0, 0)])
    sw.q_method(good_refs, good_bods)
    sw.q_method([(1, 0, 0), (0, 1, 0)] * (sw.MAX_PAIRS // 2), [(1, 0, 0), (0, 1, 0)] * (sw.MAX_PAIRS // 2), [1.0] * sw.MAX_PAIRS)      # corrected by the reviewer: 1000 parallel directions are refused, rightly
    with pytest.raises(ValueError, match="between 2 and 1000"):
        sw.q_method([(1, 0, 0)] * (sw.MAX_PAIRS + 1), [(1, 0, 0)] * (sw.MAX_PAIRS + 1), [1.0] * (sw.MAX_PAIRS + 1))

    with pytest.raises(ValueError, match="as many as the pairs"):
        sw.q_method(good_refs, good_bods, [1.0])

    for badw in [0.0, -1.0, float("nan"), float("inf"), True]:
        with pytest.raises(ValueError, match="positive finite"):
            sw.q_method(good_refs, good_bods, [1.0, badw])

    for badq in [None, "q", (1, 0, 0), (1, 0, 0, 0, 0), (True, 0, 0, 0), (1, float("nan"), 0, 0), (1, float("inf"), 0, 0), (0, 0, 0, 0)]:
        with pytest.raises(ValueError):
            sw.rotation_matrix(badq)
        with pytest.raises(ValueError):
            sw.wahba_loss(badq, good_refs, good_bods)


def test_q_method_refuses_non_observable_parallel_reference_set():
    eps = sw.PARALLEL * 0.9
    refs = [(1, 0, 0), (1, eps, 0)]
    bods = [(1, 0, 0), (0, 1, 0)]
    with pytest.raises(ValueError, match="do not fix an attitude"):
        sw.q_method(refs, bods)
