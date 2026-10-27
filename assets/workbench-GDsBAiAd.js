import{installWheels as e,loadPy as t}from"./runner-DYkmZtxU.js";var n=`"""Scientific Workbench of the Workspace (M11, 2026-10-21): five released S.T.A.R. packages behind simple forms.
Runs in the browser (Pyodide, after the package's wheel is installed) and in CPython for the tests
(tests/test_ws_bench.py compares every tool with an independent reference). Each function takes plain values and
returns a JSON-ready dict; a refused input returns {"error": the package's own message}.
"""
import math

MU, RE = 398600.4418, 6378.137


def tle(line1, line2):
    """Element set: the fields as parsed by star_tle (strict, checksums verified) plus period and altitudes."""
    import star_tle
    try:
        t = star_tle.parse(line1.rstrip(), line2.rstrip())
    except (star_tle.TleError, ValueError) as e:
        return {"error": str(e)}
    n = t["mean_motion_rev_day"] * 2 * math.pi / 86400.0                     # rad/s
    a = (MU / (n * n)) ** (1.0 / 3.0)
    e = t["eccentricity"]
    return {"satnum": t["satnum"], "classification": t["classification"], "intl_designator": t["intl_designator"],
            "epoch_utc": star_tle.epoch_utc(t).isoformat().replace("+00:00", "Z"), "inclination_deg": t["inclination_deg"],
            "raan_deg": t["raan_deg"], "eccentricity": e, "argp_deg": t["argp_deg"], "mean_anomaly_deg": t["mean_anomaly_deg"],
            "mean_motion_rev_day": t["mean_motion_rev_day"], "bstar": t["bstar"], "period_min": 1440.0 / t["mean_motion_rev_day"],
            "semi_major_axis_km": a, "perigee_km": a * (1 - e) - RE, "apogee_km": a * (1 + e) - RE}


def linsolve(rows, b):
    """A x = b by star_linsolve (exact rational elimination, then rounded): x, det and the float residual max|Ax - b|."""
    import star_linsolve
    try:
        x = star_linsolve.solve(rows, b)
        d = star_linsolve.det(rows)
    except (ValueError, ZeroDivisionError) as e:
        return {"error": str(e)}
    resid = max(abs(sum(r[j] * x[j] for j in range(len(x))) - b[i]) for i, r in enumerate(rows))
    return {"x": list(x), "det": d, "residual": resid, "n": len(rows)}


def atmosphere(z_km):
    """U.S. Standard Atmosphere 1976 below 86 km by star_atmosphere: temperature, pressure, density, speed of sound."""
    import star_atmosphere
    try:
        t, p, rho, a = star_atmosphere.ussa1976(z_km * 1000.0)
    except ValueError as e:
        return {"error": str(e)}
    return {"z_km": z_km, "temperature_k": t, "temperature_c": t - 273.15, "pressure_pa": p, "density_kg_m3": rho, "speed_of_sound_m_s": a}


def spacepacket(hex_text):
    """CCSDS 133.0-B-2 Space Packet by star_spacepacket: primary header fields and the data field."""
    import star_spacepacket
    try:
        raw = bytes.fromhex("".join(hex_text.split()))
        h, data = star_spacepacket.decode_packet(raw)
    except ValueError as e:
        return {"error": str(e)}
    return {"apid": h.apid, "packet_type": "telecommand" if h.packet_type == 1 else "telemetry", "secondary_header": h.secondary_header,
            "sequence_flags": h.sequence_flags, "sequence_count": h.sequence_count, "data_length_field": h.data_length,
            "data_octets": len(data), "data_hex": data.hex(" ")}


def coverage(altitude_km, min_elevation_deg):
    """What a satellite at this altitude sees above a minimum elevation, by star_coverage."""
    import star_coverage as c
    try:
        lam = c.central_angle_deg(altitude_km, min_elevation_deg)
        return {"nadir_angle_deg": c.nadir_angle_deg(altitude_km, min_elevation_deg), "slant_range_km": c.slant_range(altitude_km, min_elevation_deg),
                "central_angle_deg": lam, "footprint_radius_km": math.radians(lam) * c.EARTH_RADIUS_KM,
                "coverage_fraction": c.coverage_fraction(altitude_km, min_elevation_deg), "footprint_area_km2": c.footprint_area(altitude_km, min_elevation_deg)}
    except ValueError as e:
        return {"error": str(e)}
`,r=null;async function i(e){return r||(r=t(e).then(async e=>(e.globals.set(`_wb_src`,n),await e.runPythonAsync(`import sys, types
_m = types.ModuleType('ws_bench')
exec(_wb_src, _m.__dict__)
sys.modules['ws_bench'] = _m
del _m, _wb_src
`),e)),r.catch(()=>{r=null})),r}var a=e=>e.replace(/[&<>"]/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`})[e]);function o(t){let n=JSON.parse(t.dataset.t||`{}`),r=document.documentElement.lang===`it`?`it-IT`:`en-GB`,o=e=>Math.abs(e)>=1e6||Math.abs(e)<.001&&e!==0?e.toExponential(6):e.toLocaleString(r,{maximumFractionDigits:6}),s=e=>typeof e==`number`?o(e):Array.isArray(e)?e.map(e=>s(e)).join(`, `):String(e);t.querySelectorAll(`.wb-tool`).forEach(r=>{let o=r.dataset.tool,c=r.dataset.wheel,l=r.querySelector(`.wb-out`),u=Array.from(r.querySelectorAll(`input, textarea`)),d=e=>(r.querySelector(`#wb-${o}-${e}`)?.value||``).trim();r.querySelector(`.wb-ex`).addEventListener(`click`,()=>u.forEach(e=>{e.value=e.dataset.example||``})),r.querySelector(`.wb-run`).addEventListener(`click`,async()=>{l.className=`wb-out busy`,l.textContent=n.loading;try{let r=await i(e=>{l.textContent=e});await e(r,[c],e=>{l.textContent=e});let u=e=>Number(e.replace(`,`,`.`)),f=o===`tle`?{line1:d(`l1`),line2:d(`l2`)}:o===`lin`?{rows:d(`A`).split(`
`).filter(e=>e.trim()).map(e=>e.trim().split(/[\s;]+/).map(u)),b:d(`b`).split(/[\s;]+/).filter(Boolean).map(u)}:o===`atm`?{z_km:u(d(`z`))}:o===`pkt`?{hex_text:d(`hex`)}:{altitude_km:u(d(`h`)),min_elevation_deg:u(d(`e`))};r.globals.set(`_wb_args`,JSON.stringify(f));let p={tle:`tle`,lin:`linsolve`,atm:`atmosphere`,pkt:`spacepacket`,cov:`coverage`}[o],m=JSON.parse(String(await r.runPythonAsync(`import json, ws_bench\njson.dumps(ws_bench.${p}(**json.loads(_wb_args)))`)));if(t.dataset[`r${o}`]=JSON.stringify(m),m.error){l.className=`wb-out off`,l.innerHTML=`<b>${a(n.error)}:</b> ${a(m.error)}`;return}l.className=`wb-out ok`,l.innerHTML=`<table class="data kv"><tbody>${Object.entries(m).filter(([e])=>n.labels[e]).map(([e,t])=>`<tr><th scope="row">${a(n.labels[e])}</th><td class="mono">${a(s(t))}</td></tr>`).join(``)}</tbody></table>`}catch(e){l.className=`wb-out off`,l.textContent=String(e)}})}),t.dataset.ready=`1`}export{o as initWorkbench};