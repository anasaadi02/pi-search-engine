"""Search pi, written two ways.

  digits   pi.txt          base 10:  3.14159...       (Number and Date tabs)
  letters  pi_base26.txt   base 26:  D.DRSQLOL...     (Name tab, A=0 ... Z=25)

Convention: positions are 1-based. Position 1 is the first digit after the point.
Internally Python strings are 0-based, so position = index + 1.
"""
import unicodedata
from datetime import date

FILES = {"digits": "pi.txt", "letters": "pi_base26.txt"}
# mode -> (source, base, unit name, max query length)
MODES = {
  "digits": ("digits", 10, "digit", 30),
  "date": ("digits", 10, "digit", 30),
  "name": ("letters", 26, "letter", 20),
}
COUNT_LIMIT = 1000  # cap occurrence counting so searching "1" can't scan forever


def load_sources():
  return {k: open(p, encoding="ascii").read() for k, p in FILES.items()}


def find_all(data, pattern, limit=COUNT_LIMIT):
  positions = []
  i = data.find(pattern)
  while i != -1 and len(positions) < limit:
    positions.append(i + 1)
    i = data.find(pattern, i + 1)  # +1, not +len(pattern): matches may overlap
  return positions


def context(data, pos, length, radius=20):
  i = pos - 1
  # max(0, ...) matters: a negative slice start would wrap to the END of the data
  return data[max(0, i - radius):i], data[i:i + length], data[i + length:i + length + radius]


def encode_date(iso):
  """'2002-05-14' -> {format: digits}. date.fromisoformat rejects Feb 31 for us."""
  d = date.fromisoformat(iso)
  return {
    "DDMMYYYY": f"{d:%d%m%Y}",
    "MMDDYYYY": f"{d:%m%d%Y}",
    "YYYYMMDD": f"{d:%Y%m%d}",
    "DDMMYY": f"{d:%d%m%y}",
  }


def normalize_name(text):
  """'José-Luis' -> 'JOSELUIS'. NFKD splits 'é' into 'e' + accent; ascii-encoding drops the accent."""
  plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().upper()
  letters = "".join(c for c in plain if c not in " -'")
  if not letters or not all("A" <= c <= "Z" for c in letters):
    raise ValueError("Names may only contain the letters A-Z.")
  return letters


def search(sources, mode, query):
  """Single entry point for the API. Raises ValueError with a user-facing message."""
  if mode not in MODES:
    raise ValueError("Unknown search mode.")
  source, base, unit, max_len = MODES[mode]

  query = query.strip()
  if mode == "digits":
    if not (query.isascii() and query.isdigit()):  # isdigit() alone accepts "²"
      raise ValueError("Enter digits 0-9 only.")
    patterns = {"Digits": query}
  elif mode == "date":
    try:
      patterns = encode_date(query)
    except ValueError:
      raise ValueError("Enter a valid date.") from None
  else:
    patterns = {"Name": normalize_name(query)}

  data = sources[source]
  results = []
  for label, pattern in patterns.items():
    if len(pattern) > max_len:
      raise ValueError(f"Too long (max {max_len} {unit}s).")
    positions = find_all(data, pattern)
    result = {
      "label": label,
      "pattern": pattern,
      "length": len(pattern),
      "positions": positions[:10],
      "count": len(positions),
      "capped": len(positions) == COUNT_LIMIT,
      "expected": base ** len(pattern),  # a random k-symbol string shows up around base^k
    }
    if positions:
      result["context"] = context(data, positions[0], len(pattern))
    results.append(result)
  results.sort(key=lambda r: r["count"] == 0)  # hits first; sort is stable so format order is kept
  return {"total": len(data), "unit": unit, "source": source, "results": results}


if __name__ == "__main__":
  s = load_sources()
  # Counts depend on file size, so check against fixed prefixes.
  d = s["digits"][:1_000_000]
  assert find_all(d, "14159")[0] == 1
  assert find_all(d, "0")[0] == 32
  assert find_all(d, "999999")[0] == 762      # the "Feynman point"
  assert len(find_all(d, "999999")) == 2      # only correct if overlaps count
  assert find_all("1111", "11") == [1, 2, 3]
  assert len(find_all(d, "1", limit=5)) == 5
  assert context(d, 1, 5) == ("", "14159", "26535897932384626433")
  assert context("0123456789", 9, 2, radius=3) == ("567", "89", "")
  assert encode_date("2002-05-14") == {
    "DDMMYYYY": "14052002", "MMDDYYYY": "05142002", "YYYYMMDD": "20020514", "DDMMYY": "140502"}

  assert s["letters"].startswith("DRSQLOLYRTRO")  # pi in base 26 (verified independently)
  assert normalize_name("José-Luis") == "JOSELUIS"
  assert search(s, "name", "lol")["results"][0]["positions"][0] == 5

  for bad in [("digits", "12a"), ("digits", "²"), ("date", "2002-02-31"), ("name", "R2D2"),
              ("name", "x" * 21), ("x", "1")]:
    try:
      search(s, *bad)
      raise AssertionError(f"should have rejected {bad}")
    except ValueError:
      pass
  print("all checks passed")
