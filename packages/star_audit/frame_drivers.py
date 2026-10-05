"""Drivers for frame_audit: one per implementation, each a self-contained source string run in that library's venv.
Only documented APIs: astropy TEME/GCRS frames, skyfield sgp4lib.TEME.rotation_at (r_TEME = R r_GCRS)."""

ASTROPY = '''
from astropy.utils import iers
iers.conf.auto_download = False
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import TEME, GCRS, CartesianRepresentation
def teme_to_gcrs(utc, r):
    t = Time(utc, scale="utc")
    c = TEME(CartesianRepresentation(r * u.km), obstime=t).transform_to(GCRS(obstime=t))
    return c.cartesian.xyz.to_value(u.km).tolist()
'''

OREKIT = '''
import orekit_jpype
orekit_jpype.initVM()
from orekit_jpype.pyhelpers import setup_orekit_data
setup_orekit_data("/root/orekit-data.zip", from_pip_library=False)
from org.orekit.frames import FramesFactory
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.hipparchus.geometry.euclidean.threed import Vector3D
_teme, _gcrf, _utc = FramesFactory.getTEME(), FramesFactory.getGCRF(), TimeScalesFactory.getUTC()
def teme_to_gcrs(utc, r):
    d = AbsoluteDate(utc, _utc)
    p = _teme.getTransformTo(_gcrf, d).transformPosition(Vector3D(r[0] * 1e3, r[1] * 1e3, r[2] * 1e3))
    return [p.getX() / 1e3, p.getY() / 1e3, p.getZ() / 1e3]
'''

VALLADO_FK5 = '''
# Vallado's TEME -> J2000 route on the IAU-1976 precession / IAU-1980 nutation model (FK5), built from ERFA primitives:
# r_TOD = R3(-eqe82) r_TEME, eqe82 = dpsi cos(eps_mean) (no kinematic terms); r_MOD = N^T r_TOD; r_J2000 = P^T r_MOD.
# No EOP nutation corrections, no frame bias: a MODEL lineage, used to test the IAU-76/80 hypothesis of DISC-FRAME-001.
import math
import erfa
from astropy.time import Time
def _r3(a, v):
    c, s = math.cos(a), math.sin(a)
    return [c * v[0] + s * v[1], -s * v[0] + c * v[1], v[2]]
def _mtv(m, v):
    return [sum(m[j][i] * v[j] for j in range(3)) for i in range(3)]
def teme_to_gcrs(utc, r):
    t = Time(utc, scale="utc").tt
    dpsi, deps = erfa.nut80(t.jd1, t.jd2)
    eps = erfa.obl80(t.jd1, t.jd2)
    tod = _r3(-dpsi * math.cos(eps), r)
    N = erfa.numat(eps, dpsi, deps)
    P = erfa.pmat76(t.jd1, t.jd2)
    return _mtv(P, _mtv(N, tod))
'''

# same route plus the J2000 -> GCRS frame bias (ERFA bp00 bias matrix rb): r_GCRS = rb^T r_J2000
VALLADO_FK5_BIAS = VALLADO_FK5.replace("    return _mtv(P, _mtv(N, tod))",
                                       "    rb, _, _ = erfa.bp00(t.jd1, t.jd2)\n    return _mtv(rb, _mtv(P, _mtv(N, tod)))")

# ---- CCSDS TM frame decoders for ccsds_audit (decode(frame) -> dict, raise = reject) ----
TM_SPACEPACKETS = '''
from spacepackets.ccsds.tm_frame import TmTransferFrame
def decode(f):
    t = TmTransferFrame.unpack(f, len(f), True)          # raises on CRC error
    h = t.primary_header
    return {"crc_ok": True, "scid": h.master_channel_id.spacecraft_id, "vcid": h.vc_id,
            "mc": h.master_ch_frame_count, "vc": h.vc_frame_count,
            "fhp": h.frame_datafield_status.first_header_pointer,
            "ocf": t.op_ctrl_field.hex() if t.op_ctrl_field is not None else None,
            "data": bytes(t.data_field).hex()}
'''

TM_STAR_PY = '''
from star_telemetry import CcsdsTransferFrameEngine
def decode(f):
    e = CcsdsTransferFrameEngine(frame_length=len(f), has_fecf=True)
    h, d = e.parse_frame(f)
    ocf = f[-6:-2].hex() if (f[1] & 1) else None
    return {"crc_ok": bool(h.fecf_valid), "scid": h.scid, "vcid": h.vcid, "mc": f[2], "vc": h.vcfc, "fhp": h.fhp,
            "ocf": ocf, "data": bytes(d).hex()}
'''

