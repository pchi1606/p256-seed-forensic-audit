# Reproduction package — "The Published P-256 Seed Was Not the First Viable Candidate"

One-command verification of the magazine note's headline numbers.

## Run

```bash
bash reproduce.sh
```

Requires only python3. `verify.py` recomputes the paper's key claims
from the frozen analysis data files in `data/`:

- P-256 candidate 876: prime order, 256-bit, h=1, q≠p (5/5 primality
  panel; ellcard/ellsea agreement)
- P-256 candidate 1,842 (published): prime order, byte-identical to the
  documented FIPS 186-2 q
- The refutation: 876 < 1,842, both viable
- Binary curves B-233/283/409/571: 4/4 recovered at halved-clock
  readings, halving relation verified

The full order computations (PARI/GP, ~10 s per candidate) live in the
analysis working directory; this package verifies their recorded outputs.

## Contents

- `verify.py` — headline verifier (27 checks)
- `data/` — frozen analysis outputs (addendum_batch1.json, addendum_fix5b.json)
- `magazine-note.pdf` — the manuscript
- `CITATION.md`, `LICENSE` (MIT)
