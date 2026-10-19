#!/usr/bin/env python3
"""Single-step safegcd inversion modulo p = 2**255 - 19.

This uses the same half-delta variant as the published assembly, but applies
each divstep directly to full Python integers, without jump matrices. The
integer delta2 represents twice delta: it starts at 1 (delta = 1/2) and is
updated to 2 +/- delta2. After reducing the input modulo p, 588 steps suffice.

Throughout the loop, the coefficient invariants are

    f == v * a (mod p),    g == r * a (mod p).

Dividing the coefficients by 2 modulo p at every step absorbs the scaling,
so the final inverse only needs the sign correction from f and normalization.
Zero residues return zero, matching the assembly interface.

This is an executable mathematical reference; Python is not constant time.
It requires only the Python 3.8+ standard library. Run the embedded tests with:

    python3 alg/safegcd25519_nojump.py

Background: Bernstein--Yang safegcd and Wuille's half-delta variant/bound:
https://gcd.cr.yp.to/safegcd-20190413.pdf
https://github.com/sipa/safegcd-bounds#A-faster-variant-of-divsteps-hddivsteps
"""

P = (1 << 255) - 19
DIVSTEPS = 588


def invert25519(a: int) -> int:
    """Return the canonical inverse of unsigned 256-bit a, or zero if p | a."""
    if not isinstance(a, int):
        raise TypeError("a must be an integer")
    if not 0 <= a < (1 << 256):
        raise ValueError("a must be an unsigned 256-bit integer")

    a %= P
    delta2, f, g = 1, P, a
    v, r = 0, 1

    for _ in range(DIVSTEPS):
        if delta2 > 0 and (g & 1):
            # Swap f and g, then subtract the old f before halving g.
            delta2 = 2 - delta2
            f, g = g, (g - f) // 2
            v, r = r, r - v
        else:
            # Odd g needs an addition of f to make the numerator even.
            odd = g & 1
            delta2 += 2
            g = (g + odd * f) // 2
            r += odd * v

        # Divide r by 2 modulo p: adding odd p makes an odd residue even.
        r %= P
        r = (r + (r & 1) * P) // 2

    assert g == 0, "divsteps did not converge"
    assert abs(f) == (P if a == 0 else 1), "unexpected final gcd"
    return (-v if f < 0 else v) % P


if __name__ == "__main__":
    import random

    boundary_inputs = [
        0, 1,
        P - 1, P, P + 1,
        2 * P - 1, 2 * P, 2 * P + 1,
        (1 << 255) - 1, 1 << 255, (1 << 256) - 1,
    ]
    rng = random.Random(0x25519)
    random_inputs = [rng.getrandbits(256) for _ in range(200)]

    for a in boundary_inputs + random_inputs:
        residue = a % P
        expected = 0 if residue == 0 else pow(residue, -1, P)
        actual = invert25519(a)
        assert actual == expected, (
            f"a={a:#x}: expected {expected:#x}, got {actual:#x}"
        )
        assert 0 <= actual < P
        assert (a * actual) % P == (0 if residue == 0 else 1)

    print(
        f"PASS: {len(boundary_inputs)} boundary cases and "
        f"{len(random_inputs)} random unsigned 256-bit inputs "
        f"(seed=0x25519, {DIVSTEPS} single divsteps per input)"
    )
