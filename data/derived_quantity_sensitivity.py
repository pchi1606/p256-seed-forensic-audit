#!/usr/bin/env python3
"""Revision-added sensitivity (2026-10-22, panel-fix round; NOT preregistered):
derived-quantity selection rules over the stored section-4a enumeration.
Rules over each run's V_loose viable set: smallest/largest curve order N,
smallest/largest coefficient b (anchored representative; P-224 negated per
Result II), and pick-2nd / pick-3rd viable in run order. A rule 'matches' a
run if its pick equals the published candidate index."""
import hashlib, json, sys
BASE = "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit"
sys.path.insert(0, f"{BASE}/code")
from viability_pipeline import unix, candidate_seed, RUNS  # noqa: E402

RESULTS = json.load(open(f"{BASE}/paper/battery/work/mundane-battery-10run-2026-10-21/section4a_results_merged.json"))

def tonelli(b2, p):
    if pow(b2, (p - 1) // 2, p) != 1: return None
    if p % 4 == 3: return pow(b2, (p + 1) // 4, p)
    q, s = p - 1, 0
    while q % 2 == 0: q //= 2; s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1: z += 1
    m, c = s, pow(z, q, p)
    t, r = pow(b2, q, p), pow(b2, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 1, (t * t) % p
        while t2 != 1: t2 = (t2 * t2) % p; i += 1
        bb = pow(c, 1 << (m - i - 1), p)
        m, c, t, r = i, (bb * bb) % p, (t * bb * bb) % p, (r * bb) % p
    return r

def fips_b(seed_hex, p, negate=False):
    s = bytes.fromhex(seed_hex); l = p.bit_length()
    v = (l - 1) // 160; w = l - 160 * v - 1
    h = int.from_bytes(hashlib.sha1(s).digest(), "big")
    c = h & ((1 << w) - 1)
    z = int(seed_hex, 16)
    for i in range(1, v + 1):
        si = ((z + i) % 2**160).to_bytes(20, "big")
        c = (c << 160) | int.from_bytes(hashlib.sha1(si).digest(), "big")
    b2 = (-27 * pow(c, -1, p)) % p
    b = tonelli(b2, p)
    if b is None: return None
    if negate: b = p - b
    assert (pow(b, 2, p) * c) % p == p - 27
    return b

RULES = ["smallest_N", "largest_N", "smallest_b", "largest_b", "second_viable", "third_viable"]
out = {"rules": {r: {"matches": 0, "picks": {}} for r in RULES}, "viable_counts": {}}
for run, (when, n_pub, p) in RUNS.items():
    rows = RESULTS[run]
    viable = sorted([r for r in rows if r["viable"] is True], key=lambda r: r["n"])
    out["viable_counts"][run] = len(viable)
    t = unix(when)
    items = []
    for r in viable:
        seed = candidate_seed(t, r["n"])
        b = fips_b(seed, p, negate=(run == "P-224"))
        assert b is not None
        items.append({"n": r["n"], "N": int(r["order"]), "b": b})
    picks = {
        "smallest_N": min(items, key=lambda x: x["N"])["n"],
        "largest_N": max(items, key=lambda x: x["N"])["n"],
        "smallest_b": min(items, key=lambda x: x["b"])["n"],
        "largest_b": max(items, key=lambda x: x["b"])["n"],
        "second_viable": items[1]["n"] if len(items) > 1 else None,
        "third_viable": items[2]["n"] if len(items) > 2 else None,
    }
    for rule, pick in picks.items():
        out["rules"][rule]["picks"][run] = pick
        if pick == n_pub: out["rules"][rule]["matches"] += 1
json.dump(out, open(f"{BASE}/paper/battery/work/panel-fix-round/derived_quantity_results.json", "w"), indent=1)
for rule in RULES:
    print(rule, "matches:", out["rules"][rule]["matches"], "/10", out["rules"][rule]["picks"])
print("viable counts:", out["viable_counts"])
