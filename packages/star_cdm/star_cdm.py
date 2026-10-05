# -*- coding: utf-8 -*-
"""star_cdm — CCSDS 508.0-B-1 Conjunction Data Message (KVN) parser (S.T.A.R., Claude Code, 2026-10-04).

Standard library only. The obligatory keyword set is the one of the standard's own example 3.6.2 ("only obligatory
keywords"). Every malformation raises CdmFormatError; nothing is guessed. Typographic minus signs (U+2212, present
in the published PDF examples) are normalised to '-' and REPORTED in `warnings`, never silently.
"""
from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Dict, List

HEADER_REQ = ("CCSDS_CDM_VERS", "CREATION_DATE", "ORIGINATOR", "MESSAGE_ID")
RELATIVE_REQ = ("TCA", "MISS_DISTANCE")
STATE = ("X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT")
COV = ("CR_R", "CT_R", "CT_T", "CN_R", "CN_T", "CN_N", "CRDOT_R", "CRDOT_T", "CRDOT_N", "CRDOT_RDOT", "CTDOT_R",
       "CTDOT_T", "CTDOT_N", "CTDOT_RDOT", "CTDOT_TDOT", "CNDOT_R", "CNDOT_T", "CNDOT_N", "CNDOT_RDOT", "CNDOT_TDOT",
       "CNDOT_NDOT")
OBJECT_REQ = ("OBJECT", "OBJECT_DESIGNATOR", "CATALOG_NAME", "OBJECT_NAME", "INTERNATIONAL_DESIGNATOR",
              "EPHEMERIS_NAME", "COVARIANCE_METHOD", "MANEUVERABLE", "REF_FRAME") + STATE + COV
UNITS = {"MISS_DISTANCE": "m", "RELATIVE_SPEED": "m/s", "X": "km", "Y": "km", "Z": "km", "X_DOT": "km/s",
         "Y_DOT": "km/s", "Z_DOT": "km/s"}
for k in COV:  # covariance units by how many rate terms the element has
    UNITS[k] = {0: "m**2", 1: "m**2/s", 2: "m**2/s**2"}[k.count("DOT")]
TEXT = {"CCSDS_CDM_VERS", "ORIGINATOR", "MESSAGE_ID", "OBJECT", "OBJECT_DESIGNATOR", "CATALOG_NAME", "OBJECT_NAME",
        "INTERNATIONAL_DESIGNATOR", "EPHEMERIS_NAME", "COVARIANCE_METHOD", "MANEUVERABLE", "REF_FRAME",
        "MESSAGE_FOR", "COLLISION_PROBABILITY_METHOD", "SCREEN_VOLUME_FRAME", "SCREEN_VOLUME_SHAPE",
        "ORBIT_CENTER", "GRAVITY_MODEL", "ATMOSPHERIC_MODEL", "N_BODY_PERTURBATIONS", "SOLAR_RAD_PRESSURE",
        "EARTH_TIDES", "INTRACK_THRUST", "OPERATOR_CONTACT_POSITION", "OPERATOR_ORGANIZATION", "OPERATOR_PHONE",
        "OPERATOR_EMAIL", "ODM_MSG_LINK", "ADM_MSG_LINK", "TIME_LASTOB_START", "TIME_LASTOB_END", "OBJECT_TYPE",
        "COMMENT"}
DATES = {"CREATION_DATE", "TCA", "START_SCREEN_PERIOD", "STOP_SCREEN_PERIOD", "SCREEN_ENTRY_TIME", "SCREEN_EXIT_TIME",
         "TIME_LASTOB_START", "TIME_LASTOB_END"}
LINE = re.compile(r"^([A-Z0-9_]+)\s*=\s*(.*?)\s*(?:\[([^\]]+)\])?\s*$")


