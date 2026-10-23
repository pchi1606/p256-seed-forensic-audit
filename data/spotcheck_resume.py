#!/usr/bin/env python3
"""Resume the enlarged spot check: skips (run,n) pairs already MATCHed in
the shard logs, appends each new result to spotcheck_resume_results.jsonl
immediately (crash-safe), same sample/design as spotcheck_enlarged.py."""
import json, random, sys, time
sys.path.insert(0, "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit/code")
import viability_pipeline as vp
from cypari2 import Pari

BASE = "/home/hatch/workspace/publication-gap-builds/crypto-constants-audit"
HERE = f"{BASE}/paper/battery/work/panel-fix-round"
MERGED = f"{BASE}/paper/battery/work/mundane-battery-10run-2026-10-21/section4a_results_merged.json"
half = int(sys.argv[1])  # 0 or 1: which half of the REMAINING list

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

def fips_b(seed_hex, p):
    import hashlib
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
    assert (pow(b, 2, p) * c) % p == p - 27
    return b

d = json.load(open(MERGED))
runs = list(vp.RUNS.keys())
pools = {run: [r for r in d[run] if r.get("viable") is False and str(r.get("order", "")).isdigit()] for run in runs}
total = sum(len(v) for v in pools.values())
rng = random.Random(20261023)
sample = []
for run in runs:
    k = max(12, round(300 * len(pools[run]) / total))
    for r in rng.sample(pools[run], min(k, len(pools[run]))):
        sample.append((run, r["n"], str(r["order"])))
done = set()
for line in open(f"{HERE}/done_pairs.txt"):
    a, b = line.split()
    done.add((a, int(b)))
try:
    for line in open(f"{HERE}/spotcheck_resume_results.jsonl"):
        rec = json.loads(line)
        done.add((rec["run"], rec["n"]))
except FileNotFoundError:
    pass
remaining = [s for s in sample if (s[0], s[1]) not in done]
mine = [s for i, s in enumerate(remaining) if i % 2 == half]
print(f"sample {len(sample)}, done {len(done)}, remaining {len(remaining)}, mine {len(mine)}", flush=True)
pari = Pari(); pari.allocatemem(1 << 30)
out = open(f"{HERE}/spotcheck_resume_results.jsonl", "a")
t0 = time.time()
for run, n, archived in mine:
    ts_str, pub_n, p = vp.RUNS[run]
    t = vp.unix(ts_str)
    seed = vp.candidate_seed(t, n)
    try:
        b = fips_b(seed, p)
        assert b is not None
    except Exception as e:
        out.write(json.dumps({"run": run, "n": n, "archived_ellcard": archived, "ellsea": "", "match": False, "error": "b-computation: " + repr(e)[:150]}) + "\n")
        out.flush()
        print(run, n, "B-ERROR", repr(e)[:80], flush=True)
        continue
    a = p - 3
    try:
        E = pari(f"ellinit([0,0,0,{a % p},{b % p}]*Mod(1,{p}))")
        got = str(pari.ellsea(E))
        ok = (got == archived); err = ""
    except Exception as e:
        got, ok, err = "", False, repr(e)[:200]
    out.write(json.dumps({"run": run, "n": n, "archived_ellcard": archived, "ellsea": got, "match": ok, "error": err}) + "\n")
    out.flush()
    print(run, n, "MATCH" if ok else "MISMATCH/ERR", f"{time.time()-t0:.0f}s", flush=True)
print("resume half done", flush=True)
