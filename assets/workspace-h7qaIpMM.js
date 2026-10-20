import{installWheels as e,loadPy as t}from"./runner-CY_6OsPt.js";var n=`"""S.T.A.R. Workspace tasks: everyday jobs done by released S.T.A.R. packages, with a verification receipt.

Runs unchanged in two places: in the visitor's browser (Pyodide, with the packages' published wheels) and on a PC
under pytest (tests/test_ws_tasks.py, with independent references: pyproj, numpy, zlib). Nothing here contacts the
network or keeps data: the input arrives as text or bytes, the answer leaves as a dictionary.

Every task returns:
  ok            True when a result was produced
  result        the numbers, in plain units
  tools         [{"name", "version"}] - the S.T.A.R. packages (and standard modules) that did the work
  transforms    [{"code", "before", "after"}] - every change made to the input before using it
  checks        [{"code", "ok", "args"}] - deterministic checks and their outcome
  warnings      [{"code", "args"}] - things a person should look at
  error         {"code", "args"} when ok is False (never a Python traceback)
Messages are codes with arguments; the page turns them into English or Italian.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import zlib

MAX_ROWS = 50_000
MAX_TEXT = 5_000_000            # characters of CSV text
MAX_CRC_BYTES = 1_000_000       # star_crc works bit by bit (about 4 s per MB on a laptop): the cross-check stops here
R_MEAN_M = 6371008.8            # IUGG mean Earth radius, for the spherical comparison


def _version(module, dist):
    try:
        from importlib.metadata import version
        return version(dist)
    except Exception:  # noqa: BLE001 - metadata may be missing when the module is imported from a source tree
        return getattr(module, "__version__", "?")


def _tool(module, dist):
    return {"name": dist, "version": _version(module, dist)}


class TaskError(Exception):
    def __init__(self, code, **args):
        super().__init__(code)
        self.code, self.args_ = code, args


def _answer(result, tools, transforms, checks, warnings):
    return {"ok": True, "result": result, "tools": tools, "transforms": transforms, "checks": checks, "warnings": warnings}


def run(task: str, params_json: str, data: bytes | None = None) -> str:
    """Entry point used by the page: JSON in, JSON out, never an exception."""
    try:
        params = json.loads(params_json or "{}")
        fn = TASKS.get(task)
        if fn is None:
            raise TaskError("unknown_task", task=task)
        out = fn(params, data) if task == "fingerprint" else fn(params)
    except Exception as e:  # noqa: BLE001 - the page must always get an answer it can show
        if hasattr(e, "code") and hasattr(e, "args_"):      # TaskError, or ws_products.ProductError
            out = {"ok": False, "error": {"code": e.code, "args": e.args_}}
        else:
            out = {"ok": False, "error": {"code": "internal", "args": {"detail": f"{type(e).__name__}: {e}"[:300]}}}
    return json.dumps(out, ensure_ascii=False, allow_nan=False, default=str)


# ---------------------------------------------------------------- parsing what people type
_NUM = re.compile(r"\\d+(?:[.,]\\d+)?")
_SEP_OK = re.compile(r"^[\\s°'\\"′″dms.,:]*$")


def parse_number(text, what):
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        if not math.isfinite(text):
            raise TaskError("not_a_number", field=what, value=str(text))
        return float(text), None
    s = "" if text is None else str(text).strip()          # 0 is a value, not an empty field
    if not s:
        raise TaskError("empty", field=what)
    t = s.replace("−", "-")                          # spaces inside are NOT removed: "1 2 3" must not become 123
    if re.fullmatch(r"[+-]?\\d+,\\d+", t):          # decimal comma, as written in Italy
        v = float(t.replace(",", "."))
        return v, {"code": "decimal_comma", "before": s, "after": repr(v)}
    try:
        v = float(t)
    except ValueError:
        raise TaskError("not_a_number", field=what, value=s[:40]) from None
    if not math.isfinite(v):
        raise TaskError("not_a_number", field=what, value=s[:40])
    return v, None


def parse_angle(text, kind):
    """Decimal degrees ('41.9', '41,9', '-12.5') or degrees, minutes, seconds ('41 54 10 N', '41N', '12d29m46sO')."""
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        return parse_number(text, kind)
    s = "" if text is None else str(text).strip()          # 0 is a value, not an empty field
    if not s:
        raise TaskError("empty", field=kind)
    try:
        return parse_number(s, kind)
    except TaskError:
        pass
    body = s.replace("−", "-")
    sign = None
    if body[:1] in "+-":
        sign, body = body[0], body[1:]
    hemi = None
    last, prev = body[-1:], body[-2:-1]
    # a final N/S/E/W/O is a hemisphere; after a lowercase unit (10sS) the capital letter is the hemisphere
    if last.upper() in ("N", "S", "E", "W", "O") and (not prev.isalpha() or (last.isupper() and prev in "dms")):
        hemi, body = body[-1].upper(), body[:-1]
    nums = _NUM.findall(body)
    if not 1 <= len(nums) <= 3 or not _SEP_OK.match(_NUM.sub("", body)):
        raise TaskError("bad_angle", field=kind, value=s[:40])
    parts = [float(x.replace(",", ".")) for x in nums] + [0.0, 0.0]
    deg, mins, secs = parts[0], parts[1], parts[2]
    if mins >= 60 or secs >= 60 or (len(nums) > 1 and deg != int(deg)):
        raise TaskError("bad_angle", field=kind, value=s[:40])
    v = deg + mins / 60 + secs / 3600
    neg = sign == "-"
    if hemi:
        if kind.startswith("lat") and hemi not in "NS" or kind.startswith("lon") and hemi not in "EWO":
            raise TaskError("wrong_hemisphere", field=kind, value=s[:40])
        neg = neg != (hemi in "SWO")                        # O = Ovest, west in Italian
    v = -v if neg else v
    return v, {"code": "dms_to_decimal", "before": s, "after": f"{v:.8f}"}


def _latlon(params, a, b):
    lat, t1 = parse_angle(params.get(a), "lat")
    lon, t2 = parse_angle(params.get(b), "lon")
    if not -90 <= lat <= 90:
        raise TaskError("lat_range", value=lat)
    if not -180 <= lon <= 180:
        raise TaskError("lon_range", value=lon)
    return lat, lon, [t for t in (t1, t2) if t]


# ---------------------------------------------------------------- 1. distance between two places
def task_distance(params):
    import star_geodesic as geo
    import star_sphere as sph
    lat1, lon1, tr1 = _latlon(params, "lat1", "lon1")
    lat2, lon2, tr2 = _latlon(params, "lat2", "lon2")
    checks = [{"code": "coords_in_range", "ok": True, "args": {}}]
    warnings = []
    try:
        s12, az1, az2 = geo.inverse(lat1, lon1, lat2, lon2)
    except RuntimeError:
        raise TaskError("antipodal") from None
    sep = sph.separation_deg(lon1, lat1, lon2, lat2)
    s_sph = math.radians(sep) * R_MEAN_M
    if s12 == 0:
        warnings.append({"code": "same_point", "args": {}})
        checks.append({"code": "round_trip", "ok": True, "args": {"mm": 0.0}})
    elif s12 > 20_000_000:
        # star_geodesic.direct() documents a 20,000 km limit; the longest geodesic is about 20,004 km
        warnings.append({"code": "round_trip_skipped", "args": {"km": s12 / 1000}})
    else:
        # forward-backward check: walk the computed distance along the computed azimuth and see where we land
        lat_b, lon_b, _ = geo.direct(lat1, lon1, az1, s12)
        back = geo.inverse(lat2, lon2, lat_b, lon_b)[0]
        checks.append({"code": "round_trip", "ok": back < 1e-3, "args": {"mm": back * 1000}})
    diff = (s_sph - s12) / s12 * 100 if s12 else 0.0
    # the path itself, for the map: points along the geodesic (direct problem), within the package's 20,000 km limit
    path = [[lat1, lon1]]
    if 0 < s12 <= 20_000_000:
        for k in range(1, 64):
            la, lo, _ = geo.direct(lat1, lon1, az1, s12 * k / 64)
            path.append([la, lo])
    path.append([lat2, lon2])
    return _answer(
        {"distance_m": s12, "distance_km": s12 / 1000, "azimuth_start_deg": az1, "azimuth_end_deg": az2,
         "spherical_km": s_sph / 1000, "spherical_diff_percent": diff, "separation_deg": sep,
         "points": [[lat1, lon1], [lat2, lon2]], "path": path},
        [_tool(geo, "star-geodesic"), _tool(sph, "star-sphere")], tr1 + tr2, checks, warnings)


# ---------------------------------------------------------------- 2. coordinate formats
def _dms_text(fields, pos, neg):
    sign, d, m, s, frac = fields
    return f"{d}°{m:02d}'{s:02d}.{frac:03d}\\" {neg if sign == '-' else pos}"


def task_coords(params):
    import star_geodesic as geo
    import star_sexagesimal as sx
    import star_utm as utm
    lat, lon, tr = _latlon(params, "lat", "lon")
    checks, warnings = [{"code": "coords_in_range", "ok": True, "args": {}}], []
    res = {"lat": lat, "lon": lon, "lat_dms": _dms_text(sx.deg_to_dms(lat, 3), "N", "S"), "lon_dms": _dms_text(sx.deg_to_dms(lon, 3), "E", "W")}
    back = sx.dms_to_deg(*sx.deg_to_dms(lat, 6)[:3], sx.deg_to_dms(lat, 6)[3] + sx.deg_to_dms(lat, 6)[4] / 1e6)
    checks.append({"code": "dms_round_trip", "ok": abs(back - lat) < 1e-9, "args": {"deg": abs(back - lat)}})
    tools = [_tool(sx, "star-sexagesimal")]
    if -80 <= lat <= 84:
        zone, hemi, e, n = utm.utm_forward(lat, lon)
        lat_b, lon_b = utm.utm_inverse(zone, hemi, e, n)
        err = geo.inverse(lat, lon, lat_b, lon_b)[0]
        res.update({"utm_zone": zone, "utm_hemisphere": hemi, "utm_easting": e, "utm_northing": n})
        checks.append({"code": "utm_round_trip", "ok": err < 1e-3, "args": {"mm": err * 1000}})
        tools += [_tool(utm, "star-utm"), _tool(geo, "star-geodesic")]
        if 56 <= lat < 64 and 3 <= lon < 12 or 72 <= lat <= 84 and 0 <= lon < 42:
            warnings.append({"code": "utm_special_zone", "args": {"zone": zone}})
    else:
        warnings.append({"code": "utm_polar", "args": {}})
    return _answer(res, tools, tr, checks, warnings)


# ---------------------------------------------------------------- CSV reading shared by tasks 3 and 4
def _read_table(text):
    if not isinstance(text, str) or not text.strip():
        raise TaskError("empty_file")
    if len(text) > MAX_TEXT:
        raise TaskError("file_too_big", limit_mb=MAX_TEXT // 1_000_000)
    transforms = []
    if text.startswith("﻿"):
        text = text[1:]
        transforms.append({"code": "bom_removed", "before": "BOM", "after": ""})
    sample = text[:20000]
    # a binary file read as text is full of control characters: say so instead of inventing columns
    controls = sum(1 for ch in sample if (ord(ch) < 32 and ch not in "\\t\\r\\n") or ch == "\\ufffd")
    if controls > max(5, len(sample) // 100):
        raise TaskError("not_text")
    counts = {d: sample.count(d) for d in (";", "\\t", ",", "|")}          # "|" added 2026-10-19 (mandate input matrix)
    delim = max(counts, key=counts.get) if any(counts.values()) else ","
    try:
        # newline="" as the csv module requires, so a lone carriage return inside a cell is not an error
        rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delim))
    except csv.Error as e:
        raise TaskError("bad_csv", detail=str(e)[:120]) from None
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        raise TaskError("empty_file")
    if len(rows) > MAX_ROWS:
        raise TaskError("too_many_rows", limit=MAX_ROWS)
    decimal_comma = delim != "," and any(re.fullmatch(r"\\s*[+-]?\\d+,\\d+\\s*", c) for r in rows[:200] for c in r)

    def num(cell):
        c = cell.strip().replace("−", "-")
        if not c:
            return None, "missing"
        if decimal_comma:
            c2 = c.replace(".", "").replace(",", ".") if re.fullmatch(r"[+-]?\\d{1,3}(\\.\\d{3})+(,\\d+)?|[+-]?\\d+,\\d+|[+-]?\\d+", c) else c
        else:
            c2 = c.replace(",", "") if re.fullmatch(r"[+-]?\\d{1,3}(,\\d{3})+(\\.\\d+)?", c) else c
        try:
            v = float(c2)
        except ValueError:
            return None, "non_numeric"
        if not math.isfinite(v):
            return None, "non_numeric"
        return v, ("converted" if c2 != c else "ok")
    first_numeric = sum(num(c)[0] is not None for c in rows[0])
    header = first_numeric < max(1, len(rows[0]) // 2) and len(rows) > 1
    names = [c.strip() or f"col{k + 1}" for k, c in enumerate(rows[0])] if header else [f"col{k + 1}" for k in range(len(rows[0]))]
    body = rows[1:] if header else rows
    width = len(names)
    ragged = [k + (2 if header else 1) for k, r in enumerate(body) if len(r) != width]
    return {"delimiter": delim, "decimal_comma": decimal_comma, "header": header, "names": names, "body": body,
            "ragged": ragged, "num": num, "transforms": transforms}


def _column(tab, wanted):
    names = tab["names"]
    if wanted in (None, ""):
        best, best_n = None, -1
        for k in range(len(names)):
            n = sum(tab["num"](r[k])[0] is not None for r in tab["body"][:500] if k < len(r))
            if n > best_n:
                best, best_n = k, n
        return best
    if isinstance(wanted, int) or str(wanted).isdigit():
        k = int(wanted)
        if not 0 <= k < len(names):
            raise TaskError("no_column", name=str(wanted))
        return k
    if wanted in names:
        return names.index(wanted)
    raise TaskError("no_column", name=str(wanted)[:40])


# ---------------------------------------------------------------- 3. check and summarise a column of numbers
def task_column(params):
    import star_quantile as qn
    import star_stats as st
    tab = _read_table(params.get("text"))
    k = _column(tab, params.get("column"))
    name = tab["names"][k]
    values, statuses, transforms, bad = [], [], list(tab["transforms"]), []
    first_row = 2 if tab["header"] else 1
    for i, r in enumerate(tab["body"]):
        cell = r[k] if k < len(r) else ""
        v, status = tab["num"](cell)
        statuses.append(status)
        if v is None:
            bad.append({"row": first_row + i, "value": cell[:40], "why": status})
        else:
            values.append((first_row + i, v))
            if status == "converted" and sum(t["code"] == "number_format" for t in transforms) < 10:
                transforms.append({"code": "number_format", "before": cell.strip(), "after": repr(v)})
    n_conv = sum(s == "converted" for s in statuses)
    checks = [
        {"code": "columns_consistent", "ok": not tab["ragged"], "args": {"rows": tab["ragged"][:10], "count": len(tab["ragged"])}},
        {"code": "numeric_share", "ok": len(values) >= 0.9 * len(statuses), "args": {"numeric": len(values), "total": len(statuses)}},
    ]
    if len(values) < 2:
        raise TaskError("too_few_values", n=len(values), column=name[:40])
    xs = [v for _, v in values]
    med, mad = qn.median(xs), qn.mad(xs)
    # modified z-score (Iglewicz and Hoaglin): |x - median| / (1.4826 MAD) above 3.5 is flagged for a person to look at
    scale = 1.4826 * mad
    outliers = [{"row": r, "value": v, "score": abs(v - med) / scale} for r, v in values if scale > 0 and abs(v - med) / scale > 3.5]
    checks.append({"code": "outliers", "ok": not outliers, "args": {"count": len(outliers)}})
    res = {"column": name, "columns": tab["names"], "delimiter": tab["delimiter"], "decimal_comma": tab["decimal_comma"], "header": tab["header"],
           "n": len(xs), "missing": sum(s == "missing" for s in statuses), "non_numeric": sum(s == "non_numeric" for s in statuses),
           "converted": n_conv, "mean": st.mean(xs), "stdev": st.stdev(xs), "min": min(xs), "max": max(xs), "median": med,
           "q1": qn.quantile(xs, 0.25), "q3": qn.quantile(xs, 0.75), "iqr": qn.iqr(xs), "mad": mad,
           "bad_rows": bad[:20], "bad_total": len(bad), "outliers": sorted(outliers, key=lambda o: -o["score"])[:20], "outliers_total": len(outliers)}
    # a cleaned copy: the original columns plus the number read and its status, row by row
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\\n")
    w.writerow(tab["names"] + [f"{name}_value", f"{name}_status"])
    flagged = {o["row"] for o in outliers}
    for i, r in enumerate(tab["body"]):
        v, status = tab["num"](r[k] if k < len(r) else "")
        status = "outlier" if first_row + i in flagged else status
        w.writerow(list(r) + (["" for _ in range(len(tab["names"]) - len(r))] if len(r) < len(tab["names"]) else []) + ["" if v is None else repr(v), status])
    res["cleaned_csv"] = out.getvalue()
    warnings = [{"code": "converted_numbers", "args": {"count": n_conv}}] if n_conv else []
    return _answer(res, [_tool(st, "star-stats"), _tool(qn, "star-quantile")], transforms, checks, warnings)


# ---------------------------------------------------------------- 4. straight-line fit
def task_linefit(params):
    import star_linefit as lf
    tab = _read_table(params.get("text"))
    if len(tab["names"]) < 2:
        raise TaskError("need_two_columns")
    kx = _column(tab, params.get("x") if params.get("x") not in (None, "") else 0)
    ky = _column(tab, params.get("y") if params.get("y") not in (None, "") else (1 if kx != 1 else 0))
    if kx == ky:
        raise TaskError("same_column")
    pts, skipped = [], []
    first_row = 2 if tab["header"] else 1
    for i, r in enumerate(tab["body"]):
        x, sx_ = tab["num"](r[kx] if kx < len(r) else "")
        y, sy_ = tab["num"](r[ky] if ky < len(r) else "")
        (pts.append((x, y)) if x is not None and y is not None else skipped.append(first_row + i))
    if len(pts) < 3:
        raise TaskError("too_few_points", n=len(pts))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    if max(xs) == min(xs):
        raise TaskError("x_constant")
    slope, intercept = lf.fit(xs, ys)
    s_slope, s_icpt, s_res = lf.fit_errors(xs, ys)
    try:
        r = lf.correlation(xs, ys)
    except ValueError:
        r = float("nan")
    resid = [y - (slope * x + intercept) for x, y in pts]
    worst = max(range(len(pts)), key=lambda i: abs(resid[i]))
    checks = [{"code": "enough_points", "ok": len(pts) >= 5, "args": {"n": len(pts)}},
              {"code": "rows_skipped", "ok": not skipped, "args": {"count": len(skipped), "rows": skipped[:10]}}]
    if s_res > 0 and abs(resid[worst]) > 3 * s_res:
        checks.append({"code": "large_residual", "ok": False, "args": {"x": xs[worst], "y": ys[worst], "times": abs(resid[worst]) / s_res}})
    res = {"x_name": tab["names"][kx], "y_name": tab["names"][ky], "n": len(pts), "slope": slope, "intercept": intercept,
           "slope_err": s_slope, "intercept_err": s_icpt, "residual_sd": s_res, "r": None if math.isnan(r) else r,
           "r2": None if math.isnan(r) else r * r, "points": pts[:2000], "columns": tab["names"]}
    return _answer(res, [_tool(lf, "star-linefit")], list(tab["transforms"]), checks, [])


# ---------------------------------------------------------------- 5. file fingerprint
def _reflect32(v):
    out = 0
    for _ in range(32):
        out = (out << 1) | (v & 1)
        v >>= 1
    return out


def crc32_star(sc, data):
    """CRC-32/ISO-HDLC with star_crc, which accepts at most 64 KiB per call: blocks are chained by passing the
    register on (reflected back, because the algorithm is reflected). Equal to zlib.crc32 at every length (tested)."""
    if len(data) <= sc.MAX_BYTES:
        return sc.crc32(data)
    state = 0xFFFFFFFF
    for i in range(0, len(data), sc.MAX_BYTES):
        state = _reflect32(sc.crc(data[i:i + sc.MAX_BYTES], 32, 0x04C11DB7, state, True, True, 0))
    return _reflect32(state) ^ 0xFFFFFFFF
def task_fingerprint(params, data):
    import star_crc as sc
    if data is None or len(data) == 0:
        raise TaskError("empty_file")
    sha256 = hashlib.sha256(data).hexdigest()
    res = {"bytes": len(data), "sha256": sha256, "sha1": hashlib.sha1(data).hexdigest(), "md5": hashlib.md5(data).hexdigest()}
    checks, warnings, tools = [], [], [{"name": "hashlib, zlib (Python standard library)", "version": "-"}]
    c2 = zlib.crc32(data) & 0xFFFFFFFF
    res["crc32"] = f"{c2:08x}"
    if len(data) <= MAX_CRC_BYTES:
        c1 = crc32_star(sc, data)
        checks.append({"code": "crc_two_implementations", "ok": c1 == c2, "args": {"star": f"{c1:08x}", "zlib": f"{c2:08x}"}})
        tools.insert(0, _tool(sc, "star-crc"))
    else:
        warnings.append({"code": "crc_skipped", "args": {"limit_mb": MAX_CRC_BYTES // 1_000_000}})
    expected = re.sub(r"[\\s:-]", "", str(params.get("expected") or "")).lower()
    if expected:
        kind = {8: "crc32", 32: "md5", 40: "sha1", 64: "sha256"}.get(len(expected))
        if not kind or not re.fullmatch(r"[0-9a-f]+", expected):
            raise TaskError("bad_expected", length=len(expected))
        res["compared"] = kind
        res["match"] = res[kind] == expected
        checks.append({"code": "matches_expected", "ok": res["match"], "args": {"kind": kind}})
    return _answer(res, tools, [], checks, warnings)


# ---------------------------------------------------------------- 6. unit conversion
def task_units(params):
    import star_units as su
    v, tr = parse_number(params.get("value"), "value")
    a, b = str(params.get("from") or ""), str(params.get("to") or "")
    known = su.units()
    if a not in known or b not in known:
        raise TaskError("unknown_unit", unit=a if a not in known else b)
    da, db = su.dimension(a), su.dimension(b)
    if da != db:
        raise TaskError("different_dimensions", a=a, da=da, b=b, db=db)
    try:
        if da == "temperature":
            out = su.convert_temperature(v, a, b)
            back = su.convert_temperature(out, b, a)
        else:
            out = su.convert(v, a, b)
            back = su.convert(out, b, a)
    except ValueError as e:
        raise TaskError("unit_refused", detail=str(e)[:120]) from None
    rel = abs(back - v) / abs(v) if v else abs(back)
    checks = [{"code": "same_dimension", "ok": True, "args": {"dimension": da}},
              {"code": "unit_round_trip", "ok": rel < 1e-12, "args": {"rel": rel}}]
    res = {"value": v, "from": a, "to": b, "result": out, "dimension": da,
           "factor": None if da == "temperature" or v == 0 else out / v}
    return _answer(res, [_tool(su, "star-units")], [tr] if tr else [], checks, [])


def units_catalogue():
    import star_units as su
    out = {}
    for u in su.units():
        out.setdefault(su.dimension(u), []).append(u)
    return json.dumps(out)


TASKS = {"distance": task_distance, "coords": task_coords, "column": task_column, "linefit": task_linefit,
         "fingerprint": task_fingerprint, "units": task_units}

# the everyday products (first batch 2026-10-20) live in ws_products.py; the page loads that module before this one.
# Imported without a fallback on purpose: a missing products module must fail loudly, not hide the products.
import ws_products  # noqa: E402

TASKS.update(ws_products.TASKS)
`,r=`"""S.T.A.R. everyday products (first batch, 2026-10-20): Italian tax code, Italian VAT number, IBAN, working days.

Pure Python (standard library only), so it runs unchanged in the visitor's browser (Pyodide) and under pytest, where it
is compared with independent implementations (python-stdnum, schwifty, holidays, dateutil) that are NEVER shipped.
Same contract as ws_tasks.py: a task returns result, tools, transforms, checks, warnings; errors carry a code.

Sources of the rules:
  codice fiscale  D.M. 23/12/1976 (format and check character), D.P.R. 605/1973; omocodia: letters L-V replace the
                  digits from the right (Agenzia delle Entrate)
  partita IVA     11 digits: 7 serial, 3 office code, 1 check digit computed with the Luhn mod-10 rule
  IBAN            ISO 13616 (structure), ISO 7064 MOD 97-10 (check digits), SWIFT IBAN registry (lengths)
  working days    L. 260/1949 art. 2 as amended (national holidays; 4 October from 2026, L. 151/2025; 17 March 2011 only,
                  D.L. 5/2011), Gregorian Easter
"""
from __future__ import annotations

import datetime as dt
import re

VERSION = "0.1.0"
TOOL = {"name": "S.T.A.R. everyday products (ws_products)", "version": VERSION}


class ProductError(Exception):
    """Same shape as ws_tasks.TaskError (code + args_), so the page shows a translated message, never a traceback."""
    def __init__(self, code, **args):
        super().__init__(code)
        self.code, self.args_ = code, args


def _answer(result, transforms, checks, warnings, tools=None):
    return {"ok": True, "result": result, "tools": tools or [TOOL], "transforms": transforms, "checks": checks, "warnings": warnings}


def _clean(text, field, allow=r"[\\s\\-\\.]"):
    s = "" if text is None else str(text)
    if not s.strip():
        raise ProductError("empty", field=field)
    if len(s) > 200:
        raise ProductError("too_long", field=field, limit=200)
    c = re.sub(allow, "", s).upper()
    tr = [{"code": "normalised", "before": s.strip()[:60], "after": c}] if c != s.strip() else []
    return c, tr


# ---------------------------------------------------------------- shared: the odd/even tables of the Italian check characters
ODD = {**dict(zip("0123456789", [1, 0, 5, 7, 9, 13, 15, 17, 19, 21])),
       **dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23]))}
EVEN = {**{d: int(d) for d in "0123456789"}, **{ch: i for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}}


def _odd_even_char(s):
    """Check character of the codice fiscale and of the Italian bank CIN: odd positions (1st, 3rd, ...) through ODD,
    even ones through EVEN, sum modulo 26 as a letter."""
    total = sum(ODD[ch] if i % 2 == 0 else EVEN[ch] for i, ch in enumerate(s))
    return chr(ord("A") + total % 26)


# ---------------------------------------------------------------- 1. codice fiscale
OMO = dict(zip("LMNPQRSTUV", "0123456789"))
OMO_POS = [14, 13, 12, 10, 9, 7, 6]           # digit positions, in the order the Agenzia substitutes them (right to left)
MONTHS = dict(zip("ABCDEHLMPRST", range(1, 13)))
CF_RE = re.compile(r"[A-Z]{6}[0-9LMNPQRSTUV]{2}[ABCDEHLMPRST][0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{3}[A-Z]")


def cf_check_char(first15):
    return _odd_even_char(first15)


def _letters(word):
    w = re.sub(r"[^A-Z]", "", _strip_accents(word).upper())
    cons = [c for c in w if c not in "AEIOU"]
    vows = [c for c in w if c in "AEIOU"]
    return cons, vows


def _strip_accents(s):
    table = str.maketrans("ÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜàáâäèéêëìíîïòóôöùúûüÇçÑñ", "AAAAEEEEIIIIOOOOUUUUaaaaeeeeiiiioooouuuuCcNn")
    return str(s).translate(table)


def cf_surname_code(surname):
    cons, vows = _letters(surname)
    return "".join((cons + vows + ["X"] * 3)[:3])


def cf_name_code(name):
    cons, vows = _letters(name)
    if len(cons) >= 4:
        return cons[0] + cons[2] + cons[3]
    return "".join((cons + vows + ["X"] * 3)[:3])


def task_cf(params):
    code, tr = _clean(params.get("code"), "code")
    if len(code) != 16:
        raise ProductError("cf_length", n=len(code))
    if not CF_RE.fullmatch(code):
        raise ProductError("cf_format")
    checks, warnings = [], []
    expected = cf_check_char(code[:15])
    checks.append({"code": "cf_check_char", "ok": expected == code[15], "args": {"expected": expected, "found": code[15]}})
    letters_at = [p for p in OMO_POS if code[p] in OMO]
    omocode = bool(letters_at)
    if omocode:
        in_order = letters_at == OMO_POS[:len(letters_at)]
        checks.append({"code": "cf_omocode_order", "ok": in_order, "args": {"n": len(letters_at)}})
    base = "".join(OMO.get(ch, ch) if i in OMO_POS else ch for i, ch in enumerate(code))
    yy, month, day = int(base[6:8]), MONTHS[base[8]], int(base[9:11])
    sex = "F" if day > 40 else "M"
    dd = day - 40 if day > 40 else day
    today = dt.date.today()
    births = []
    for century in (1900, 2000):
        try:
            d = dt.date(century + yy, month, dd)
        except ValueError:
            continue
        if d <= today:
            births.append(d.isoformat())
    checks.append({"code": "cf_birth_date", "ok": bool(births), "args": {"day": day, "month": month}})
    place = base[11:15]
    res = {"code": code, "valid": all(c["ok"] for c in checks if c["code"] != "cf_omocode_order"),
           "check_char_expected": expected, "omocode": omocode, "omocode_positions": len(letters_at), "base_code": base[:15] + cf_check_char(base[:15]),
           "sex": sex, "birth_day": dd, "birth_month": month, "birth_year_2digit": f"{yy:02d}", "birth_date_candidates": births,
           "place_code": place, "place_kind": "foreign_country" if place[0] == "Z" else "italian_municipality",
           "surname_code": code[:3], "name_code": code[3:6]}
    for key, fn, field in (("surname", cf_surname_code, "surname_code"), ("name", cf_name_code, "name_code")):
        given = (params.get(key) or "").strip()
        if given:
            mine = fn(given)
            checks.append({"code": f"cf_{key}_match", "ok": mine == code[:3] if key == "surname" else mine == code[3:6], "args": {"expected": mine}})
            res[f"{key}_given_code"] = mine
    if omocode:
        warnings.append({"code": "cf_omocode", "args": {"base": res["base_code"]}})
    if len(births) == 2:
        warnings.append({"code": "cf_century_ambiguous", "args": {"a": births[0][:4], "b": births[1][:4]}})
    warnings.append({"code": "cf_not_registry", "args": {}})
    return _answer(res, tr, checks, warnings)


# ---------------------------------------------------------------- 2. partita IVA
def piva_check_digit_italian(first10):
    """The rule as written for the partita IVA: digits in odd positions (1st, 3rd, ... 9th) added; digits in even positions
    (2nd ... 10th) doubled, minus 9 when the double exceeds 9, then added; check digit = (10 - total mod 10) mod 10."""
    total = 0
    for i, ch in enumerate(first10):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            d = d - 9 if d > 9 else d
        total += d
    return (10 - total % 10) % 10


def luhn_check_digit(payload):
    """The Luhn mod-10 rule, as usually stated: from the right of the payload, double every second digit starting with
    the rightmost one."""
    total = 0
    for i, ch in enumerate(reversed(payload)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            d = d - 9 if d > 9 else d
        total += d
    return (10 - total % 10) % 10


def task_piva(params):
    code, tr = _clean(params.get("code"), "code")
    if code.startswith("IT"):
        tr.append({"code": "country_prefix_removed", "before": code, "after": code[2:]})
        code = code[2:]
    if not code.isdigit():
        raise ProductError("piva_digits")
    if len(code) != 11:
        raise ProductError("piva_length", n=len(code))
    expected = piva_check_digit_italian(code[:10])
    office = int(code[7:10])
    checks = [{"code": "piva_check_digit", "ok": expected == int(code[10]), "args": {"expected": expected, "found": int(code[10])}},
              {"code": "piva_office_code", "ok": 1 <= office <= 100 or office in (120, 121, 888, 999), "args": {"office": f"{office:03d}"}},
              {"code": "piva_serial", "ok": code[:7] != "0000000", "args": {}}]
    res = {"code": code, "valid": all(c["ok"] for c in checks), "serial": code[:7], "office_code": f"{office:03d}",
           "check_digit_expected": expected, "luhn_same": luhn_check_digit(code[:10]) == expected}
    return _answer(res, tr, checks, [{"code": "piva_not_vies", "args": {}}])


# ---------------------------------------------------------------- 3. IBAN
# total IBAN length per country (SWIFT IBAN registry); checked in the tests against python-stdnum and schwifty
IBAN_LEN = {
    "AD": 24, "AE": 23, "AL": 28, "AT": 20, "AZ": 28, "BA": 20, "BE": 16, "BG": 22, "BH": 22, "BI": 27, "BR": 29, "BY": 28,
    "CH": 21, "CR": 22, "CY": 28, "CZ": 24, "DE": 22, "DJ": 27, "DK": 18, "DO": 28, "EE": 20, "EG": 29, "ES": 24, "FI": 18,
    "FK": 18, "FO": 18, "FR": 27, "GB": 22, "GE": 22, "GI": 23, "GL": 18, "GR": 27, "GT": 28, "HN": 28, "HR": 21, "HU": 28,
    "IE": 22, "IL": 23, "IQ": 23, "IS": 26, "IT": 27, "JO": 30, "KW": 30, "KZ": 20, "LB": 28, "LC": 32, "LI": 21, "LT": 20,
    "LU": 20, "LV": 21, "LY": 25, "MC": 27, "MD": 24, "ME": 22, "MK": 19, "MN": 20, "MR": 27, "MT": 31, "MU": 30, "NI": 28,
    "NL": 18, "NO": 15, "OM": 23, "PK": 24, "PL": 28, "PS": 29, "PT": 25, "QA": 29, "RO": 24, "RS": 22, "RU": 33, "SA": 24,
    "SC": 31, "SD": 18, "SE": 24, "SI": 19, "SK": 24, "SM": 27, "SO": 23, "ST": 25, "SV": 28, "TL": 23, "TN": 24, "TR": 26,
    "UA": 29, "VA": 22, "VG": 24, "XK": 20, "YE": 30,
}


def iban_mod97(iban):
    moved = iban[4:] + iban[:4]
    digits = "".join(str(int(ch, 36)) for ch in moved)
    return int(digits) % 97


def iban_check_digits(country, bban):
    return f"{98 - iban_mod97(country + '00' + bban):02d}"


def it_cin(abi_cab_account):
    return _odd_even_char(abi_cab_account)


def task_iban(params):
    code, tr = _clean(params.get("code"), "code")
    if code.startswith("IBAN"):
        tr.append({"code": "iban_prefix_removed", "before": code, "after": code[4:]})
        code = code[4:]
    if not re.fullmatch(r"[A-Z0-9]+", code):
        raise ProductError("iban_chars")
    if len(code) < 5 or not code[:2].isalpha() or not code[2:4].isdigit():
        raise ProductError("iban_format")
    country = code[:2]
    if country not in IBAN_LEN:
        raise ProductError("iban_country", country=country)
    checks = [{"code": "iban_length", "ok": len(code) == IBAN_LEN[country], "args": {"expected": IBAN_LEN[country], "found": len(code)}}]
    checks.append({"code": "iban_mod97", "ok": iban_mod97(code) == 1, "args": {"expected": iban_check_digits(country, code[4:]), "found": code[2:4]}})
    res = {"iban": code, "printed": " ".join(code[i:i + 4] for i in range(0, len(code), 4)), "country": country,
           "check_digits": code[2:4], "bban": code[4:]}
    if country in ("IT", "SM") and len(code) == 27:
        bban = code[4:]
        res.update(cin=bban[0], abi=bban[1:6], cab=bban[6:11], account=bban[11:])
        ok_shape = bool(re.fullmatch(r"[A-Z]\\d{10}[A-Z0-9]{12}", bban))
        checks.append({"code": "it_bban_format", "ok": ok_shape, "args": {}})
        if ok_shape:
            exp = it_cin(bban[1:])
            checks.append({"code": "it_cin", "ok": exp == bban[0], "args": {"expected": exp, "found": bban[0]}})
    res["valid"] = all(c["ok"] for c in checks)
    return _answer(res, tr, checks, [{"code": "iban_not_account", "args": {}}])


# ---------------------------------------------------------------- 4. working days and deadlines
def easter(year):
    """Gregorian Easter Sunday (the anonymous algorithm published by Meeus, valid for every Gregorian year)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    ll = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ll) // 451
    month = (h + ll - 7 * m + 114) // 31
    day = (h + ll - 7 * m + 114) % 31 + 1
    return dt.date(year, month, day)


FIXED = [((1, 1), "new_year"), ((1, 6), "epiphany"), ((4, 25), "liberation"), ((5, 1), "labour"), ((6, 2), "republic"),
         ((8, 15), "assumption"), ((11, 1), "all_saints"), ((12, 8), "immaculate"), ((12, 25), "christmas"), ((12, 26), "st_stephen")]
YEAR_MIN, YEAR_MAX = 2001, 2099      # 2 June has been a holiday again since 2001 (L. 336/2000)


def holidays_it(year, patron=None):
    """National holidays of Italy for a year (L. 260/1949 art. 2 as amended), plus an optional local patron day (month, day)."""
    if not YEAR_MIN <= year <= YEAR_MAX:
        raise ProductError("year_range", min=YEAR_MIN, max=YEAR_MAX, year=year)
    out = {dt.date(year, m, d): name for (m, d), name in FIXED}
    if year >= 2026:                                   # L. 8 ottobre 2025, n. 151
        out[dt.date(year, 10, 4)] = "st_francis"
    if year == 2011:                                   # one-off: 150 years of the unification of Italy (D.L. 22 febbraio 2011, n. 5)
        out[dt.date(2011, 3, 17)] = "unification_150"
    e = easter(year)
    out[e] = "easter"
    out[e + dt.timedelta(days=1)] = "easter_monday"
    if patron:
        try:
            p = dt.date(year, patron[0], patron[1])
        except ValueError:
            raise ProductError("patron_date", value=f"{patron[1]:02d}/{patron[0]:02d}") from None
        out.setdefault(p, "patron")
    return out


def _parse_date(text, field):
    s = "" if text is None else str(text).strip()
    if not s:
        raise ProductError("empty", field=field)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ProductError("bad_date", field=field, value=s[:30])


def _parse_patron(text):
    s = "" if text is None else str(text).strip()
    if not s:
        return None
    m = re.fullmatch(r"(\\d{1,2})[/\\-.](\\d{1,2})", s)
    if not m:
        raise ProductError("bad_patron", value=s[:20])
    return (int(m.group(2)), int(m.group(1)))          # typed as day/month


def _is_working(d, hol, saturday_working):
    if d.weekday() == 6 or (d.weekday() == 5 and not saturday_working):
        return False
    return d not in hol


def _holidays_between(a, b, patron):
    hol = {}
    for y in range(a.year, b.year + 1):
        hol.update(holidays_it(y, patron))
    return hol


def task_workdays(params):
    mode = params.get("mode") or "between"
    patron = _parse_patron(params.get("patron"))
    sat = bool(params.get("saturday_working"))
    start = _parse_date(params.get("start"), "start")
    checks, warnings, tr = [], [], []
    if mode == "between":
        end = _parse_date(params.get("end"), "end")
        if end < start:
            start, end = end, start
            tr.append({"code": "dates_swapped", "before": "", "after": ""})
        if (end - start).days > 3660:
            raise ProductError("span_too_long", limit_years=10)
        hol = _holidays_between(start, end, patron)
        days = [start + dt.timedelta(days=k) for k in range((end - start).days + 1)]
        working = [d for d in days if _is_working(d, hol, sat)]
        listed = sorted((d, n) for d, n in hol.items() if start <= d <= end)
        res = {"mode": mode, "start": start.isoformat(), "end": end.isoformat(), "calendar_days": len(days),
               "working_days": len(working), "both_ends_included": True,
               "weekend_days": sum(1 for d in days if d.weekday() == 6 or (d.weekday() == 5 and not sat)),
               "holidays_on_weekdays": [[d.isoformat(), n] for d, n in listed if d.weekday() < (6 if sat else 5)],
               "holidays_all": [[d.isoformat(), n] for d, n in listed]}
    else:
        n = params.get("n")
        try:
            n = int(str(n).strip())
        except (TypeError, ValueError):
            raise ProductError("bad_n", value=str(n)[:20]) from None
        if not 1 <= n <= 1000:
            raise ProductError("n_range", min=1, max=1000)
        hol = _holidays_between(start, start + dt.timedelta(days=n * 3 + 400), patron)
        d, count, skipped = start, 0, []
        while count < n:
            d += dt.timedelta(days=1)
            if _is_working(d, hol, sat):
                count += 1
            elif d in hol:
                skipped.append([d.isoformat(), hol[d]])
        res = {"mode": mode, "start": start.isoformat(), "n": n, "deadline": d.isoformat(), "weekday": d.weekday(),
               "start_day_counted": False, "holidays_skipped": skipped}
    res["saturday_working"] = sat
    res["patron"] = f"{patron[1]:02d}/{patron[0]:02d}" if patron else ""
    # bridge days ("ponti"): a working day between a holiday and the weekend, in the period shown
    a, b = dt.date.fromisoformat(res["start"]), dt.date.fromisoformat(res.get("end") or res["deadline"])
    hol_all = _holidays_between(a, b, patron)
    bridges = []
    if not sat:      # a bridge sits between a holiday and the weekend: Monday before a Tuesday holiday, Friday after a Thursday one
        for h in sorted(x for x in hol_all if a <= x <= b):
            for cand, wd in ((h - dt.timedelta(days=1), 0), (h + dt.timedelta(days=1), 4)):
                if a <= cand <= b and cand.weekday() == wd and _is_working(cand, hol_all, sat):
                    bridges.append(cand.isoformat())
    res["bridge_days"] = sorted(set(bridges))
    e = easter(a.year)
    checks.append({"code": "easter_rule", "ok": e.weekday() == 6 and dt.date(a.year, 3, 22) <= e <= dt.date(a.year, 4, 25), "args": {"date": e.isoformat()}})
    warnings.append({"code": "wd_rules", "args": {}})
    return _answer(res, tr, checks, warnings)


TASKS = {"p_cf": task_cf, "p_piva": task_piva, "p_iban": task_iban, "p_workdays": task_workdays}
`,i=document.documentElement.lang===`it`?`it-IT`:`en-GB`,a=(e,t=2)=>typeof e==`number`&&Number.isFinite(e)?e.toLocaleString(i,{maximumFractionDigits:t,minimumFractionDigits:t}):String(e??`—`),o=e=>String(e??``).replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#39;`})[e]);async function s(e){let t=await crypto.subtle.digest(`SHA-256`,e);return Array.from(new Uint8Array(t)).map(e=>e.toString(16).padStart(2,`0`)).join(``)}var c=null;async function l(i,a){if(c)return c;let o=await t(a);return await e(o,i,a),o.globals.set(`_wp_src`,r),await o.runPythonAsync(`import sys, types
_m = types.ModuleType('ws_products')
exec(_wp_src, _m.__dict__)
sys.modules['ws_products'] = _m
del _m, _wp_src
`),o.globals.set(`_ws_src`,n),await o.runPythonAsync(`import sys, types
_m = types.ModuleType('ws_tasks')
exec(_ws_src, _m.__dict__)
sys.modules['ws_tasks'] = _m
del _m, _ws_src
`),c=o,o}function u(e){let t=JSON.parse(e.dataset.t||`{}`),n=JSON.parse(e.dataset.wheels||`[]`),r=Array.from(e.querySelectorAll(`.ws-task`)),c=Array.from(e.querySelectorAll(`.ws-pick`)),u=e.querySelector(`.ws-status`),d=(e,n={})=>e.replace(/\{(\w+)\}/g,(e,r)=>{let s=n[r];return r===`dimension`&&typeof s==`string`&&t[`dim_${s}`]?o(t[`dim_${s}`]):o(typeof s==`number`?Number.isInteger(s)?s.toLocaleString(i):r===`rel`||r===`deg`?s.toExponential(1):a(s,r===`mm`?4:2):s)}),f=(e,n)=>d(t[`${e}_${n.code}`]||`${n.code}`,n.args||{}),p=t=>{r.some(e=>e.id===`ws-${t}`)||(t=r[0].id.slice(3)),r.forEach(e=>e.hidden=e.id!==`ws-${t}`),c.forEach(e=>e.setAttribute(`aria-current`,String(e.dataset.task===t))),e.dataset.task=t};c.forEach(t=>t.addEventListener(`click`,()=>{p(t.dataset.task),history.replaceState(null,``,`#${t.dataset.task}`),e.querySelector(`#ws-${t.dataset.task} h2`)?.focus()})),p(location.hash.slice(1));let m=e=>new Promise((t,n)=>{let r=new FileReader;r.onerror=()=>n(Error(`read`)),r.onload=()=>{let e=new Uint8Array(r.result);try{t({text:new TextDecoder(`utf-8`,{fatal:!0}).decode(e),enc:`UTF-8`,bytes:e})}catch{try{t({text:new TextDecoder(`windows-1252`).decode(e),enc:`Windows-1252`,bytes:e})}catch{n(Error(`decode`))}}},r.readAsArrayBuffer(e)}),h=e=>e.arrayBuffer().then(e=>new Uint8Array(e)),g=async(e,n,r,a)=>{let c=await s(a.bytes),l=new Date,u=r,d=(e,t,n)=>`<section><h4><span>${e}</span>${o(t)}</h4>${n}</section>`,p=(e,t)=>e.length?`<ul>${e.join(``)}</ul>`:`<p class="small muted">${o(t)}</p>`;return{html:`<div class="ws-receipt" role="region" aria-label="${o(t.receipt)}">
      <header><b>${o(t.receipt)}</b><span class="mono small">${o(l.toLocaleString(i))}</span></header>
      ${d(1,t.r_tool,p((u.tools||[]).map(e=>`<li><span class="mono">${o(e.name)}</span> ${o(e.version)}</li>`),`—`))}
      ${d(2,t.r_input,p(a.summary.map(e=>`<li>${e}</li>`).concat(`<li>${o(t.r_fingerprint)} <span class="mono hash">${c}</span></li>`),`—`))}
      ${d(3,t.r_changes,p((u.transforms||[]).map(e=>`<li>${f(`tr`,e)}: <span class="mono">${o(e.before)}</span> → <span class="mono">${o(e.after)}</span></li>`),t.r_nochanges))}
      ${d(4,t.r_checks,p((u.checks||[]).map(e=>`<li class="${e.ok?`pass`:`fail`}"><b>${e.ok?`✓`:`✗`}</b> ${f(`ck`,e)}</li>`),`—`))}
      ${d(5,t.r_limits,p((u.warnings||[]).map(e=>`<li class="warn">! ${f(`wn`,e)}</li>`).concat(`<li>${o(t[`limits_${e}`])}</li>`),`—`))}
      <footer class="btn-row"><button type="button" class="btn small ws-dl-receipt">${o(t.dl_receipt)}</button><button type="button" class="btn small ws-print">${o(t.print)}</button></footer>
    </div>`,doc:{receipt:`S.T.A.R. Workspace verification receipt`,task:n,date:l.toISOString(),tools:u.tools,input:{summary:a.summary.map(e=>e.replace(/<[^>]+>/g,``)),sha256:c},transforms:u.transforms,checks:u.checks,warnings:u.warnings,limits:t[`limits_${e}`],result:Object.fromEntries(Object.entries(u.result||{}).filter(([e])=>![`cleaned_csv`,`points`,`path`].includes(e)))}}},_=(e,t,n)=>{let r=document.createElement(`a`);r.href=URL.createObjectURL(new Blob([t],{type:n})),r.download=e,document.body.appendChild(r),r.click(),r.remove(),setTimeout(()=>URL.revokeObjectURL(r.href),2e3)},v=async(r,i,a,s,c,d)=>{let p=r.querySelector(`.ws-out`),m=r.querySelector(`.ws-run`);m.disabled=!0,p.innerHTML=`<p class="ws-wait" role="status">${o(t.working)}</p>`;let h=e=>{u.textContent=e,p.querySelector(`.ws-wait`).textContent=e};try{let m=await l(n,h);u.textContent=t.ready,m.globals.set(`_p`,JSON.stringify(a)),m.globals.set(`_task`,i),m.globals.set(`_hasd`,s!==null),m.globals.set(`_d`,s??0);let v=await m.runPythonAsync(`import ws_tasks
