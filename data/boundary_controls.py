#!/usr/bin/env python3
"""Boundary controls for the viability predicate's exact decision edges
(test-23b loop 6, methods Major 5). Extends synthetic_controls.py
(loop 3) at the boundaries that suite did not test:
  - cofactor h = 9 (the first value the h <= 8 rule must reject):
    a curve of order 9q (q prime) must return viable=False from the
    PRODUCTION predicate order_prime_factors_info.
  - embedding degree k = 20 (the strict tier tests p^d != 1 mod q for
    1 <= d <= 20): a prime-order curve with ord_q(p) = 20 must return
    k_gt_20 = False; one with ord_q(p) = 21 must return True.
    k_gt_20 is verbatim from verify_independent.py (production check).
Ground truth: PARI/GP ellcard. Embedding-boundary cases are
constructed backward: choose primes p, q with q in p's Hasse interval
and ord_q(p) exactly 20 (resp. 21), then locate a curve over F_p with
#E = q by scanning b (a = p - 3, the pipeline's family).
"""
import json, sys
sys.path.insert(0, "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/code")
from viability_pipeline import order_prime_factors_info
sys.path.insert(0, "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/paper/battery/work/loop3-fixes")
from synthetic_controls import scan_orders, is_prime, classify, ord_mod, k_gt_20

results = {"design": "boundary controls: h=9 reject; embedding ord 20 reject / 21 pass; production predicate code; GP ellcard ground truth",
           "cases": {}}

# ---- h = 9 ----
orders = scan_orders(10007, 6000)
hit = None
for b in sorted(orders):
    h, rem = classify(orders[b])
    if h == 9 and is_prime(rem):
        hit = (b, orders[b], rem); break
b, N, q9 = hit
q, h, viable = order_prime_factors_info(N, 10007)
results["cases"]["h9_reject"] = {"field": 10007, "b": b, "order": N, "q": q9,
                                 "predicate_returns": {"q": q, "h": h, "viable": viable},
                                 "expected_viable": False, "pass": bool(viable is False and h == 9)}
print("h9:", results["cases"]["h9_reject"], flush=True)

# ---- embedding boundaries: backward construction ----
def primes_upto(n):
    s = bytearray(b"\x01") * (n + 1); s[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]: s[i*i:n+1:i] = b"\x00" * ((n - i*i) // i + 1)
    return [i for i in range(2, n + 1) if s[i]]

targets = {}
for p in primes_upto(300000):
    if p < 5000: continue
    import math
    smax = int(2 * math.isqrt(p))
    for s in range(2, smax + 1):
        q = p + 1 - s
        if not is_prime(q) or q == p: continue
        o = ord_mod(p % q, q)
        if o == 20 and "k20" not in targets: targets["k20"] = (p, q)
        if o == 21 and "k21" not in targets: targets["k21"] = (p, q)
    if len(targets) == 2: break
print("targets:", targets, flush=True)
assert len(targets) == 2

for name, expect in (("k20", False), ("k21", True)):
    p, q = targets[name]
    orders = scan_orders(p, 40000)
    bhit = next(b for b in sorted(orders) if orders[b] == q)
    r = k_gt_20(p, q)
    results["cases"][f"{name}_{'reject' if not expect else 'pass'}"] = {
        "field": p, "b": bhit, "order": q, "ord_q(p)": ord_mod(p % q, q),
        "k_gt_20_returns": r, "expected": expect, "pass": bool(r is expect)}
    print(name, results["cases"][f"{name}_{'reject' if not expect else 'pass'}"], flush=True)

results["all_pass"] = all(c["pass"] for c in results["cases"].values())
json.dump(results, open("/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/paper/battery/work/loop6-fixes/boundary_controls_results.json", "w"), indent=1)
print("ALL PASS" if results["all_pass"] else "FAILURE")
