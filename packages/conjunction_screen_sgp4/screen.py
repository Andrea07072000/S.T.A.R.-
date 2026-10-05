# -*- coding: utf-8 -*-
"""Screening di congiunzioni su TLE reali con SGP4 (CPU). Task T9 del ledger S.T.A.R. R&D, scritto da Claude Code.

Metodo (dichiarato, cosi' si puo' criticare):
  1. TLE -> Satrec (sgp4 2.x, implementazione di Vallado): i TLE sono elementi MEDI SGP4, quindi si propagano con
     SGP4 e con nient'altro (un integratore Cowell inizializzato da un TLE sbaglia di km gia' all'epoca).
  2. Griglia grossolana: posizioni TEME ogni `step` secondi per `hours` ore; a ogni istante cKDTree.query_pairs con
     raggio `coarse_km`. Il raggio copre il moto relativo nel passo: due oggetti a velocita' relativa v_rel possono
     avvicinarsi di v_rel*step/2 tra due campioni, per questo coarse_km >> soglia finale.
  3. Rifinitura: per ogni coppia candidata, propagazione a 1 s nella finestra +-step attorno al campione piu' vicino;
     minimo della distanza = TCA (time of closest approach) e miss distance.
  4. Esclusione delle coppie "sempre vicine" (stessa piattaforma/stesso treno Starlink appena lanciato): se la distanza
     resta < coarse_km per oltre il 50 % dei campioni non e' un incontro, e' formazione. Sono contate a parte.

Limiti (NON nascosti): SGP4 su TLE ha errori di ~1 km all'epoca che crescono di km/giorno; una miss distance sotto
~1 km e' sotto la risoluzione del dato. Questo e' uno SCREENING (chi guardare), non una probabilita' di collisione.
L'oracolo esterno per la validazione e' CelesTrak SOCRATES sugli stessi giorni: confronto da fare (task per Antigravity).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from sgp4 import __version__ as SGP4_VERSION
from sgp4.api import SatrecArray, Satrec, jday


def _tle_checksum(line):
    return sum(int(c) if c.isdigit() else (1 if c == "-" else 0) for c in line[:68]) % 10


def tle_problem(l1, l2):
    """None if the pair is a well-formed TLE, else the reason. Added 2026-10-05: the star_audit tle_audit showed that
    Satrec.twoline2rv accepts malformed TLEs by design (checksum, line number, satnum mismatch, truncation), so this
    screening ingested them silently; they are now rejected and COUNTED in the report."""
    if len(l1) != 69 or len(l2) != 69:
        return "length"
    if l1[2:7] != l2[2:7]:
        return "satnum_mismatch"
    if not (l1[68].isdigit() and l2[68].isdigit()) or _tle_checksum(l1) != int(l1[68]) or _tle_checksum(l2) != int(l2[68]):
        return "checksum"
    return None


def load_tles(paths):
    sats, names, ids, seen, prov, groups = [], [], [], set(), [], []
    for g, p in enumerate(paths):
        raw = Path(p).read_bytes()
        prov.append({"file": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "rejected": {}})
        lines = [ln.rstrip() for ln in raw.decode("utf-8", "replace").splitlines() if ln.strip()]
        i = 0
        while i < len(lines) - 1:
            if lines[i].startswith("1 ") and lines[i + 1].startswith("2 "):
                name, l1, l2, i = "", lines[i], lines[i + 1], i + 2
            elif i + 2 < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
                name, l1, l2, i = lines[i].strip(), lines[i + 1], lines[i + 2], i + 3
            else:
                i += 1
                continue
            why = tle_problem(l1, l2)
            if why:
                prov[-1]["rejected"][why] = prov[-1]["rejected"].get(why, 0) + 1
                continue
            norad = l1[2:7].strip()
            if norad in seen:
                continue                       # dedup per numero NORAD: lo stesso oggetto in due file conta una volta
            seen.add(norad)
            sats.append(Satrec.twoline2rv(l1, l2))
            names.append(name or norad)
            groups.append(g)
            ids.append(norad)
    return sats, names, ids, prov, groups


def positions(arr, jd, fr):
    e, r, _ = arr.sgp4(jd, fr)                 # r: (n_sat, n_t, 3) km TEME
    return e, r


def refine_tca(state_at, step: float, iterations: int = 3):
    """Closed-form TCA refinement (STAR-EXP-003), shared by the screening and its tests. state_at(t) returns
    (r1, v1, r2, v2) at offset t seconds from the coarse sample (or None if propagation failed). Re-linearises the
    relative motion: t* = t - dr.dv/|dv|^2, clipped to +-step. Returns (t*, miss distance) or None."""
    tsec = 0.0
    for _ in range(iterations):
        s = state_at(tsec)
        if s is None:
            return None
        dr, dv = np.subtract(s[0], s[2]), np.subtract(s[1], s[3])
        vv = float(dv @ dv)
        dt = -float(dr @ dv) / vv if vv > 0 else 0.0
        tsec = float(np.clip(tsec + dt, -step, step))
        if abs(dt) < 1e-4:
            break
    s = state_at(tsec)
    if s is None:
        return None
    return tsec, float(np.linalg.norm(np.subtract(s[0], s[2])))


def screen(paths, start: datetime, hours: float, step: float, coarse_km, final_km: float, cross_only: bool = False,
           refine: str = "linear"):
    if coarse_km is None:
        # raggio minimo che non perde incontri: soglia + meta' dello spostamento relativo massimo in un passo (LEO <= 15,5 km/s)
        coarse_km = final_km + 15.5 * step / 2 + 1.0
    t0 = time.perf_counter()
    sats, names, ids, prov, groups = load_tles(paths)
    if not sats:
        raise ValueError(f"no valid TLE in {list(paths)}: nothing to screen")
    grp = np.array(groups)
    arr = SatrecArray(sats)
    n = len(sats)
    epochs = np.array([s.jdsatepoch + s.jdsatepochF for s in sats])
    jd0, fr0 = jday(start.year, start.month, start.day, start.hour, start.minute, start.second)
    nt = int(hours * 3600 / step) + 1
    fr = fr0 + np.arange(nt) * step / 86400.0
    jd = np.full(nt, jd0)
    t_load = time.perf_counter() - t0

    # Per coppia: incontri distinti. Un incontro = campioni consecutivi entro coarse_km; se ne rifinisce il minimo.
    # Prima versione: un solo minimo per coppia -> su 6 h due oggetti si incontrano piu' volte (una per orbita) e il
    # minimo grossolano cadeva sull'incontro sbagliato (diff fino a 3,3 km tra passo 10 s e 2 s).
    cur = {}                                   # (i,j) -> [ultimo k, d minima, k del minimo]
    encounters = []                            # (i, j, k del minimo)
    close_count = {}
    err_any = np.zeros(n, dtype=bool)
    chunk = 60
    for c in range(0, nt, chunk):
        e, r = positions(arr, jd[c:c + chunk], fr[c:c + chunk])
        err_any |= (e != 0).any(axis=1)
        for k in range(r.shape[1]):
            ok = ~(e[:, k] != 0)
            idx = np.nonzero(ok)[0]
            tree = cKDTree(r[idx, k])
            pairs = tree.query_pairs(coarse_km, output_type="ndarray")
            if not len(pairs):
                continue
            a, b = idx[pairs[:, 0]], idx[pairs[:, 1]]
            if cross_only:
                keep = grp[a] != grp[b]
                a, b = a[keep], b[keep]
                if not len(a):
                    continue
            d = np.linalg.norm(r[a, k] - r[b, k], axis=1)
            for ai, bi, di in zip(a.tolist(), b.tolist(), d.tolist()):
                key = (ai, bi) if ai < bi else (bi, ai)
                close_count[key] = close_count.get(key, 0) + 1
                kk = c + k
                st = cur.get(key)
                if st is None or kk > st[0] + 1:
                    if st is not None:
                        encounters.append((key[0], key[1], st[2]))
                    cur[key] = [kk, di, kk]
                else:
                    st[0] = kk
                    if di < st[1]:
                        st[1], st[2] = di, kk
    t_coarse = time.perf_counter() - t0 - t_load

    encounters.extend((key[0], key[1], st[2]) for key, st in cur.items())
    formation = {k for k, v in close_count.items() if v > 0.5 * nt}
    events = []
    dropped = 0  # candidate pairs lost because SGP4 failed during refinement: counted, never silent
    for i, j, k in encounters:
        if (i, j) in formation:
            continue
        if refine == "linear":
            # STAR-EXP-003: TCA in forma chiusa. Al campione k il moto relativo su +-step e' lineare entro pochi metri
            # (accelerazione relativa ~ m/s^2), quindi t* = -dr.dv/|dv|^2; due iterazioni di Newton (ri-linearizzando
            # in t*) bastano. 2-4 valutazioni SGP4 per incontro invece di ~2.000 della griglia: misurato in EXPERIMENTS.
            def _state(ts, i=i, j=j, k=k):
                f_now = fr[k] + ts / 86400.0
                ei, ri, vi = sats[i].sgp4(jd0, f_now)
                ej, rj, vj = sats[j].sgp4(jd0, f_now)
                return None if (ei or ej) else (ri, vi, rj, vj)
            res = refine_tca(_state, step)
            if res is None:
                dropped += 1
                continue
            tsec, miss = res
            if miss <= final_km:
                tca = start.timestamp() + (k * step) + tsec
                age = (jd0 + fr[k] - min(epochs[i], epochs[j]))
                events.append({"a": ids[i], "a_name": names[i], "b": ids[j], "b_name": names[j],
                               "tca_utc": datetime.fromtimestamp(tca, timezone.utc).isoformat(timespec="milliseconds"),
                               "miss_km": round(miss, 3), "older_tle_age_days": round(float(age), 2)})
            continue
        w = np.arange(-step, step + 1, 1.0)
        frw = fr[k] + w / 86400.0
        jdw = np.full(len(w), jd0)
        ei, ri, _ = sats[i].sgp4_array(jdw, frw)
        ej, rj, _ = sats[j].sgp4_array(jdw, frw)
        good = (ei == 0) & (ej == 0)
        if not good.any():
            dropped += 1
            continue
        dd = np.linalg.norm(ri - rj, axis=1)
        dd[~good] = np.inf
        m = int(np.argmin(dd))
        # Secondo passo a 1 ms attorno al minimo: a 15 km/s di velocita' relativa 1 s sono 15 km, e la verifica di
        # convergenza (passo 10 s vs 2 s) perdeva 9 eventi su 107 per questo, non per il passo grossolano.
        w2 = w[m] + np.arange(-1.0, 1.0005, 0.001)
        f2 = fr[k] + w2 / 86400.0
        e2i, r2i, _ = sats[i].sgp4_array(np.full(len(w2), jd0), f2)
        e2j, r2j, _ = sats[j].sgp4_array(np.full(len(w2), jd0), f2)
        d2 = np.linalg.norm(r2i - r2j, axis=1)
        d2[(e2i != 0) | (e2j != 0)] = np.inf
        m2 = int(np.argmin(d2))
        if d2[m2] < dd[m]:
            w, dd, m = w2, d2, m2
        if dd[m] <= final_km:
            tca = start.timestamp() + (k * step) + w[m]
            age = (jd0 + fr[k] - min(epochs[i], epochs[j]))
            events.append({"a": ids[i], "a_name": names[i], "b": ids[j], "b_name": names[j],
                           "tca_utc": datetime.fromtimestamp(tca, timezone.utc).isoformat(timespec="seconds"),
                           "miss_km": round(float(dd[m]), 3), "older_tle_age_days": round(float(age), 2)})
    events.sort(key=lambda x: x["miss_km"])
    t_total = time.perf_counter() - t0
    return {
        "experiment": "EXP-C01 SGP4 conjunction screening (CPU)",
        "author": "Claude Code (S.T.A.R. R&D regia)",
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "inputs": prov,
        "config": {"start_utc": start.isoformat(), "hours": hours, "step_s": step, "coarse_km": coarse_km,
                   "final_km": final_km, "cross_only": cross_only, "refine": refine},
        "environment": {"python": sys.version.split()[0], "sgp4": SGP4_VERSION, "numpy": np.__version__,
                        "platform": platform.platform(), "cpu": platform.processor()},
        "objects": n,
        "tles_rejected_malformed": sum(sum(p["rejected"].values()) for p in prov),
        "objects_with_sgp4_error": int(err_any.sum()),
        "candidates_dropped_sgp4_error": dropped,
        "tle_epoch_range_utc": [datetime.fromtimestamp((float(epochs.min()) - 2440587.5) * 86400, timezone.utc)
                                .isoformat(timespec="seconds"),
                                datetime.fromtimestamp((float(epochs.max()) - 2440587.5) * 86400, timezone.utc)
                                .isoformat(timespec="seconds")],
        "coarse_candidate_pairs": len(close_count),
        "coarse_encounters": len(encounters),
        "formation_pairs_excluded": len(formation),
        "events_below_final_km": len(events),
        "runtime_s": {"load": round(t_load, 2), "coarse": round(t_coarse, 2), "total": round(t_total, 2)},
        "events": events,                      # dump COMPLETO (Bionic T10b: con il solo top-200 il richiamo non si calcola)
        "limits": "SGP4/TLE ~1 km all'epoca, cresce con l'eta' del TLE; screening, non probabilita' di collisione; "
                  "validazione esterna (SOCRATES) NON ancora fatta.",
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("tle", nargs="+")
    ap.add_argument("--start", required=True, help="UTC ISO, es. 2026-10-02T00:00:00")
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--step", type=float, default=60)
    ap.add_argument("--coarse-km", type=float, default=None, help="default: soglia + 15,5 km/s * step/2 + 1")
    ap.add_argument("--refine", choices=["linear", "grid"], default="linear", help="linear = TCA in forma chiusa (veloce); grid = metodo originale")
    ap.add_argument("--cross-only", action="store_true", help="solo coppie tra file (popolazioni) diversi")
    ap.add_argument("--final-km", type=float, default=5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    start = datetime.fromisoformat(a.start).replace(tzinfo=timezone.utc)
    res = screen(a.tle, start, a.hours, a.step, a.coarse_km, a.final_km, a.cross_only, a.refine)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("events", "inputs")}, indent=1, ensure_ascii=False))
    print("prime 5:", json.dumps(res["events"][:5], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
