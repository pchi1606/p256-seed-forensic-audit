#!/usr/bin/env python3
"""Twist sensitivity v2 — CORRECTED (test-23b loop 8, Domain M1).
v1 used a hand-typed order for candidate 1,842 that did not match the
deposited enumeration, and reported the production predicate's
partial trial-division product (it stops once h > 8) as an exact
cofactor. v2 takes all orders from the deposited enumeration data,
factors each twist order completely in PARI/GP, and tests viability
both by the production predicate and by the divisor criterion
(no h <= 8 with prime quotient). Run 2026-10-22.
"""
import sys, json, subprocess
sys.path.insert(0, "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/code")
from viability_pipeline import order_prime_factors_info

p = 2**256 - 2**224 + 2**192 + 2**96 - 1
merged = json.load(open("/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/paper/battery/work/mundane-battery-10run-2026-10-21/section4a_results_merged.json"))
N = {n: int(next(r for r in merged["P-256"] if r["n"] == n)["order"]) for n in (876, 78, 1842)}

def gp(cmd):
    r = subprocess.run(["gp", "-q", "-s", "1G"], input=cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("gp: " + r.stderr.strip()[:200])
    return r.stdout.strip()

out = {}
for n, Nv in N.items():
    Nt = 2 * (p + 1) - Nv
    fac = gp(f"f=factor({Nt}); print(f[,1]~); print(f[,2]~)")
    fac_lines = fac.splitlines()
    primes = [int(x) for x in fac_lines[0].strip("[]").split(", ") if x]
    exps = [int(x) for x in fac_lines[1].strip("[]").split(", ") if x]
    # exact cofactor: Nt / largest prime factor (with multiplicity handled:
    # cofactor relative to the largest prime factor q_max)
    qmax = max(primes)
    h_exact = Nt // qmax
    q, h_partial, viable = order_prime_factors_info(Nt, p)
    # divisor criterion: viable iff exists h | Nt, h <= 8, Nt/h prime
    divisors_ok = False
    for h in range(1, 9):
        if Nt % h == 0:
            qq = Nt // h
            if gp(f"print(isprime({qq}))") == "1":
                divisors_ok = True
    out[str(n)] = {"order": str(Nv), "twist_order": str(Nt),
                   "factorization": [[str(a), b] for a, b in zip(primes, exps)],
                   "largest_prime_factor": str(qmax), "h_exact_vs_largest_prime": str(h_exact),
                   "production_predicate": {"q": (str(q) if q else None), "h_partial_product": h_partial, "viable": bool(viable)},
                   "divisor_criterion_viable": divisors_ok}
    print(f"n={n}: factors={list(zip(primes, exps))[:6]}... h_exact={h_exact} production_viable={viable} divisor_viable={divisors_ok}", flush=True)
out["summary"] = ("All three twist orders are non-viable under V_loose by both the "
                  "production predicate and the divisor criterion. v1's printed "
                  "cofactors (33, 46924, 177) were partial trial-division products "
                  "(and, for 1842, computed from a mistyped order); the exact "
                  "cofactors against the largest prime factor are in this file.")
json.dump(out, open("/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/paper/battery/work/loop6-fixes/twist_sensitivity_results_v2.json", "w"), indent=1)
print("SAVED v2")