# star_aos (C) through its host program in WSL: decode() batches nothing, so frames are decoded in one WSL call on
# first use and served from a cache (300 separate wsl.exe calls would take minutes). mc is read from octet 2 by the
# driver (the C header does not expose the master-channel count), exactly as the Python star_telemetry driver does.
TM_STAR_C = '''
import json, os, subprocess, tempfile
_EXE = "/root/star_fw/star_aos_dump_host"
_SRC = os.environ["STAR_AOS_SRC"]          # WSL path of star_telemetry_c/src, given by the caller (no personal paths in code)
_cache = {}
def _batch(frames):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "s.bin")
    open(p, "wb").write(b"".join(frames))
    wp = "/mnt/" + p[0].lower() + p[2:].replace(chr(92), "/")
    specs = " ".join(f"{len(f)}:1" for f in frames)
    cmd = (f"mkdir -p /root/star_fw && gcc -std=c99 -O2 -Wall -Wextra -Werror '{_SRC}/star_aos.c' '{_SRC}/host_main.c' "
           f"-o {_EXE} && {_EXE} '{wp}' {specs}")
    r = subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-300:])
    rows = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    for f, x in zip(frames, rows):
        _cache[f] = x
def decode(f):
    if f not in _cache:
        _batch([bytes.fromhex(h) for h in payload["frames"]])
    x = _cache[f]
    if "error" in x:
        raise ValueError(f"star_aos error {x['error']}")
    if not x["fecf_valid"]:
        raise ValueError("FECF")
    o, n, k = x["data_offset"], x["data_len"], x["ocf_len"]
    return {"crc_ok": True, "scid": x["scid"], "vcid": x["vcid"], "mc": f[2], "vc": x["vcfc"], "fhp": x["fhp"],
            "ocf": f[o + n:o + n + k].hex() if k else None, "data": f[o:o + n].hex()}
'''

# ---- TDB - TT drivers for tdb_audit (tdb_minus_tt(jd_tt) -> seconds, geocentric) ----
TDB_ERFA = '''
import erfa
def tdb_minus_tt(jd):
    return erfa.dtdb(jd, 0.0, 0.0, 0.0, 0.0, 0.0)     # geocentric: ut, elong, u, v = 0 (SOFA/ERFA Fairhead-Bretagnon)
'''

TDB_ASTROPY = '''
from astropy.time import Time
def tdb_minus_tt(jd):
    t = Time(jd, format="jd", scale="tt")
    return float((t.tdb.jd1 - t.tt.jd1) * 86400.0 + (t.tdb.jd2 - t.tt.jd2) * 86400.0)
'''

TDB_SKYFIELD = '''
from skyfield.api import load
_ts = load.timescale(builtin=True)
def tdb_minus_tt(jd):
    # two-part times: (t.tdb - t.tt) on float JDs of ~2.45e6 days has ~40 us resolution (first version of this driver
    # did that and showed a 20 us skyfield 'divergence' that was the probe's own rounding, 2026-10-05)
    t = _ts.tt_jd(jd)
    return float((t.tdb_fraction - t.tt_fraction) * 86400.0)
'''

TDB_SPICE = '''
import spiceypy as sp
import os
sp.furnsh(os.environ["STAR_LSK"])                      # leap-second kernel path given by the caller
def tdb_minus_tt(jd):
    tt_s = (jd - 2451545.0) * 86400.0                    # TT seconds past J2000
    return float(sp.unitim(tt_s, "TT", "TDB") - tt_s)    # NAIF DELTET model (K sin E)
'''

# model implementation (written from the published equation, not from any library): USNO Circular 179 (Kaplan 2005),
# eq. 2.6 -- used to isolate whether a library's divergence is the published formula itself
TDB_USNO_C179 = '''
import math
def tdb_minus_tt(jd):
    t = (jd - 2451545.0) / 36525.0
    s = math.sin
    return (0.001657 * s(628.3076 * t + 6.2401) + 0.000022 * s(575.3385 * t + 4.2970)
            + 0.000014 * s(1256.6152 * t + 6.1969) + 0.000005 * s(606.9777 * t + 4.0212)
            + 0.000005 * s(52.9691 * t + 0.4444) + 0.000002 * s(21.3299 * t + 5.5431)
            + 0.000010 * t * s(628.3076 * t + 4.2490))
'''