TABLE_KEYS = {  # extracted from the keyword tables of CCSDS 508.0-B-1 (sec. 3.2-3.5)
    "ACTUAL_OD_SPAN", "AREA_DRG", "AREA_PC", "AREA_SRP", "ATMOSPHERIC_MODEL", "CATALOG_NAME", "CCSDS_CDM_VERS",
    "CD_AREA_OVER_MASS", "COLLISION_PROBABILITY", "COLLISION_PROBABILITY_METHOD", "COMMENT", "COVARIANCE_METHOD",
    "CREATION_DATE", "CR_AREA_OVER_MASS", "EARTH_TIDES", "EPHEMERIS_NAME", "GRAVITY_MODEL", "INTERNATIONAL_DESIGNATOR",
    "INTRACK_THRUST", "MANEUVERABLE", "MASS", "MESSAGE_FOR", "MESSAGE_ID", "MISS_DISTANCE", "N_BODY_PERTURBATIONS",
    "OBJECT", "OBJECT_DESIGNATOR", "OBJECT_NAME", "OBJECT_TYPE", "OBS_AVAILABLE", "OBS_USED",
    "OPERATOR_CONTACT_POSITION", "OPERATOR_EMAIL", "OPERATOR_ORGANIZATION", "OPERATOR_PHONE", "ORBIT_CENTER",
    "ORIGINATOR", "RECOMMENDED_OD_SPAN", "REF_FRAME", "RELATIVE_POSITION_N", "RELATIVE_POSITION_R",
    "RELATIVE_POSITION_T", "RELATIVE_SPEED", "RELATIVE_VELOCITY_N", "RELATIVE_VELOCITY_R", "RELATIVE_VELOCITY_T",
    "RESIDUALS_ACCEPTED", "SCREEN_ENTRY_TIME", "SCREEN_EXIT_TIME", "SCREEN_VOLUME_FRAME", "SCREEN_VOLUME_SHAPE",
    "SCREEN_VOLUME_X", "SCREEN_VOLUME_Y", "SCREEN_VOLUME_Z", "SEDR", "SOLAR_RAD_PRESSURE", "START_SCREEN_PERIOD",
    "STOP_SCREEN_PERIOD", "TCA", "THRUST_ACCELERATION", "TIME_LASTOB_END", "TIME_LASTOB_START", "TRACKS_AVAILABLE",
    "TRACKS_USED", "WEIGHTED_RMS"}
EXT_COV = re.compile(r"^C(DRG|SRP|THR)_(R|T|N|RDOT|TDOT|NDOT|DRG|SRP|THR)$")


def _known(key: str) -> bool:
    return key in TABLE_KEYS or key in STATE or key in COV or bool(EXT_COV.match(key))


class CdmFormatError(ValueError):
    pass


CCSDS_DATE = re.compile(r"^\d{4}-(\d{2}-\d{2}|\d{3})T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$")


def _date(s: str, key: str) -> datetime:
    """CCSDS 502.0 time formats only (calendar or day-of-year, '.' before fractions). Python's fromisoformat alone
    is too lenient: it accepted '18:29:32:212' (found by the Orekit oracle, fail.cdm-lenient-date)."""
    if not CCSDS_DATE.match(s):
        raise CdmFormatError(f"{key}: not a CCSDS date: {s!r}")
    try:
        base = s.rstrip("Z")
        return datetime.strptime(base, "%Y-%jT%H:%M:%S.%f" if "." in base else "%Y-%jT%H:%M:%S") if len(base.split("T")[0]) == 8             else datetime.fromisoformat(base)
    except ValueError:
        raise CdmFormatError(f"{key}: not a valid date: {s!r}") from None


