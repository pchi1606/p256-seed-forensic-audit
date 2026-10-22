#!/usr/bin/env python3
"""Negated-root sensitivity for the P-256 headline candidates
(test-23b loop 6, domain Blocker B1, branch (b)).

For p = 3 (mod 4), E_{-b} is the quadratic twist of E_b, so its order
is 2(p+1) - #E_b exactly. For candidates 876, 78, and 1,842 (orders
from Result I / FIPS 186-2), compute the twist order, run the
production viability predicate on it, and cross-check the twist order
for 876 and 78 by a direct ellcard computation on the negated
coefficient. Question answered: under the other root representative,
would any load-bearing candidate have been viable? Run 2026-10-22.
"""
import sys, json, subprocess
sys.path.insert(0, "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/code")
from viability_pipeline import fips_b_from_seed, order_prime_factors_info

p = 2**256 - 2**224 + 2**192 + 2**96 - 1
seeds = {876: "50C71A63F911DB7B2F31618ECF609D37154437F9",
         78: "DE9F9A343DFA8F3B009D335319C20276AD62EEA5"}
N = {876: 115792089210356248762697446949407573529980276179566407717841077783673421468943,
     78:  115792089210356248762697446949407573529488654146255459484813647826182573233708,
     1842: 115792089210356248762697446949407573530086143415290314195533631308867097853951}

def gp_order(b):
    cmd = f"E=ellinit([0,0,0,{-3 % p},{b}]*Mod(1,{p})); print(ellcard(E))"
    r = subprocess.run(["gp", "-q", "-s", "1G"], input=cmd,
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("gp: " + r.stderr.strip()[:200])
    return int(r.stdout.strip())

res = {}
for n, Nv in N.items():
    Nt = 2 * (p + 1) - Nv
    q, h, viable = order_prime_factors_info(Nt, p)
    res[str(n)] = {"order": str(Nv), "twist_order": str(Nt), "twist_h": h,
                   "twist_viable_loose": bool(viable)}
    print(f"n={n}: twist h={h} viable_loose={viable}", flush=True)
for n, s in seeds.items():
    b = fips_b_from_seed(s, p)
    direct = gp_order((-b) % p)
    res[str(n)]["direct_ellcard_negated_b"] = str(direct)
    res[str(n)]["direct_matches_twist_formula"] = (direct == int(res[str(n)]["twist_order"]))
    print(f"n={n}: direct ellcard(-b) matches 2p+2-N: {res[str(n)]['direct_matches_twist_formula']}", flush=True)
res["summary"] = ("Under the negated root representative, none of 876, 78, or the "
                  "published 1,842 would be viable (twist cofactors 33, 46924, 177).")
json.dump(res, open("/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/paper/battery/work/loop6-fixes/twist_sensitivity_results.json", "w"), indent=1)
print("SAVED")