TDB_STAR = '''
# star_tdb is found through PYTHONPATH set by the caller (no absolute sys.path in code: compliance rule 2026-10-04)
from star_tdb import tdb_minus_tt as _f
def tdb_minus_tt(jd):
    return _f(jd)
'''

# ---- CCSDS Space Packet decoders for packet_audit (decode(buffer) -> fields; raise = reject) ----
PKT_SPACEPACKETS = '''
# SpacePacket has no unpack(); the header class does (first driver called SpacePacket.unpack: a probe defect, 2026-10-05)
from spacepackets.ccsds.spacepacket import SpacePacketHeader
def decode(b):
    h = SpacePacketHeader.unpack(b)
    if len(b) != h.packet_len:
        raise ValueError(f"buffer {len(b)} octets, header says {h.packet_len}")
    return {"apid": h.apid, "seq": h.seq_count, "ptype": int(h.packet_type), "sec": int(h.sec_header_flag),
            "data": bytes(b[6:]).hex()}
'''

PKT_CCSDSPY = '''
# ccsdspy reports inconsistencies through its logger (ccsdspy.log), not the warnings module (first driver listened to
# warnings only and saw nothing: a probe defect, 2026-10-05)
import io, logging
import ccsdspy
from ccsdspy.utils import split_packet_bytes, get_packet_apid
class _Grab(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING); self.records = []
    def emit(self, record):
        self.records.append(record.getMessage())
def decode(b):
    g = _Grab(); ccsdspy.log.addHandler(g)
    try:
        pk = split_packet_bytes(io.BytesIO(b))
    finally:
        ccsdspy.log.removeHandler(g)
    if g.records or len(pk) != 1:
        raise ValueError(f"{len(pk)} packets, log: {g.records[:1]}")
    p = bytes(pk[0])
    return {"apid": get_packet_apid(p[:6]), "seq": ((p[2] << 8) | p[3]) & 0x3FFF, "ptype": (p[0] >> 4) & 1,
            "sec": (p[0] >> 3) & 1, "data": p[6:].hex()}
'''

PKT_STAR = '''
from star_telemetry.engine import parse_space_packets
def decode(b):
    pk = parse_space_packets(b)
    if len(pk) != 1 or pk[0].length != len(b):
        raise ValueError(f"{len(pk)} packets covering {sum(p.length for p in pk)} of {len(b)} octets")
    p = pk[0]
    return {"apid": p.apid, "seq": p.seq_count, "ptype": p.packet_type, "sec": p.sec_hdr_flag, "data": p.payload.hex()}
'''

# ---- TLE ingestion drivers for tle_audit (ingest(l1, l2) -> {satnum, inc deg}; raise = reject) ----
TLE_SGP4_API = '''
import math
from sgp4.api import Satrec
def ingest(l1, l2):
    s = Satrec.twoline2rv(l1, l2)
    if s.error:
        raise ValueError(f"sgp4 error {s.error}")
    return {"satnum": s.satnum, "inc": math.degrees(s.inclo)}
'''

TLE_SKYFIELD = '''
from skyfield.api import EarthSatellite, load
_ts = load.timescale(builtin=True)
def ingest(l1, l2):
    s = EarthSatellite(l1, l2, ts=_ts)
    import math
    return {"satnum": s.model.satnum, "inc": math.degrees(s.model.inclo)}
'''

TLE_PYORBITAL = '''
from pyorbital.tlefile import Tle
def ingest(l1, l2):
    t = Tle("audit", line1=l1, line2=l2)
    return {"satnum": int(t.satnumber), "inc": float(t.inclination)}
'''

TLE_OREKIT = '''
import orekit_jpype
orekit_jpype.initVM()
from orekit_jpype.pyhelpers import setup_orekit_data
setup_orekit_data("/root/orekit-data.zip", from_pip_library=False)
from org.orekit.propagation.analytical.tle import TLE
import math
def ingest(l1, l2):
    if not TLE.isFormatOK(l1, l2):
        raise ValueError("TLE.isFormatOK false")
    t = TLE(l1, l2)
    return {"satnum": t.getSatelliteNumber(), "inc": math.degrees(t.getI())}
'''

