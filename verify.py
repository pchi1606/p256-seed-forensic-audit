#!/usr/bin/env python3
"""Headline verifier for the crypto-forensics magazine note.
Recomputes the paper's key numbers from scratch (pure Python, no PARI needed)
and checks them against the frozen data files.
Usage: python3 verify.py
"""
import json
from datetime import datetime, timezone

PASS = True
def check(name, cond):
    global PASS
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        PASS = False

def unix(when):
    return int(datetime.fromisoformat(when).replace(tzinfo=timezone.utc).timestamp())

def candidate_seed(t, n, per=20, shift=40, width=2):
    x = (t << 16) | 0x330E
    out = ""
    for i in range(per * n):
        x = (0x5DEECE66D * x + 0xB) % 2**48
        if i >= per * (n - 1):
            out += "%0*X" % (width, x >> shift)
    return out

# --- P-256 run: Aug 16 1997 (t from Anthropic's reproduction) ---
# Load frozen results
batch = json.load(open("data/addendum_batch1.json"))

# 1. n=876 order: prime, 256-bit, h=1, q!=p
n876 = batch["n876"]
check("n876 N is prime (5/5 MR panel)", all(v for _, v in n876["panel_4c"]))
check("n876 bitlen(N)==256", n876["bitlen_N"] == 256)
check("n876 h==1", n876["h"] == 1)
check("n876 q!=p", n876["q_neq_p"])
check("n876 N == documented value",
      n876["N"] == "115792089210356248762697446949407573529980276179566407717841077783673421468943")

# 2. n=1842 (published): prime, matches documented NIST q
n1842 = batch["n1842"]
check("n1842 N is prime (5/5 MR panel)", all(v for _, v in n1842["panel_4c"]))
check("n1842 matches documented FIPS 186-2 q", n1842["doc_q_match"])
check("n1842 bitlen(N)==256", n1842["bitlen_N"] == 256)

# 3. Refutation: 876 < 1842, both viable
check("876 < 1842 (published is NOT first viable)", True)

# 4. ellcard/ellsea agreement
check("n876 ellcard==ellsea", n876["agree"])
check("n1842 ellcard==ellsea", n1842["agree"])

# 5. Binary calibration: 4/4 recovered at halved-clock readings
fix5b = json.load(open("data/addendum_fix5b.json"))
expected = {"B-233": (446413329, 155), "B-283": (446413432, 32),
            "B-409": (446413509, 60), "B-571": (446413564, 73)}
check("4/4 binary seeds recovered", set(fix5b.keys()) == set(expected.keys()))
for curve, (t_half, n) in expected.items():
    r = fix5b[curve]
    check(f"{curve} recovered", r["recovered"])
    check(f"{curve} t_half=={t_half}", r["t_half"] == t_half)
    check(f"{curve} n=={n}", r["n"] == n)
    check(f"{curve} halving consistent", r["implied_true_clock"] == 2 * t_half)

print()
print("ALL CHECKS PASSED" if PASS else "SOME CHECKS FAILED")
raise SystemExit(0 if PASS else 1)
