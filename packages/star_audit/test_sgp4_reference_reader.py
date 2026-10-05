"""The SGP4-VER reader treated as a hostile-input parser (mutation score 0.50: the reader was barely tested). A wrong
reader turns into false findings about other people's software, so every rule is pinned on tiny synthetic files.
Verifies: R5 (README).
"""
import pytest

from sgp4_audit import load_reference

L1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
L2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667     0.00      4320.0        360.00"
L1b = "1 04632U 70093B   04031.91070959 -.00000084  00000-0  10000-3 0  9955"
L2b = "2 04632  11.4628 273.1101 1450506 207.6000 143.9350  1.20231981 44145  -5184.0     -4320.0        360.00"


def write(tmp_path, tle, out):
    t, o = tmp_path / "v.tle", tmp_path / "v.out"
    t.write_text(tle, encoding="utf-8")
    o.write_text(out, encoding="utf-8")
    return t, o


def test_truncates_line2_to_69_columns_and_reads_values(tmp_path):
    t, o = write(tmp_path, f"#comment\n{L1}\n{L2}\n", "5 xx\n 0.0 1.5 2.5 3.5 4 5 6\n 360.0 -1.0 -2.0 -3.0 4 5 6\n")
    c = load_reference(t, o)
    assert len(c) == 1 and c[0]["satnum"] == 5 and c[0]["case"] == 0
    assert c[0]["line1"] == L1 and c[0]["line2"] == L2[:69] and len(c[0]["line2"]) == 69
    assert c[0]["epochs"] == [0.0, 360.0] and c[0]["ref"] == [[1.5, 2.5, 3.5], [-1.0, -2.0, -3.0]]


def test_cases_follow_file_order(tmp_path):
    t, o = write(tmp_path, f"{L1}\n{L2}\n{L1b}\n{L2b}\n", "5 xx\n 0 1 2 3\n4632 xx\n -5184 7 8 9\n")
    c = load_reference(t, o)
    assert [x["satnum"] for x in c] == [5, 4632] and [x["case"] for x in c] == [0, 1]
    assert c[1]["epochs"] == [-5184.0] and c[1]["ref"] == [[7.0, 8.0, 9.0]]


def test_order_mismatch_raises(tmp_path):
    t, o = write(tmp_path, f"{L1}\n{L2}\n{L1b}\n{L2b}\n", "4632 xx\n 0 1 2 3\n")
    with pytest.raises(ValueError, match="does not match TLE order"):
        load_reference(t, o)


def test_more_reference_blocks_than_tles_raises(tmp_path):
    t, o = write(tmp_path, f"{L1}\n{L2}\n", "5 xx\n 0 1 2 3\n5 xx\n 0 1 2 3\n")
    with pytest.raises(ValueError):
        load_reference(t, o)


def test_short_and_non_numeric_lines_are_skipped_not_misread(tmp_path):
    t, o = write(tmp_path, f"{L1}\n{L2}\n", "5 xx\n 0 1 2\n abc def ghi jkl\n 60 1 2 3\n")
    c = load_reference(t, o)
    assert c[0]["epochs"] == [60.0] and c[0]["ref"] == [[1.0, 2.0, 3.0]]


def test_line1_without_line2_is_not_a_tle(tmp_path):
    t, o = write(tmp_path, f"{L1}\n#broken\n{L1b}\n{L2b}\n", "4632 xx\n 0 1 2 3\n")
    c = load_reference(t, o)
    assert [x["satnum"] for x in c] == [4632]


def test_line1_is_cut_at_69_and_is_the_satnum_authority(tmp_path):
    l2_other = "2 99999" + L2[7:]
    t, o = write(tmp_path, f"{L1}   trailing junk\n{l2_other}\n", "5 xx\n 0 1 2 3\n")
    c = load_reference(t, o)
    assert c[0]["line1"] == L1 and c[0]["satnum"] == 5


def test_dangling_line1_at_end_of_file_is_ignored(tmp_path):
    t, o = write(tmp_path, f"{L1b}\n{L2b}\n{L1}", "4632 xx\n 0 1 2 3\n")
    assert [x["satnum"] for x in load_reference(t, o)] == [4632]


def test_mismatch_message_names_the_reference_satellite(tmp_path):
    t, o = write(tmp_path, f"{L1}\n{L2}\n", "4632 xx\n 0 1 2 3\n")
    with pytest.raises(ValueError, match=r"block 0 \(sat 4632\)"):
        load_reference(t, o)
