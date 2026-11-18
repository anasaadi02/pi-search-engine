"""Write pi's fractional digits in a given base.

  python make_digits.py 10  100000000   -> pi.txt         (0-9)
  python make_digits.py 26  100000000   -> pi_base26.txt  (A=0 ... Z=25)
"""
import math
import sys

import gmpy2  # GMP/MPFR in C: ~100x faster than pure-Python mpmath

GUARD = 10  # extra digits so rounding in the last place can't touch the ones we keep
OUTPUT = {10: "pi.txt", 26: "pi_base26.txt"}
B26 = str.maketrans("0123456789abcdefghijklmnop", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def frac_digits(base, n):
  """The first n base-`base` digits after the point, as one big integer.

  Shifting the point: frac(pi) * base**n moves n digits in front of the point,
  exactly like 0.14159 * 10**3 = 141.59 -> floor -> 141.
  """
  # MPFR works in bits: one base-b digit = log2(b) bits.
  gmpy2.get_context().precision = int((n + GUARD) * math.log2(base)) + 64
  frac = gmpy2.const_pi() - 3
  scaled = gmpy2.floor(frac * gmpy2.mpz(base) ** (n + GUARD))
  return gmpy2.mpz(scaled) // gmpy2.mpz(base) ** GUARD  # drop the guard digits


if __name__ == "__main__":
  base, n = int(sys.argv[1]), int(sys.argv[2])
  v = frac_digits(base, n)
  text = v.digits(base).rjust(n, "0")  # leading zero digits are lost in an integer: put them back
  if base == 26:
    text = text.translate(B26)
  with open(OUTPUT[base], "w", encoding="ascii") as f:
    f.write(text)
  print(f"wrote {n:,} base-{base} digits to {OUTPUT[base]}")
