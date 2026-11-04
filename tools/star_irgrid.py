"""star_irgrid: DC voltage drop (IR drop) of a small reference power-grid mesh, solved exactly and on a sparsified
network, with the error of the sparsified solution against the exact one. Standard library only.

A reference implementation, written to be read and checked; it is not a production sign-off tool and not a port of
any commercial or published engine. The browser version (site/src/irgrid.ts) performs the same operations in the
same order, so both give bit-identical voltages and the same SHA-256 fingerprints (tests/test_irgrid_parity.py).

The network (reference_grid):
  * nx x ny nodes (2 to 20 per side, at most 400 nodes); node k = j * nx + i.
  * a resistor between horizontal and vertical neighbours: conductance G0 * (0.5 + u) siemens, u uniform in [0, 1)
    from the mulberry32 generator (class Rng);
  * every node draws a load current I0 * (0.5 + u) amperes (same generator, after the edges);
  * five supply pads (the four corners and the centre) tie their node to VDD through G_PAD siemens.
  Only the resistive part is simulated: this is the DC operating point. Capacitances would not change it.

The solve: (L + diag(gpad)) v = gpad * VDD - iload, L the conductance Laplacian of the mesh. The matrix is symmetric
positive definite and banded (bandwidth nx); it is factorised by a banded Cholesky decomposition (direct, exact up to
rounding) and solved by forward and backward substitution.

The sparsifier (sparsify), stated so that it can be checked:
  1. the effective resistance R_e of every mesh edge is computed exactly, R_e = ||F^-1 (e_u - e_v)||^2 where F is the
     Cholesky factor of the grounded matrix (the supply is the ground node); leverage = g_e * R_e;
  2. a maximum-weight spanning tree (Kruskal, ties broken by edge index) is always kept at its own conductance, so the
     reduced network stays connected;
  3. every other edge is kept with probability p_e = min(1, rho * g_e * R_e) and, if kept, its conductance is divided
     by p_e (one draw of the same generator, seeded with `seed`, per off-tree edge, in edge order).
  Steps 1 and 3 are the effective-resistance sampling of Spielman and Srivastava (2008, "Graph sparsification by
  effective resistances"); step 2 is the spanning-tree backbone used by power-grid sparsifiers. The expected
  sparsified matrix equals the original one; the error bound of the paper is not claimed for this combination.
  On a mesh the network is already sparse: the point is to measure the price of each removed edge, not a speed-up.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
import time

VDD = 1.0          # volt
G_PAD = 100.0      # siemens, each supply pad
G0 = 2.0           # siemens: mesh conductances in [1, 3)
I0 = 1e-3          # ampere: loads in [0.5, 1.5) mA
NET_SEED = 1
MAX_SIDE = 20


M32 = 0xFFFFFFFF


class Rng:
    """mulberry32 (Tommy Ettinger, 2017): a 32-bit state stepped by 0x6D2B79F5 and hashed; every value is a
    32-bit pattern, so Python's masked arithmetic and JavaScript's Math.imul give the same sequence. Returns k / 2^32."""

    def __init__(self, seed: int):
        self.s = seed & M32

    def next(self) -> float:
        self.s = (self.s + 0x6D2B79F5) & M32
        t = self.s
        t = ((t ^ (t >> 15)) * (t | 1)) & M32
        t = (t ^ ((t + (((t ^ (t >> 7)) * (t | 61)) & M32)) & M32)) & M32
        return (t ^ (t >> 14)) / 4294967296


def _check_side(name, x):
    if isinstance(x, bool) or not isinstance(x, int) or not 2 <= x <= MAX_SIDE:
        raise ValueError(f"{name} must be an integer from 2 to {MAX_SIDE}")


def reference_grid(nx: int, ny: int, net_seed: int = NET_SEED) -> dict:
    _check_side("nx", nx)
    _check_side("ny", ny)
    n, rng = nx * ny, Rng(net_seed)
    edges = []
    for j in range(ny):
        for i in range(nx - 1):
            k = j * nx + i
            edges.append((k, k + 1, G0 * (0.5 + rng.next())))
    for j in range(ny - 1):
        for i in range(nx):
            k = j * nx + i
            edges.append((k, k + nx, G0 * (0.5 + rng.next())))
    iload = [I0 * (0.5 + rng.next()) for _ in range(n)]
    pads = sorted({0, nx - 1, n - nx, n - 1, (ny // 2) * nx + nx // 2})
    gpad = [0.0] * n
    for p in pads:
        gpad[p] = G_PAD
    return {"n": n, "nx": nx, "ny": ny, "edges": edges, "gpad": gpad, "iload": iload, "vdd": VDD, "pads": pads}


def network(n: int, edges, gpad, iload, vdd: float = VDD) -> dict:
    """A network given by hand: edges (u, v, g) with u != v, a pad conductance and a load current per node."""
    if len(gpad) != n or len(iload) != n:
        raise ValueError("gpad and iload need one value per node")
    out = []
    for u, v, g in edges:
        if u == v or not (0 <= u < n and 0 <= v < n) or not (g > 0 and math.isfinite(g)):
            raise ValueError(f"bad edge {(u, v, g)}")
        out.append((min(u, v), max(u, v), float(g)))
    return {"n": n, "edges": out, "gpad": [float(x) for x in gpad], "iload": [float(x) for x in iload], "vdd": float(vdd)}


def bandwidth(net) -> int:
    return max((v - u for u, v, _ in net["edges"]), default=0)


def assemble(net, edges=None) -> list:
    """Band storage: a[k][d] = M[k][k - d], d = 0..b. Diagonal starts at gpad, then each edge in order."""
    n, b = net["n"], bandwidth(net)
    a = [[0.0] * (b + 1) for _ in range(n)]
    for k in range(n):
        a[k][0] = net["gpad"][k]
    for u, v, g in (net["edges"] if edges is None else edges):
        a[u][0] += g
        a[v][0] += g
        a[v][v - u] -= g
    return a


def cholesky(a) -> list:
    n, b = len(a), len(a[0]) - 1
    f = [[0.0] * (b + 1) for _ in range(n)]
    for k in range(n):
        lo = max(0, k - b)
        for j in range(lo, k + 1):
            s = a[k][k - j]
            fk, fj = f[k], f[j]
            for m in range(lo, j):
                s -= fk[k - m] * fj[j - m]
            if j == k:
                if not s > 0:
                    raise ValueError("matrix not positive definite: a node is not connected to any supply pad")
                fk[0] = math.sqrt(s)
            else:
                fk[k - j] = s / fj[0]
    return f


def substitute(f, rhs) -> list:
    n, b = len(f), len(f[0]) - 1
    y = [0.0] * n
    for k in range(n):
        s = rhs[k]
        fk = f[k]
        for m in range(max(0, k - b), k):
            s -= fk[k - m] * y[m]
        y[k] = s / fk[0]
    x = [0.0] * n
    for k in range(n - 1, -1, -1):
        s = y[k]
        for m in range(k + 1, min(n, k + b + 1)):
            s -= f[m][m - k] * x[m]
        x[k] = s / f[k][0]
    return x


def rhs(net) -> list:
    return [net["gpad"][k] * net["vdd"] - net["iload"][k] for k in range(net["n"])]


def solve(net, edges=None) -> list:
    return substitute(cholesky(assemble(net, edges)), rhs(net))


def effective_resistances(net, f=None) -> list:
    """R_e = (e_u - e_v)^T M^-1 (e_u - e_v) = ||F^-1 (e_u - e_v)||^2, for every edge, from the factor F of M."""
    f = cholesky(assemble(net)) if f is None else f
    n, b = len(f), len(f[0]) - 1
    out = []
    y = [0.0] * n
    for u, v, _ in net["edges"]:
        r = 0.0
        for k in range(u, n):
            s = 1.0 if k == u else (-1.0 if k == v else 0.0)
            fk = f[k]
            for m in range(max(u, k - b), k):
                s -= fk[k - m] * y[m]
            y[k] = s / fk[0]
            r += y[k] * y[k]
        out.append(r)
    return out


def spanning_tree(net) -> list:
    """Indices of a maximum-weight spanning forest (Kruskal; heavier first, ties by edge index)."""
    parent = list(range(net["n"]))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    keep = []
    for i in sorted(range(len(net["edges"])), key=lambda i: (-net["edges"][i][2], i)):
        u, v, _ = net["edges"][i]
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            keep.append(i)
    return sorted(keep)


def sparsify(net, rho: float, seed: int, reff=None) -> dict:
    if isinstance(rho, bool) or not isinstance(rho, (int, float)) or not (0 <= rho <= 8):
        raise ValueError("rho must be a number from 0 to 8")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2 ** 32:
        raise ValueError("seed must be an integer from 0 to 2^32 - 1")
    reff = effective_resistances(net) if reff is None else reff
    tree = set(spanning_tree(net))
    rng = Rng(seed)
    kept = []
    for i, (u, v, g) in enumerate(net["edges"]):
        if i in tree:
            kept.append((u, v, g))
            continue
        p = min(1.0, rho * g * reff[i])
        if rng.next() < p:
            kept.append((u, v, g / p))
    return {"edges": kept, "tree": len(tree), "offtree_kept": len(kept) - len(tree)}


def _f64(xs) -> bytes:
    return struct.pack(f"<{len(xs)}d", *xs)


def network_bytes(net, edges=None) -> bytes:
    """Fingerprinted form of a network: per edge int32 u, int32 v, float64 g (little-endian), then the n pad
    conductances, the n load currents and VDD as float64."""
    es = net["edges"] if edges is None else edges
    return b"".join(struct.pack("<iid", u, v, g) for u, v, g in es) + _f64(net["gpad"]) + _f64(net["iload"]) + _f64([net["vdd"]])


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rel_l2(a, b) -> float:
    num = 0.0
    den = 0.0
    for x, y in zip(a, b):
        num += (x - y) * (x - y)
        den += y * y
    return math.sqrt(num) / math.sqrt(den)


def run(nx: int = 16, ny: int = 16, rho: float = 1.0, seed: int = 7) -> dict:
    """The whole task: build, solve exactly, sparsify, solve again, compare. Times are of this Python process."""
    net = reference_grid(nx, ny)
    n, e0 = net["n"], len(net["edges"])
    t0 = time.perf_counter()
    f = cholesky(assemble(net))
    v = substitute(f, rhs(net))
    t1 = time.perf_counter()
    reff = effective_resistances(net, f)
    sp = sparsify(net, rho, seed, reff)
    t2 = time.perf_counter()
    vs = solve(net, sp["edges"])
    t3 = time.perf_counter()
    drop, drops = [net["vdd"] - x for x in v], [net["vdd"] - x for x in vs]
    lev_sum = 0.0                       # a plain running sum, as in JS (sum() of floats is compensated since Python 3.12)
    for (_, _, g), r in zip(net["edges"], reff):
        lev_sum += g * r
    e1 = len(sp["edges"])
    return {
        "task": "star_irgrid: DC IR drop of a reference power-grid mesh, exact and sparsified",
        "method": {"solver": "banded Cholesky (direct)", "sparsifier": "effective-resistance sampling (Spielman-Srivastava 2008) "
                   "with a maximum-weight spanning tree always kept; p_e = min(1, rho * g_e * R_e), kept edges reweighted by 1/p_e",
                   "generator": "mulberry32"},
        "inputs": {"nx": nx, "ny": ny, "rho": rho, "seed": seed, "net_seed": NET_SEED, "vdd_V": VDD, "g_pad_S": G_PAD,
                   "pads": net["pads"]},
        "before": {"nodes": n, "edges": e0, "nonzeros": n + 2 * e0},
        "after": {"nodes": n, "edges": e1, "nonzeros": n + 2 * e1, "tree_edges": sp["tree"], "offtree_kept": sp["offtree_kept"],
                  "offtree_total": e0 - sp["tree"]},
        "leverage_sum_mesh": lev_sum,
        "worst_drop_mV": {"exact": 1e3 * max(drop), "sparsified": 1e3 * max(drops)},
        "rel_l2_error": {"voltage": rel_l2(vs, v), "drop": rel_l2(drops, drop)},
        "sha256": {"input_network": sha256(network_bytes(net)), "sparsified_network": sha256(network_bytes(net, sp["edges"])),
                   "v_exact": sha256(_f64(v)), "v_sparsified": sha256(_f64(vs))},
        "times_ms": {"exact_solve": 1e3 * (t1 - t0), "resistances_and_sampling": 1e3 * (t2 - t1), "sparsified_solve": 1e3 * (t3 - t2),
                     "measured_in": "python " + sys.version.split()[0]},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DC IR drop of a reference power-grid mesh, exact and sparsified")
    ap.add_argument("--nx", type=int, default=16)
    ap.add_argument("--ny", type=int, default=16)
    ap.add_argument("--rho", type=float, default=1.0, help="oversampling factor, 0 (tree only) to 8")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--json", metavar="FILE", help="write the full report as JSON")
    a = ap.parse_args(argv)
    try:
        r = run(a.nx, a.ny, int(a.rho) if a.rho == int(a.rho) else a.rho, a.seed)
    except ValueError as exc:
        print(f"star_irgrid: {exc}", file=sys.stderr)
        return 2
    b, s, er = r["before"], r["after"], r["rel_l2_error"]
    print(f"nodes {b['nodes']}; edges {b['edges']} -> {s['edges']} (tree {s['tree_edges']} + {s['offtree_kept']} of "
          f"{s['offtree_total']} off-tree); nonzeros {b['nonzeros']} -> {s['nonzeros']}")
    print(f"worst drop {r['worst_drop_mV']['exact']:.4f} mV exact, {r['worst_drop_mV']['sparsified']:.4f} mV sparsified")
    print(f"relative L2 error: voltages {er['voltage']:.3e}, drops {er['drop']:.3e}")
    print(f"sha256 v_exact {r['sha256']['v_exact']}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(r, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