def parse_cdm(text: str) -> Dict:
    warnings: List[str] = []
    if "\u2212" in text:
        warnings.append(f"normalised {text.count(chr(0x2212))} typographic minus sign(s) U+2212 to '-'")
        text = text.replace("\u2212", "-")
    head: Dict = {}
    objects: List[Dict] = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("COMMENT"):
            continue
        m = LINE.match(line)
        if not m:
            raise CdmFormatError(f"line {n}: not a KEY = VALUE line: {raw!r}")
        key, val, unit = m.group(1), m.group(2), m.group(3)
        if not _known(key):
            raise CdmFormatError(f"line {n}: unknown keyword {key!r} (not in CCSDS 508.0-B-1)")
        if key == "OBJECT":
            if val not in ("OBJECT1", "OBJECT2") or len(objects) >= 2 or (objects and val == "OBJECT1"):
                raise CdmFormatError(f"line {n}: unexpected OBJECT = {val} (exactly OBJECT1 then OBJECT2)")
            objects.append({})
        target = objects[-1] if objects else head
        if key in target:
            raise CdmFormatError(f"line {n}: duplicate keyword {key}")
        exp = UNITS.get(key)
        if unit is not None and exp is not None and unit != exp:
            raise CdmFormatError(f"line {n}: {key} unit [{unit}], standard requires [{exp}]")
        if key in DATES:
            target[key] = _date(val, key)
        elif key in TEXT or key.startswith("OPERATOR_"):
            target[key] = val
        else:
            try:
                target[key] = float(val)
            except ValueError:
                raise CdmFormatError(f"line {n}: {key} must be numeric, got {val!r}") from None
    if len(objects) != 2:
        raise CdmFormatError(f"a CDM has exactly 2 objects, found {len(objects)}")
    miss = [k for k in HEADER_REQ + RELATIVE_REQ if k not in head]
    for o in objects:
        miss += [f"{o.get('OBJECT', '?')}.{k}" for k in OBJECT_REQ if k not in o]
    if miss:
        raise CdmFormatError(f"missing obligatory keyword(s): {miss}")
    return {"header": head, "object1": objects[0], "object2": objects[1], "warnings": warnings}


def covariance_rtn(obj: Dict) -> List[List[float]]:
    """Symmetric 6x6 RTN covariance (m, m/s) from the 21 lower-triangular elements."""
    names = ["R", "T", "N", "RDOT", "TDOT", "NDOT"]
    pre = ["CR", "CT", "CN", "CRDOT", "CTDOT", "CNDOT"]
    c = [[0.0] * 6 for _ in range(6)]
    for i in range(6):
        for j in range(i + 1):
            v = obj[f"{pre[i]}_{names[j]}"]
            c[i][j] = c[j][i] = v
    return c


def miss_distance_from_states(cdm: Dict) -> float:
    """|r1 - r2| at TCA in metres, from the two state vectors: an independent check of MISS_DISTANCE."""
    o1, o2 = cdm["object1"], cdm["object2"]
    return 1000.0 * math.sqrt(sum((o1[k] - o2[k]) ** 2 for k in ("X", "Y", "Z")))


def consistency_report(cdm: Dict, tol_m: float = 1.0) -> Dict:
    """Cross-check the declared MISS_DISTANCE against (a) the two state vectors and (b) RELATIVE_POSITION_R/T/N when
    present. Flags are facts about the message, not corrections: the parser never edits values."""
    h = cdm["header"]
    out = {"declared_m": h["MISS_DISTANCE"], "from_states_m": miss_distance_from_states(cdm), "flags": []}
    if abs(out["from_states_m"] - out["declared_m"]) > tol_m:
        out["flags"].append("STATES_INCONSISTENT_WITH_MISS_DISTANCE")
    if all(k in h for k in ("RELATIVE_POSITION_R", "RELATIVE_POSITION_T", "RELATIVE_POSITION_N")):
        out["from_rtn_m"] = math.sqrt(sum(h[k] ** 2 for k in ("RELATIVE_POSITION_R", "RELATIVE_POSITION_T", "RELATIVE_POSITION_N")))
        if abs(out["from_rtn_m"] - out["declared_m"]) > tol_m:
            out["flags"].append("RTN_INCONSISTENT_WITH_MISS_DISTANCE")
    return out


def _sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _unit(a):
    n = math.sqrt(_dot(a, a))
    return [x / n for x in a]


def rtn_axes(r_km, v_kms):
    """Object-1 RTN unit vectors (CCSDS 508.0-B annex: R along r, N along r x v, T = N x R)."""
    R = _unit(r_km)
    N = _unit(_cross(r_km, v_kms))
    return R, _cross(N, R), N


