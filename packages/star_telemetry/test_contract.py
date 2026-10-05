# SPDX-License-Identifier: Apache-2.0
"""Construction and input contract of CcsdsTransferFrameEngine, from a probe with hostile inputs (2026-10-05).
Verifies: R1, R3 (README).

Found by the probe: frame_length 0, -5, NaN and 256.5 were accepted, and frames shorter than the primary header then
failed with IndexError or struct.error instead of ValueError; has_fecf="no" was treated as True; and
process_raw_stream("...") with a str returned [] silently, as if the link carried no frame. All are refused now."""
import math

import pytest

from star_telemetry.engine import CcsdsTransferFrameEngine as Engine


@pytest.mark.parametrize("length", [0, -5, 3, 7, math.nan, math.inf, 256.5, True])
def test_impossible_frame_length_is_refused_with_fecf(length):
    with pytest.raises(ValueError):
        Engine(frame_length=length, has_fecf=True)


def test_minimum_lengths_are_accepted():
    Engine(frame_length=8, has_fecf=True)
    Engine(frame_length=6, has_fecf=False)
    with pytest.raises(ValueError):
        Engine(frame_length=5, has_fecf=False)


@pytest.mark.parametrize("flag", ["no", 1, None])
def test_has_fecf_must_be_a_bool(flag):
    with pytest.raises(TypeError):
        Engine(frame_length=256, has_fecf=flag)


@pytest.mark.parametrize("stream", ["\x1a\xcf\xfc\x1d" + "x" * 256, None, [0x1A, 0xCF, 0xFC, 0x1D]])
def test_non_bytes_stream_is_refused_not_read_as_empty(stream):
    with pytest.raises(TypeError):
        Engine(frame_length=256, has_fecf=True).process_raw_stream(stream)


def test_wrong_length_frame_is_a_value_error():
    with pytest.raises(ValueError):
        Engine(frame_length=256, has_fecf=True).parse_frame(b"\x40" * 255)
