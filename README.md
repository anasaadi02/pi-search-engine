# Pi Search Engine

Find your birthday, your name, or any number in the first 100 million digits of π.

- **Number**: any digit sequence, e.g. `999999` (the Feynman point, position 762)
- **Date**: searched as DDMMYYYY, MMDDYYYY, YYYYMMDD and DDMMYY
- **Name**: searched in π written in **base 26**, where every position is a letter (A=0 … Z=25).
  π in base 26 starts `D.DRSQLOL…`

A digit viewer below the results lets you browse π and jumps to each match.

## Run it

```bash
pip install -r requirements.txt
python make_digits.py 10 100000000   # -> pi.txt         (~6 min)
python make_digits.py 26 100000000   # -> pi_base26.txt  (~10 min)
python server.py                     # -> http://127.0.0.1:8000
```

The data files are not in the repo (100 MB each). Use a smaller count like `1000000` for a quick try.

## How it works

| File | Role |
|---|---|
| `make_digits.py` | Computes π in any base with gmpy2 (GMP/MPFR): scale `frac(π)` by `base^n`, floor, convert. |
| `search.py` | Overlapping `str.find` search, date/name encoders, expected-position math (`base^length`). Run it to self-test. |
| `server.py` | Standard-library HTTP server: `/`, `/api/search`, `/api/digits`. |
| `index.html` | The whole UI: no framework, no build step. |

**Why names aren't always found:** a random k-symbol string first shows up around position `base^k`.
A 4-letter name in base 26 is expected near 457,000; a 6-letter one near 309 million.
(Nobody has proven every pattern appears in π: that's the open question of whether π is a *normal* number.)