def min_eigenvalue(m: List[List[float]], sweeps: int = 60) -> float:
    """Smallest eigenvalue of a symmetric matrix (cyclic Jacobi, standard library only)."""
    a = [row[:] for row in m]
    n = len(a)
    for _ in range(sweeps):
        off = sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off < 1e-30 * max(1.0, sum(a[i][i] ** 2 for i in range(n))):
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if a[p][q] == 0.0:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = math.copysign(1.0, theta) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
    return min(a[i][i] for i in range(n))


def deep_consistency(cdm: Dict, tol_m: float = 1.0, tol_ms: float = 0.1, psd_rel_tol: float = 1e-4) -> Dict:
    """Component-level internal consistency of a CDM (S.T.A.R. 2026-10-05). Beyond consistency_report (norms only):
    (1) RELATIVE_POSITION_R/T/N against r2 - r1 projected on object-1 RTN axes, component by component;
    (2) RELATIVE_SPEED against |v2 - v1|; (3) RELATIVE_VELOCITY_R/T/N against v2 - v1 on the same axes;
    (4) each object's 6x6 RTN covariance positive semi-definite (min eigenvalue >= -psd_rel_tol * max diagonal).
    Only keywords present in the message are checked; nothing is corrected. Units: m and m/s.
    psd_rel_tol 1e-4: CDM covariances are printed to 4-5 significant digits; the official example 3.6.2 has a minimum
    eigenvalue of -0.006 m^2 against a 2533 m^2 diagonal, which is rounding, not an error (2026-10-05)."""
    o1, o2, h = cdm["object1"], cdm["object2"], cdm["header"]
    r1 = [o1[k] for k in ("X", "Y", "Z")]
    v1 = [o1[k] for k in ("X_DOT", "Y_DOT", "Z_DOT")]
    dr = _sub([o2[k] for k in ("X", "Y", "Z")], r1)
    dv = _sub([o2[k] for k in ("X_DOT", "Y_DOT", "Z_DOT")], v1)
    axes = rtn_axes(r1, v1)
    out = {"checks": {}, "flags": []}
    pos = {c: 1000.0 * _dot(dr, ax) for c, ax in zip("RTN", axes)}
    vel = {c: 1000.0 * _dot(dv, ax) for c, ax in zip("RTN", axes)}
    for c in "RTN":
        k = f"RELATIVE_POSITION_{c}"
        if k in h:
            out["checks"][k] = {"declared": h[k], "computed": pos[c]}
            if abs(h[k] - pos[c]) > tol_m:
                out["flags"].append(f"{k}_INCONSISTENT_WITH_STATES")
        k = f"RELATIVE_VELOCITY_{c}"
        if k in h:
            out["checks"][k] = {"declared": h[k], "computed": vel[c]}
            if abs(h[k] - vel[c]) > tol_ms:
                out["flags"].append(f"{k}_INCONSISTENT_WITH_STATES")
    if "RELATIVE_SPEED" in h:
        speed = 1000.0 * math.sqrt(_dot(dv, dv))
        out["checks"]["RELATIVE_SPEED"] = {"declared": h["RELATIVE_SPEED"], "computed": speed}
        if abs(h["RELATIVE_SPEED"] - speed) > tol_ms:
            out["flags"].append("RELATIVE_SPEED_INCONSISTENT_WITH_STATES")
    for name, obj in (("OBJECT1", o1), ("OBJECT2", o2)):
        try:
            cov = covariance_rtn(obj)
        except KeyError:
            continue
        lam = min_eigenvalue(cov)
        scale = max(abs(cov[i][i]) for i in range(6)) or 1.0
        out["checks"][f"{name}_COVARIANCE_MIN_EIGENVALUE"] = {"computed": lam, "scale": scale}
        if lam < -psd_rel_tol * scale:
            out["flags"].append(f"{name}_COVARIANCE_NOT_POSITIVE_SEMIDEFINITE")
    return out