# ---- orbital elements drivers for elements_audit (elements(r_km, v_kms, mu) -> p km, e, angles deg) ----
EL_SGP4_VALLADO = '''
import math
from sgp4.ext import rv2coe
def elements(r, v, mu):
    p, a, e, i, raan, argp, nu, m, arglat, truelon, lonper = rv2coe(r, v, mu)
    d = math.degrees
    return {"p": p, "e": e, "i": d(i), "raan": d(raan), "argp": d(argp), "nu": d(nu)}
'''

EL_HAPSIRA = '''
import math
import numpy as np
from hapsira.core.elements import rv2coe
def elements(r, v, mu):
    p, e, i, raan, argp, nu = rv2coe(mu, np.array(r, float), np.array(v, float))
    d = math.degrees
    return {"p": float(p), "e": float(e), "i": d(i), "raan": d(raan), "argp": d(argp), "nu": d(nu)}
'''

EL_SKYFIELD = '''
from skyfield.api import load
from skyfield.positionlib import ICRF
from skyfield.elementslib import osculating_elements_of
_ts = load.timescale(builtin=True)
_t = _ts.tt_jd(2451545.0)
_AU = 149597870.700
def elements(r, v, mu):
    pos = ICRF([x / _AU for x in r], [x * 86400.0 / _AU for x in v], t=_t, center=399)
    o = osculating_elements_of(pos, gm_km3_s2=mu)
    return {"p": o.semi_latus_rectum.km, "e": float(o.eccentricity), "i": o.inclination.degrees,
            "raan": o.longitude_of_ascending_node.degrees, "argp": o.argument_of_periapsis.degrees,
            "nu": o.true_anomaly.degrees}
'''

EL_STAR = '''
import math
from star_elements import rv_to_coe
def elements(r, v, mu):
    h, e, i, raan, argp, nu = rv_to_coe(r, v, mu)
    d = math.degrees
    return {"p": h * h / mu, "e": e, "i": d(i), "raan": d(raan), "argp": d(argp), "nu": d(nu)}
'''

# ---- GMST drivers for gmst_audit (gmst_deg(jd_ut1) -> degrees) ----
GMST_ERFA82 = '''
import erfa, math
def gmst_deg(jd):
    return math.degrees(erfa.gmst82(jd, 0.0))
'''

GMST_ERFA06 = '''
import erfa, math
def gmst_deg(jd):
    return math.degrees(erfa.gmst06(jd, 0.0, jd, 69.184 / 86400.0))    # TT = UT1 + 69.184 s
'''

GMST_ASTROPY = '''
from astropy.utils import iers
iers.conf.auto_download = False
from astropy.time import Time
def gmst_deg(jd):
    t = Time(jd, format="jd", scale="ut1")
    return float(t.sidereal_time("mean", "greenwich", model="IAU2006").deg)
'''

GMST_SKYFIELD = '''
from skyfield.api import load
_ts = load.timescale(builtin=True)
def gmst_deg(jd):
    return float(_ts.ut1_jd(jd).gmst) * 15.0          # skyfield returns hours
'''

GMST_SGP4 = '''
import math
from sgp4.propagation import gstime
def gmst_deg(jd):
    return math.degrees(gstime(jd))                    # Vallado's own code (IAU 1982), as used by SGP4
'''

GMST_PYORBITAL = '''
import datetime as _dt
from pyorbital.astronomy import gmst
def gmst_deg(jd):
    # pyorbital takes a datetime (treated as UT1 here); microsecond resolution
    t = _dt.datetime(2000, 1, 1, 12) + _dt.timedelta(days=jd - 2451545.0)
    return float(gmst(t)) * 180.0 / 3.141592653589793
'''

GMST_STAR = '''
from star_sidereal import gmst82_deg
def gmst_deg(jd):
    return gmst82_deg(jd, 0.0)
'''

SKYFIELD = '''
from skyfield.api import load
from skyfield.sgp4lib import TEME
_ts = load.timescale(builtin=True)
def teme_to_gcrs(utc, r):
    d, t = utc.split("T"); Y, M, D = (int(x) for x in d.split("-")); h, m, s = t.split(":")
    tt = _ts.utc(Y, M, D, int(h), int(m), float(s))
    R = TEME.rotation_at(tt)
    return [sum(R[j][i] * r[j] for j in range(3)) for i in range(3)]
'''
