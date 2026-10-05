"""Official examples of CCSDS 508.0-B-1 sec. 3.6 (extracted verbatim from the public PDF into fixtures/) plus
malformed messages. Findings in the standard itself are asserted, not hidden: example 3.6.3 writes 'TRACKS USED'
(table 3-3 defines TRACKS_USED) and example 3.6.4 gives object states 55,000 km apart for a 104.92 m miss distance."""
import re
from pathlib import Path

import pytest

from star_cdm import CdmFormatError, consistency_report, covariance_rtn, parse_cdm

F = Path(__file__).resolve().parent / "fixtures"
ex = lambda n: (F / f"ccsds508_example_{n}.kvn").read_text(encoding="utf-8")


def fix_dates(t):
    """Examples 3.6.3/3.6.4 write SCREEN_PERIOD times as 18:29:32:212 (':' before the fraction, not CCSDS)."""
    return t.replace("18:29:32:212", "18:29:32.212")


def test_examples_3_6_3_and_3_6_4_have_malformed_dates_in_the_standard():
    for n in (2, 3):
        with pytest.raises(CdmFormatError, match="CCSDS date"):
            parse_cdm(ex(n))


def test_example_3_6_2_obligatory_keywords():
    c = parse_cdm(ex(1))
    assert c["header"]["MISS_DISTANCE"] == 715 and c["object2"]["OBJECT_NAME"] == "FENGYUN 1C DEB"
    assert c["object1"]["Z_DOT"] == -3.526774282          # value printed with a U+2212 minus in the PDF
    assert any("U+2212" in w for w in c["warnings"])
    r = consistency_report(c)
    assert abs(r["from_states_m"] - 715) < 1.0 and r["flags"] == []


def test_covariance_matrix_is_symmetric_6x6():
    m = covariance_rtn(parse_cdm(ex(1))["object1"])
    assert len(m) == 6 and all(len(row) == 6 for row in m)
    assert all(m[i][j] == m[j][i] for i in range(6) for j in range(6)) and m[1][1] == 2.533e3


def test_example_3_6_3_has_a_keyword_typo_in_the_standard():
    with pytest.raises(CdmFormatError, match="TRACKS USED"):
        parse_cdm(fix_dates(ex(2)))
    c = parse_cdm(fix_dates(ex(2)).replace("TRACKS USED", "TRACKS_USED"))
    assert c["header"]["COLLISION_PROBABILITY"] == 4.835e-05


def test_example_3_6_4_states_inconsistent_with_miss_distance():
    r = consistency_report(parse_cdm(fix_dates(ex(3))))
    assert abs(r["from_rtn_m"] - 104.92) < 0.01
    assert "STATES_INCONSISTENT_WITH_MISS_DISTANCE" in r["flags"] and r["from_states_m"] > 5e7


@pytest.mark.parametrize("mutate,msg", [
    (lambda t: "\n".join(l for l in t.splitlines() if not l.startswith("TCA")), "missing"),
    (lambda t: t.replace("TCA ", "XTCA ", 1), "unknown keyword"),
    (lambda t: t.replace("[m]", "[km]", 1), "unit"),
    (lambda t: re.sub(r"OBJECT\s+= OBJECT2", "OBJECT = OBJECT1", t), "OBJECT"),
    (lambda t: t + "OBJECT = OBJECT2\n", "OBJECT"),
    (lambda t: t.replace("2570.097065", "2570.0g7065"), "numeric"),
    (lambda t: t.replace("2010-03-13T22:37:52.618", "2010-13-13T22:37:52.618"), "date"),
    (lambda t: t.replace("ORIGINATOR", "ORIGINATOR = X\nORIGINATOR", 1), "duplicate"),
    (lambda t: re.split(r"OBJECT\s+= OBJECT2", t)[0], "exactly 2"),
])
def test_malformed_messages_are_rejected(mutate, msg):
    with pytest.raises(CdmFormatError, match=msg):
        parse_cdm(mutate(ex(1)))
