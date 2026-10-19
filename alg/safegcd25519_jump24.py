#!/usr/bin/env python3
"""24-step jump safegcd inversion modulo p = 2**255 - 19.

Like the no-jump reference, this uses half-delta divsteps with delta2 = 2*delta
starting at 1. A jump builds an integer matrix M from only the low 24 bits of
f and g, then updates the full integers once:

    [f_next, g_next]^T = M * [f, g]^T / 2**24.

The coefficient invariants are f == d*a (mod p) and g == e*a (mod p). Apply
the same matrix to d,e, dividing by 2**24 modulo p using a precomputed constant.
Thus each jump absorbs its scaling, leaving only the final sign correction.

The schedule uses 25 identical jumps: 24 * 25 = 600 divsteps. Once g reaches
zero, further divsteps preserve f and d. Zero residues return zero.

This is an executable mathematical reference; Python is not constant time.
It requires only the Python 3.8+ standard library. Run the embedded tests with:

    python3 alg/safegcd25519_jump24.py

Background on jump matrices and the half-delta variant/bound:
https://github.com/bitcoin-core/secp256k1/blob/master/doc/safegcd_implementation.md
https://github.com/sipa/safegcd-bounds#A-faster-variant-of-divsteps-hddivsteps
"""

P = (1 << 255) - 19
JUMP_STEPS = 24
JUMPS = 25
DIVSTEPS = JUMP_STEPS * JUMPS
SCALE = 1 << JUMP_STEPS
# (p+1)//2 is 1/2 modulo p; this fixed power is independent of the input.
INVERSE_SCALE = pow((P + 1) // 2, JUMP_STEPS, P)


def jumpdivsteps(delta2: int, f: int, g: int):
    """Return (delta2_next, (u,v,q,r)), with M=[[u,v],[q,r]], for 24 steps.

    M starts as the identity. Each step left-multiplies it by the appropriate
    integer divstep matrix, with its division by 2 deferred until the end.
    Only the low 24 bits of f,g are used to select the steps; the
    resulting matrix also applies to the original full-width signed values.
    """
    if not (f & 1):
        raise ValueError("f must be odd")

    mask = SCALE - 1
    f, g = f & mask, g & mask
    u, v, q, r = 1, 0, 0, 1

    for _ in range(JUMP_STEPS):
        if delta2 > 0 and (g & 1):
            delta2 = 2 - delta2
            f, g = g, (g - f) // 2
            # M <- [[0, 2], [-1, 1]] * M.
            u, v, q, r = 2 * q, 2 * r, q - u, r - v
        else:
            odd = g & 1
            delta2 += 2
            g = (g + odd * f) // 2
            # M <- [[2, 0], [odd, 1]] * M.
            u, v, q, r = 2 * u, 2 * v, q + odd * u, r + odd * v

    return delta2, (u, v, q, r)


def invert25519(a: int) -> int:
    """Return the canonical inverse of unsigned 256-bit a, or zero if p | a."""
    if not isinstance(a, int):
        raise TypeError("a must be an integer")
    if not 0 <= a < (1 << 256):
        raise ValueError("a must be an unsigned 256-bit integer")

    a %= P
    delta2, f, g = 1, P, a
    d, e = 0, 1

    for _ in range(JUMPS):
        delta2, (u, v, q, r) = jumpdivsteps(delta2, f, g)
        f_num, g_num = u * f + v * g, q * f + r * g
        assert f_num % SCALE == 0 and g_num % SCALE == 0
        f, g = f_num // SCALE, g_num // SCALE

        # Apply M/2**24 modulo p to the coefficients, using the old d,e.
        d, e = (
            ((u * d + v * e) * INVERSE_SCALE) % P,
            ((q * d + r * e) * INVERSE_SCALE) % P,
        )

    assert g == 0, "divsteps did not converge"
    assert abs(f) == (P if a == 0 else 1), "unexpected final gcd"
    return (-d if f < 0 else d) % P


if __name__ == "__main__":
    import random

    def check_jumps(a):
        """Compare each jump with full-width single steps, including negatives."""
        delta2, f, g = 1, P, a % P
        for _ in range(JUMPS):
            next_delta2, (u, v, q, r) = jumpdivsteps(delta2, f, g)
            old_f, old_g = f, g

            # Independent full-width recurrence: no low-bit truncation or matrix.
            for _ in range(JUMP_STEPS):
                if delta2 > 0 and (g & 1):
                    delta2, f, g = 2 - delta2, g, (g - f) // 2
                elif g & 1:
                    delta2, g = 2 + delta2, (g + f) // 2
                else:
                    delta2, g = 2 + delta2, g // 2

            assert next_delta2 == delta2, f"delta mismatch for a={a:#x}"
            assert u * old_f + v * old_g == SCALE * f, f"f mismatch for a={a:#x}"
            assert q * old_f + r * old_g == SCALE * g, f"g mismatch for a={a:#x}"
            assert u * r - v * q == SCALE, f"determinant mismatch for a={a:#x}"

    boundary_inputs = [
        0, 1,
        P - 1, P, P + 1,
        2 * P - 1, 2 * P, 2 * P + 1,
        (1 << 255) - 1, 1 << 255, (1 << 256) - 1,
    ]
    rng = random.Random(0x25519)
    random_inputs = [rng.getrandbits(256) for _ in range(200)]

    for a in boundary_inputs + random_inputs:
        check_jumps(a)
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
        f"(seed=0x25519, {DIVSTEPS} divsteps per input)"
    )
    print("PASS: every jump matrix matches full-width single divsteps")
