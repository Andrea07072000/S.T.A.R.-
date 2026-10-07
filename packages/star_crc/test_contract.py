"""Refusals and hard limits of star_crc: hostile values for each argument of each public function, edge-of-range checks, pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import pytest

import star_crc as sc


HOSTILE_DATA = ["abc", None, [1, 2, 3], memoryview(b"x"), 7]
GOOD = b"\x01\x23"


def test_pinned_constants_and_exports():
    assert sc.__version__ == "0.1.0"
    assert sc.__all__ == ["crc", "crc16_ccsds", "crc16_xmodem", "crc32", "crc32c"]
    assert sc.MAX_BYTES == 65536


@pytest.mark.parametrize("bad", HOSTILE_DATA)
def test_data_type_refusals_in_all_public_functions(bad):
    for f in (sc.crc16_ccsds, sc.crc16_xmodem, sc.crc32, sc.crc32c):
        with pytest.raises(ValueError, match="data must be bytes or bytearray"):
            f(bad)
    with pytest.raises(ValueError, match="data must be bytes or bytearray"):
        sc.crc(bad, 16, 0x1021, 0, False, False, 0)


def test_data_length_limit_inside_and_outside():
    assert sc.crc16_xmodem(bytes(sc.MAX_BYTES)) == 0
    with pytest.raises(ValueError, match="at most 65536"):
        sc.crc16_xmodem(bytes(sc.MAX_BYTES + 1))
    with pytest.raises(ValueError, match="at most 65536"):
        sc.crc(bytes(sc.MAX_BYTES + 1), 16, 0x1021, 0, False, False, 0)


@pytest.mark.parametrize("width", [7, 65, 8.0, True, None])
def test_width_refusals(width):
    with pytest.raises(ValueError, match="width"):
        sc.crc(GOOD, width, 0x07, 0, False, False, 0)


def test_width_limits_accepted_just_inside():
    assert isinstance(sc.crc(GOOD, 8, 0x07, 0, False, False, 0), int)
    assert isinstance(sc.crc(GOOD, 64, 0x42F0E1EBA9EA3693, 0, False, False, 0), int)


@pytest.mark.parametrize("poly", [0, 6, 0x107, 3.5])
def test_poly_refusals(poly):
    if poly == 6:
        with pytest.raises(ValueError, match="odd"):
            sc.crc(GOOD, 8, poly, 0, False, False, 0)
    else:
        with pytest.raises(ValueError, match="poly"):
            sc.crc(GOOD, 8, poly, 0, False, False, 0)


def test_poly_limits_accepted_just_inside():
    assert isinstance(sc.crc(GOOD, 8, 1, 0, False, False, 0), int)
    assert isinstance(sc.crc(GOOD, 8, 0xFF, 0, False, False, 0), int)


@pytest.mark.parametrize("value, field", [(-1, "init"), (256, "init"), (-1, "xor_out"), (256, "xor_out")])
def test_init_xor_out_refusals(value, field):
    kwargs = dict(width=8, poly=0x07, init=0, reflect_in=False, reflect_out=False, xor_out=0)
    kwargs[field] = value
    with pytest.raises(ValueError, match=field):
        sc.crc(GOOD, **kwargs)


def test_init_xor_out_limits_accepted():
    assert isinstance(sc.crc(GOOD, 8, 0x07, 0, False, False, 0), int)
    assert isinstance(sc.crc(GOOD, 8, 0x07, 255, False, False, 255), int)


@pytest.mark.parametrize("ri, ro", [(0, False), (1, False), (None, False), (False, 0), (False, 1), (False, None)])
def test_reflect_flags_must_be_bools(ri, ro):
    with pytest.raises(ValueError, match="reflect_in and reflect_out"):
        sc.crc(GOOD, 8, 0x07, 0, ri, ro, 0)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_nan_and_infinity_are_refused_everywhere(bad):
    """Added in review: the hostile probe with non-finite floats, one argument at a time."""
    for position in (1, 2, 3, 6):
        args = [b"abc", 16, 0x1021, 0, False, False, 0]
        args[position] = bad
        with pytest.raises(ValueError, match="must be an integer"):
            sc.crc(*args)
    for position in (4, 5):
        args = [b"abc", 16, 0x1021, 0, False, False, 0]
        args[position] = bad
        with pytest.raises(ValueError, match="reflect_in and reflect_out"):
            sc.crc(*args)
    for f in (sc.crc16_ccsds, sc.crc16_xmodem, sc.crc32, sc.crc32c):
        with pytest.raises(ValueError, match="data must be bytes"):
            f(bad)