ws_tasks.run(_task, _p, bytes(_d.to_py()) if _hasd else None)`),y=JSON.parse(v);if(e.dataset.last=v.length>2e5?v.slice(0,2e5):v,!y.ok){p.innerHTML=`<div class="ws-error" role="alert"><b>${o(t.cannot)}</b><p>${f(`er`,y.error)}</p></div>`;return}let x=b[i](y.result,r),C=await g(i,r.querySelector(`h2`).textContent||i,y,{summary:c,bytes:d});p.innerHTML=`<div class="ws-result">${x}</div>${C.html}`,p.querySelector(`.ws-dl-receipt`).addEventListener(`click`,()=>_(`star-receipt-${i}.json`,JSON.stringify(C.doc,null,1),`application/json`)),p.querySelector(`.ws-print`).addEventListener(`click`,()=>window.print()),p.querySelector(`.ws-dl-csv`)?.addEventListener(`click`,()=>_(`star-checked-${(y.result.column||`data`).replace(/[^\w.-]+/g,`_`)}.csv`,y.result.cleaned_csv,`text/csv`)),S[i]?.(y.result,p),p.querySelector(`.ws-result`)?.focus()}catch(n){let r=String(n.message||n);e.dataset.err=r.slice(-4e3);let i=r.trim().split(/\r?\n/).slice(-2).join(` `).slice(-300);p.innerHTML=`<div class="ws-error" role="alert"><b>${o(t.cannot)}</b><p>${o(t.engine_failed)} <span class="mono small">${o(i)}</span></p></div>`}finally{m.disabled=!1}},y=e=>`<dl class="ws-kv">${e.map(([e,t])=>`<div><dt>${o(e)}</dt><dd>${t}</dd></div>`).join(``)}</dl>`,b={distance:e=>`<p class="ws-big">${a(e.distance_km,3)} km</p><p class="small muted">${o(t.d_exact)}</p>`+y([[t.d_start,`${a(e.azimuth_start_deg,2)}°`],[t.d_end,`${a(e.azimuth_end_deg,2)}°`],[t.d_sphere,`${a(e.spherical_km,3)} km (${e.spherical_diff_percent>=0?`+`:``}${a(e.spherical_diff_percent,3)} %)`]])+`<p class="small">${d(t.d_sphere_note,{km:Math.abs(e.spherical_km-e.distance_km)})}</p><canvas class="ws-map" width="900" height="450" role="img" aria-label="${o(t.d_map)}"></canvas>`,coords:e=>y([[t.c_dec,`<span class="mono">${a(e.lat,8)}${i.startsWith(`it`)?`;`:`,`} ${a(e.lon,8)}</span>`],[t.c_dms,`<span class="mono">${o(e.lat_dms)}, ${o(e.lon_dms)}</span>`]].concat(e.utm_zone?[[t.c_utm,`<span class="mono">${o(e.utm_zone)}${o(e.utm_hemisphere)} · E ${a(e.utm_easting,3)} m · N ${a(e.utm_northing,3)} m</span>`]]:[])),column:e=>{let n=e.bad_rows,r=e.outliers;return`<p class="ws-big">${a(e.n,0)} ${o(t.s_values)} · ${o(t.s_median.toLowerCase())} ${a(e.median,4)} · ${o(t.s_mean)} ${a(e.mean,4)}</p>`+(e.outliers_total>0?`<p class="small warn-text">${d(t.s_head_note,{n:e.outliers_total})}</p>`:``)+`<p class="small muted">${d(t.s_read,{col:e.column,delim:e.delimiter===`	`?`TAB`:e.delimiter,dec:e.decimal_comma?t.s_comma:t.s_point})}</p>`+y([[t.s_mean,a(e.mean,6)],[t.s_sd,a(e.stdev,6)],[t.s_median,a(e.median,6)],[t.s_q,`${a(e.q1,6)} – ${a(e.q3,6)}`],[t.s_minmax,`${a(e.min,6)} – ${a(e.max,6)}`],[t.s_mad,a(e.mad,6)],[t.s_missing,a(e.missing,0)],[t.s_nonnum,a(e.non_numeric,0)]])+(n.length?`<h3>${o(t.s_bad_h)}</h3><table class="ws-table"><thead><tr><th>${o(t.s_row)}</th><th>${o(t.s_value)}</th><th>${o(t.s_why)}</th></tr></thead><tbody>${n.map(e=>`<tr><td>${e.row}</td><td class="mono">${o(e.value)||`∅`}</td><td>${o(t[`why_${e.why}`]||e.why)}</td></tr>`).join(``)}</tbody></table>${e.bad_total>n.length?`<p class="small">${d(t.s_more,{n:e.bad_total-n.length})}</p>`:``}`:``)+(r.length?`<h3>${o(t.s_out_h)}</h3><p class="small">${o(t.s_out_p)}</p><table class="ws-table"><thead><tr><th>${o(t.s_row)}</th><th>${o(t.s_value)}</th><th>${o(t.s_score)}</th></tr></thead><tbody>${r.map(e=>`<tr><td>${e.row}</td><td class="mono">${a(e.value,6)}</td><td>${a(e.score,1)}</td></tr>`).join(``)}</tbody></table>`:`<p>${o(t.s_no_out)}</p>`)+`<p><button type="button" class="btn small primary ws-dl-csv">${o(t.dl_csv)}</button></p><p class="small muted">${o(t.s_csv_note)}</p>`},linefit:e=>`<p class="ws-big mono">${o(e.y_name)} = ${a(e.slope,6)} × ${o(e.x_name)} ${e.intercept>=0?`+`:`−`} ${a(Math.abs(e.intercept),6)}</p>`+y([[t.l_slope,`${a(e.slope,6)} ± ${a(e.slope_err,6)}`],[t.l_icpt,`${a(e.intercept,6)} ± ${a(e.intercept_err,6)}`],[t.l_r2,e.r2==null?`—`:a(e.r2,6)],[t.l_sd,a(e.residual_sd,6)],[t.l_n,a(e.n,0)]])+`<p class="small">${o(t.l_note)}</p><canvas class="ws-plot" width="900" height="420" role="img" aria-label="${o(t.l_plot)}"></canvas>`,fingerprint:e=>(e.compared?`<p class="ws-big ${e.match?`ok`:`no`}">${e.match?`✓ `+o(t.fp_match):`✗ `+o(t.fp_nomatch)}</p><p class="small">${d(t.fp_compared,{kind:String(e.compared).toUpperCase()})}</p>`:``)+y([[`SHA-256`,`<span class="mono hash">${o(e.sha256)}</span>`],[`SHA-1`,`<span class="mono hash">${o(e.sha1)}</span>`],[`MD5`,`<span class="mono hash">${o(e.md5)}</span>`],[`CRC-32`,`<span class="mono">${o(e.crc32??`—`)}</span>`],[t.fp_size,`${a(e.bytes,0)} byte`]]),units:e=>`<p class="ws-big">${e.value.toLocaleString(i,{maximumSignificantDigits:12})} ${o(e.from)} = <b>${e.result.toLocaleString(i,{maximumSignificantDigits:12})}</b> ${o(e.to)}</p>`+y([[t.u_dim,o(t[`dim_${e.dimension}`]||e.dimension)],[t.u_factor,e.factor==null?o(t.u_affine):e.factor.toLocaleString(i,{maximumSignificantDigits:15})]])},x=new Image;x.src=`${document.documentElement.dataset.base||`/`}data/earth-2048.webp`;let S={distance:(e,t)=>{let n=t.querySelector(`.ws-map`),r=()=>{let t=n.getContext(`2d`),r=n.width,i=n.height;x.complete&&x.naturalWidth?t.drawImage(x,0,0,r,i):(t.fillStyle=`#0a1b2f`,t.fillRect(0,0,r,i));let a=e=>(e+180)/360*r,o=e=>(90-e)/180*i,s=e.path;t.strokeStyle=`#ffd27a`,t.lineWidth=3,t.beginPath(),s.forEach(([e,n],r)=>r&&Math.abs(n-s[r-1][1])>180?t.moveTo(a(n),o(e)):r?t.lineTo(a(n),o(e)):t.moveTo(a(n),o(e))),t.stroke();for(let[e,n]of[s[0],s[s.length-1]])t.fillStyle=`#fff`,t.beginPath(),t.arc(a(n),o(e),6,0,2*Math.PI),t.fill()};x.complete?r():x.onload=r},linefit:(e,t)=>{let n=t.querySelector(`.ws-plot`),r=n.getContext(`2d`),i=n.width,o=n.height,s=e.points,c=s.map(e=>e[0]),l=s.map(e=>e[1]),[u,d,f,p]=[Math.min(...c),Math.max(...c),Math.min(...l),Math.max(...l)],m=e=>48+(e-u)/(d-u||1)*(i-96),h=e=>o-48-(e-f)/(p-f||1)*(o-96);r.fillStyle=`#ffffff`,r.fillRect(0,0,i,o),r.strokeStyle=`#c9c5bb`,r.lineWidth=1,r.strokeRect(48,48,i-96,o-96),r.fillStyle=`#3a3f46`,r.font=`13px system-ui`,r.fillText(String(e.x_name),i/2,o-12),r.save(),r.translate(14,o/2),r.rotate(-Math.PI/2),r.fillText(String(e.y_name),0,0),r.restore(),r.fillText(a(u,3),48,o-48+18),r.fillText(a(d,3),i-48-40,o-48+18),r.fillText(a(p,3),4,52),r.fillText(a(f,3),4,o-48),r.fillStyle=`#1d4ed8`;for(let[e,t]of s)r.beginPath(),r.arc(m(e),h(t),3.5,0,2*Math.PI),r.fill();r.strokeStyle=`#b42318`,r.lineWidth=2,r.beginPath(),r.moveTo(m(u),h(e.slope*u+e.intercept)),r.lineTo(m(d),h(e.slope*d+e.intercept)),r.stroke()}},C=(e,t)=>e.querySelector(`[name="${t}"]`)?.value??``,w=e=>new TextEncoder().encode(e);r.forEach(n=>{let r=n.id.slice(3);n.querySelector(`.ws-example`)?.addEventListener(`click`,()=>{let e=JSON.parse(n.dataset.example||`{}`);for(let[t,r]of Object.entries(e)){let e=n.querySelector(`[name="${t}"]`);e&&(e.value=r)}n.querySelector(`input[type="file"]`)?.value&&(n.querySelector(`input[type="file"]`).value=``),n.dataset.exampleFile=e.__file?`1`:``}),n.querySelectorAll(`select.ws-city`).forEach(e=>e.addEventListener(`change`,()=>{if(!e.value)return;let[t,r]=e.value.split(`,`),i=e.dataset.for;n.querySelector(`[name="lat${i}"]`).value=t,n.querySelector(`[name="lon${i}"]`).value=r}));let i=n.querySelector(`[name="from"]`),s=n.querySelector(`[name="to"]`);if(i&&s){let e=()=>{let e=(i.selectedOptions[0]?.parentElement)?.dataset.dim;if(Array.from(s.querySelectorAll(`optgroup`)).forEach(t=>{t.hidden=t.dataset.dim!==e}),(s.selectedOptions[0]?.parentElement)?.dataset.dim!==e){let t=Array.from(s.querySelectorAll(`optgroup[data-dim="${e}"] option`)).find(e=>e.value!==i.value);t&&(s.value=t.value)}};i.addEventListener(`change`,e),e()}let c=()=>n.querySelectorAll(`select[name="column"], select[name="x"], select[name="y"]`).forEach(e=>{e.innerHTML=`<option value="">${o(t.auto)}</option>`});n.querySelector(`input[type="file"]`)?.addEventListener(`change`,c),n.querySelector(`textarea`)?.addEventListener(`input`,c),n.querySelector(`.ws-example`)?.addEventListener(`click`,c),n.querySelector(`.ws-clear`)?.addEventListener(`click`,c),n.querySelector(`.ws-clear`)?.addEventListener(`click`,()=>{n.querySelectorAll(`input:not([type=file]):not([type=button]), textarea`).forEach(e=>e.value=``),n.querySelectorAll(`input[type="file"]`).forEach(e=>e.value=``),n.querySelector(`.ws-out`).innerHTML=``,n.dataset.exampleFile=``}),n.querySelector(`form`).addEventListener(`submit`,async i=>{i.preventDefault();let s=n.querySelector(`.ws-out`);try{if(r===`distance`){let e={lat1:C(n,`lat1`),lon1:C(n,`lon1`),lat2:C(n,`lat2`),lon2:C(n,`lon2`)};await v(n,r,e,null,[`${o(t.d_from)} ${o(e.lat1)} · ${o(e.lon1)}`,`${o(t.d_to)} ${o(e.lat2)} · ${o(e.lon2)}`],w(JSON.stringify(e)))}else if(r===`coords`){let e={lat:C(n,`lat`),lon:C(n,`lon`)};await v(n,r,e,null,[`${o(e.lat)} · ${o(e.lon)}`],w(JSON.stringify(e)))}else if(r===`column`||r===`linefit`){let i=n.querySelector(`input[type="file"]`).files?.[0],c=C(n,`text`),l=t.pasted,u=null;if(i){if(i.size>5e6){s.innerHTML=`<div class="ws-error" role="alert">${o(d(t.er_file_too_big,{limit_mb:5}))}</div>`;return}let e=await m(i);c=e.text,u=e.bytes,l=`${o(i.name)} · ${a(i.size,0)} byte · ${o(d(t.enc_used,{enc:e.enc}))}`}let f={text:c};r===`column`?f.column=C(n,`column`):(f.x=C(n,`x`),f.y=C(n,`y`));let p=c?c.split(/\r?\n/).filter(e=>e.trim()).length:0;await v(n,r,f,null,[l,d(t.lines,{n:p})],u??w(c));let h=JSON.parse(e.dataset.last||`{}`).result;if(h?.columns)for(let e of r===`column`?[`column`]:[`x`,`y`]){let i=n.querySelector(`select[name="${e}"]`),a=i.value||(r===`column`?h.column:e===`x`?h.x_name:h.y_name);i.innerHTML=`<option value="">${o(t.auto)}</option>`+h.columns.map(e=>`<option${e===a?` selected`:``}>${o(e)}</option>`).join(``)}}else if(r===`fingerprint`){let e=n.querySelector(`input[type="file"]`).files?.[0],i,c;if(e){if(e.size>2e8){s.innerHTML=`<div class="ws-error" role="alert">${o(t.fp_too_big)}</div>`;return}i=await h(e),c=`${o(e.name)} · ${a(e.size,0)} byte`}else if(n.dataset.exampleFile)i=w(t.fp_example_text),c=t.fp_example_name;else{s.innerHTML=`<div class="ws-error" role="alert">${o(t.er_empty_file)}</div>`;return}await v(n,r,{expected:C(n,`expected`)},i,[c],i)}else if(r===`units`){let e={value:C(n,`value`),from:C(n,`from`),to:C(n,`to`)};await v(n,r,e,null,[`${o(e.value)} ${o(e.from)} → ${o(e.to)}`],w(JSON.stringify(e)))}}catch(e){s.innerHTML=`<div class="ws-error" role="alert"><b>${o(t.cannot)}</b><p>${o(String(e.message||e))}</p></div>`}})}),u.textContent=t.not_loaded}export{u as initWorkspace};