# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""python -m star_timescales [instant, e.g. 2026-09-28T12:00:00Z]

Prints TAI - UTC, TT - UTC, GPS time, the CCSDS CUC time code and the Julian dates for an instant (default: now), and how long the
embedded leap-second table remains valid. Exit code 0 if the instant is covered, 2 if it is not.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from . import (
    LEAP_SECONDS_SOURCE,
    LEAP_SECONDS_VALID_UNTIL,
    GPS_EPOCH,
    LeapSecondTableError,
    encode_cuc,
    NaiveDatetimeError,
    gps_minus_utc,
    gps_week_and_seconds,
    julian_date,
    modified_julian_date,
    tai_minus_utc,
    tt_minus_utc,
)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    try:
        when = datetime.fromisoformat(args[0].replace("Z", "+00:00")) if args else datetime.now(timezone.utc)
        tai, tt = tai_minus_utc(when), tt_minus_utc(when)  # refused before anything is printed
        jd, mjd = julian_date(when), modified_julian_date(when)
    except NaiveDatetimeError:
        print(f"refused: '{args[0]}' has no timezone; add one, e.g. {args[0].split('T')[0]}T00:00:00Z",
              file=sys.stderr)
        return 2
    except LeapSecondTableError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except ValueError:  # not parseable (LeapSecondTableError, a ValueError, is handled above)
        print(f"refused: '{args[0]}' is not an ISO-8601 instant; e.g. 2026-09-28T12:00:00Z", file=sys.stderr)
        return 2
    print(f"instant (UTC)   {when.astimezone(timezone.utc).isoformat(timespec='seconds')}")
    print(f"TAI - UTC       {tai} s")
    print(f"TT - UTC        {tt:.3f} s")
    print(f"JD / MJD        {jd:.6f} / {mjd:.6f}")
    if when.astimezone(timezone.utc) >= GPS_EPOCH:
        week, sow = gps_week_and_seconds(when)
        print(f"GPS - UTC       {gps_minus_utc(when)} s")
        print(f"GPS week / SOW  {week} / {sow:.6f} s")
    else:
        print(f"GPS             not defined before {GPS_EPOCH:%Y-%m-%d}")
    days = (LEAP_SECONDS_VALID_UNTIL - datetime.now(timezone.utc)).days
    print(f"CCSDS CUC       {encode_cuc(when).hex(' ').upper()}  (Level 1, P-field 1E: 4+2 octets, TAI since 1958)")
    print(f"table           {LEAP_SECONDS_SOURCE}")
    print(f"table valid     until {LEAP_SECONDS_VALID_UNTIL:%Y-%m-%d} ({days} days from today)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
