/*
 * C ABI:
 *   void invert25519(uint64_t out[4], const uint64_t in[4]);
 *
 * out and in may alias.
 */

.text
.p2align 2
.global invert25519
.global _invert25519
.type invert25519, %function

_invert25519:
invert25519:

        ldp x16, x2, [x1, #16]
        movz x10, #0xffed
        mov x14, #19
        movk x10, #0x3fff, lsl #16
        mov x4, #-19
        ldp x13, x9, [x1]
        mov x6, #1
        movi v17.4S, #0
        movk x10, #0xffff, lsl #32
        mov x3, #0x7fff
        movk x10, #0x3fff, lsl #48
        movi v4.4S, #0
        mov x7, #0x4000000
        mov v0.d[0], x10
        add x10, x10, #18
        mov v3.d[0], x10
        mov v1.d[0], x10
        lsr x11, x2, #63
        orr x12, x2, #0x8000000000000000
        madd x11, x14, x11, x14
        movi v28.2D, #-1
        and x4, x4, #0x00000000000fffff
        movi v16.4S, #0
        mov v4.d[0], x3
        orr x4, x4, #0xfffffe0000000000
        mov v2.d[0], x10
        movi v5.4S, #0
        adds x3, x13, x11
        movz x10, #0x0080, lsl #16
        ushr v28.2D, v28.2D, #40
        adcs x2, x9, xzr
        mov x11, #1
        movi v6.4S, #0
        adcs x16, x16, xzr
        dup v30.4S, w10
        mov v5.s[2], w11
        movz x10, #0xca1b
        adcs x13, x12, xzr
        movi v7.4S, #0
        csel x11, x14, xzr, cc
        movk x10, #0x006b, lsl #16
        movi v27.2D, #-1
        subs x8, x3, x11
        dup v29.4S, w10
        movi v31.4S, #19
        movz x10, #0x0020, lsl #16
        sbcs x9, x2, xzr
        mov x5, x8
        dup v18.2D, x8
        sbcs x2, x16, xzr
        ushr v27.2D, v27.2D, #34
        mov v31.s[1], w10
        sbc x10, x13, xzr
        and x5, x5, #0x00000000000fffff
        orr x5, x5, #0xc000000000000000
        tst x5, #1
        and x13, x10, #0x7fffffffffffffff
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        ushr v19.2D, v18.2D, #30
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        zip1 v19.2D, v18.2D, v19.2D
        cneg x16, x10, ge
        add x6, x6, #2
        add x5, x5, x16
        and v19.16B, v19.16B, v27.16B
        tst x5, #2
        csel x10, x4, xzr, ne
        xtn2 v0.4S, v19.2D
        dup v19.2D, x8
        ushr v18.2D, v19.2D, #60
        dup v19.2D, x9
        ccmp x6, xzr, #0x8, ne
        cneg x6, x6, ge
        add x6, x6, #2
        asr x5, x5, #1
        ushr v20.2D, v19.2D, #56
        dup v19.2D, x2
        cneg x10, x10, ge
        csel x4, x5, x4, ge
        add x5, x5, x10
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        cneg x6, x6, ge
        csel x4, x5, x4, ge
        sli v20.2D, v19.2D, #8
        cneg x10, x10, ge
        add x6, x6, #2
        ushr v19.2D, v19.2D, #22
        add x5, x5, x10
        tst x5, #2
        zip1 v19.2D, v20.2D, v19.2D
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        and v19.16B, v19.16B, v27.16B
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        xtn2 v2.4S, v19.2D
        cneg x10, x10, ge
        dup v19.2D, x2
        add x6, x6, #2
        add x5, x5, x10
        tst x5, #2
        asr x5, x5, #1
        ushr v24.2D, v19.2D, #52
        movi v19.2D, #0
        csel x11, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        mov v19.d[0], x13
        cneg x6, x6, ge
        cneg x10, x11, ge
        add x6, x6, #2
        add x5, x5, x10
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ushr v19.2D, v19.2D, #48
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x12, x10, ge
        add x5, x5, x12
        cneg x6, x6, ge
        add x6, x6, #2
        xtn2 v4.4S, v19.2D
        dup v19.2D, x9
        sli v18.2D, v19.2D, #4
        tst x5, #2
        asr x5, x5, #1
        ushr v19.2D, v19.2D, #26
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        cneg x10, x10, ge
        add x6, x6, #2
        zip1 v19.2D, v18.2D, v19.2D
        add x5, x5, x10
        tst x5, #2
        asr x5, x5, #1
        and v19.16B, v19.16B, v27.16B
        csel x12, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        xtn2 v1.4S, v19.2D
        dup v19.2D, x13
        cneg x10, x12, ge
        add x6, x6, #2
        add x5, x5, x10
        sli v24.2D, v19.2D, #12
        ushr v19.2D, v19.2D, #18
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        zip1 v19.2D, v24.2D, v19.2D
        cneg x10, x10, ge
        cneg x6, x6, ge
        add x5, x5, x10
        add x6, x6, #2
        and v19.16B, v19.16B, v27.16B
        tst x5, #2
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        asr x5, x5, #1
        cneg x10, x10, ge
        cneg x6, x6, ge
        csel x4, x5, x4, ge
        add x5, x5, x10
        xtn2 v3.4S, v19.2D
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        cneg x6, x6, ge
        add x5, x5, x10
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        cneg x6, x6, ge
        add x5, x5, x10
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        add x5, x5, x10
        cneg x6, x6, ge
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        add x6, x6, #2
        add x4, x4, x7
        cneg x14, x10, ge
        and x4, x4, #0xfffffffff800003f
        ins v26.d[0], x4
        add x5, x5, x14
        asr x5, x5, #1
        add x5, x5, x7
        lsr x7, x7, #2
        and x5, x5, #0xfffffffff800003f
        ins v26.d[1], x5
        shl v19.2D, v26.2D, #22
        sshr v25.2D, v26.2D, #42
        sshr v19.2D, v19.2D, #43
        usra v25.2D, v19.2D, #63
        xtn v19.2S, v19.2D
        xtn2 v19.4S, v25.2D
        neg v19.4S, v19.4S
        shl v18.4S, v19.4S, #4
        shl v19.4S, v19.4S, #10

    mov x3, #24
.p2align 4
Linvert25519_plain_loop:

        smull v24.2D, v18.2S, v0.S[0]
        smlal2 v24.2D, v18.4S, v0.S[2]
        smull v20.2D, v18.2S, v5.S[0]
        smlal2 v20.2D, v18.4S, v5.S[2]
        sshr v18.2D, v24.2D, #24
        mul v24.4S, v20.4S, v29.4S
        smlal v18.2D, v19.2S, v0.S[1]
        smlal2 v18.2D, v19.4S, v0.S[3]
        and v24.16B, v24.16B, v28.16B
        and v0.16B, v18.16B, v27.16B
        sshr v18.2D, v18.2D, #30
        uzp1 v24.4S, v24.4S, v24.4S
        smlal v18.2D, v19.2S, v1.S[0]
        umov x5, v0.d[1]
        umov x4, v0.d[0]
        eor v24.16B, v24.16B, v30.16B
        smlal2 v18.2D, v19.4S, v1.S[2]
        and x5, x5, #0x0000000000ffffff
        sub v26.4S, v24.4S, v30.4S
        orr x5, x5, #0xc000000000000000
        and x4, x4, #0x0000000000ffffff
        and v24.16B, v18.16B, v27.16B
        sshr v22.2D, v18.2D, #30
        tst x5, #1
        smlsl v20.2D, v26.2S, v31.S[0]
        orr x4, x4, #0xffffffe000000000
        sli v0.2D, v24.2D, #32
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        cneg x6, x6, ge
        cneg x10, x10, ge
        csel x4, x5, x4, ge
        add x5, x5, x10
        add x6, x6, #2
        sshr v24.2D, v20.2D, #24
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        smlal v22.2D, v19.2S, v1.S[1]
        csel x4, x5, x4, ge
        smlal v24.2D, v19.2S, v5.S[1]
        cneg x10, x10, ge
        smlal2 v22.2D, v19.4S, v1.S[3]
        cneg x6, x6, ge
        add x5, x5, x10
        add x6, x6, #2
        tst x5, #2
        and v1.16B, v22.16B, v27.16B
        sshr v22.2D, v22.2D, #30
        csel x13, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        smlal2 v24.2D, v19.4S, v5.S[3]
        asr x5, x5, #1
        cneg x13, x13, ge
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        add x5, x5, x13
        add x6, x6, #2
        tst x5, #2
        and v5.16B, v24.16B, v27.16B
        sshr v24.2D, v24.2D, #30
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        asr x5, x5, #1
        cneg x10, x10, ge
        smlal v22.2D, v19.2S, v2.S[0]
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        add x5, x5, x10
        smlal v24.2D, v19.2S, v6.S[0]
        add x6, x6, #2
        tst x5, #2
        smlal2 v24.2D, v19.4S, v6.S[2]
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        smlal2 v22.2D, v19.4S, v2.S[2]
        asr x5, x5, #1
        cneg x10, x10, ge
        cneg x6, x6, ge
        and v23.16B, v22.16B, v27.16B
        csel x4, x5, x4, ge
        add x5, x5, x10
        sshr v22.2D, v22.2D, #30
        add x6, x6, #2
        and v18.16B, v24.16B, v27.16B
        tst x5, #2
        asr x5, x5, #1
        sshr v24.2D, v24.2D, #30
        sli v1.2D, v23.2D, #32
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        sli v5.2D, v18.2D, #32
        csel x4, x5, x4, ge
        cneg x16, x10, ge
        cneg x6, x6, ge
        add x5, x5, x16
        smlal v24.2D, v19.2S, v6.S[1]
        smlal2 v24.2D, v19.4S, v6.S[3]
        add x6, x6, #2
        smlal v22.2D, v19.2S, v2.S[1]
        tst x5, #2
        asr x5, x5, #1
        smlal2 v22.2D, v19.4S, v2.S[3]
        csel x13, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        cneg x6, x6, ge
        cneg x13, x13, ge
        sshr v18.2D, v24.2D, #30
        csel x4, x5, x4, ge
        and v6.16B, v24.16B, v27.16B
        add x5, x5, x13
        add x6, x6, #2
        and v2.16B, v22.16B, v27.16B
        tst x5, #2
        sshr v22.2D, v22.2D, #30
        smlal v18.2D, v19.2S, v7.S[0]
        smlal2 v18.2D, v19.4S, v7.S[2]
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        asr x5, x5, #1
        cneg x10, x10, ge
        cneg x6, x6, ge
        and v24.16B, v18.16B, v27.16B
        csel x4, x5, x4, ge
        add x5, x5, x10
        smlal v22.2D, v19.2S, v3.S[0]
        add x6, x6, #2
        smlal2 v22.2D, v19.4S, v3.S[2]
        sli v6.2D, v24.2D, #32
        tst x5, #2
        asr x5, x5, #1
        sshr v24.2D, v18.2D, #30
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        cneg x6, x6, ge
        add x5, x5, x10
        and v18.16B, v22.16B, v27.16B
        sshr v22.2D, v22.2D, #30
        smlal v24.2D, v19.2S, v7.S[1]
        add x6, x6, #2
        smlal2 v24.2D, v19.4S, v7.S[3]
        tst x5, #2
        asr x5, x5, #1
        sli v2.2D, v18.2D, #32
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        cneg x6, x6, ge
        smlal v22.2D, v19.2S, v3.S[1]
        add x5, x5, x10
        smlal2 v22.2D, v19.4S, v3.S[3]
        and v7.16B, v24.16B, v27.16B
        add x6, x6, #2
        tst x5, #2
        sshr v3.2D, v24.2D, #30
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        cneg x6, x6, ge
        smlal v3.2D, v19.2S, v16.S[0]
        add x5, x5, x10
        smlal2 v3.2D, v19.4S, v16.S[2]
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        cneg x10, x10, ge
        csel x4, x5, x4, ge
        sshr v24.2D, v3.2D, #30
        and v3.16B, v3.16B, v27.16B
        add x4, x4, x7
        cneg x6, x6, ge
        add x5, x5, x10
        sshr v21.2D, v22.2D, #30
        add x6, x6, #2
        and x4, x4, #0xfffffffffe000fff
        tst x5, #2
        sli v7.2D, v3.2D, #32
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        add x5, x5, x7
        smlal v24.2D, v19.2S, v16.S[1]
        cneg x10, x10, ge
        and v3.16B, v22.16B, v27.16B
        smlal2 v24.2D, v19.4S, v16.S[3]
        and x5, x5, #0xfffffffffe000fff
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        add x5, x5, x10
        smlal v21.2D, v19.2S, v4.S[0]
        add x6, x6, #2
        tst x5, #2
        smlal2 v21.2D, v19.4S, v4.S[2]
        and v16.16B, v24.16B, v27.16B
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        sshr v18.2D, v24.2D, #30
        cneg x6, x6, ge
        cneg x10, x10, ge
        csel x4, x5, x4, ge
        add x5, x5, x10
        smlal v18.2D, v19.2S, v17.S[0]
        sshr v4.2D, v21.2D, #30
        add x6, x6, #2
        smlal2 v18.2D, v19.4S, v17.S[2]
        tst x5, #2
        asr x5, x5, #1
        smlal v18.2D, v26.2S, v31.S[1]
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        cneg x6, x6, ge
        add x5, x5, x10
        and v19.16B, v18.16B, v27.16B
        sshr v17.2D, v18.2D, #30
        add x6, x6, #2
        tst x5, #2
        and v18.16B, v21.16B, v27.16B
        sli v16.2D, v19.2D, #32
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        asr x5, x5, #1
        cneg x10, x10, ge
        cneg x6, x6, ge
        csel x4, x5, x4, ge
        add x5, x5, x10
        sli v3.2D, v18.2D, #32
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x13, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x13, x13, ge
        cneg x6, x6, ge
        add x5, x5, x13
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        cneg x6, x6, ge
        add x5, x5, x10
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        cneg x6, x6, ge
        add x5, x5, x10
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        cneg x6, x6, ge
        cneg x10, x10, ge
        csel x4, x5, x4, ge
        add x5, x5, x10
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x14, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x14, ge
        cneg x6, x6, ge
        add x5, x5, x10
        add x6, x6, #2
        tst x5, #2
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        asr x5, x5, #1
        cneg x10, x10, ge
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        add x5, x5, x10
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x10, x10, ge
        add x5, x5, x10
        cneg x6, x6, ge
        add x6, x6, #2
        tst x5, #2
        asr x5, x5, #1
        csel x10, x4, xzr, ne
        ccmp x6, xzr, #0x8, ne
        csel x4, x5, x4, ge
        cneg x6, x6, ge
        cneg x10, x10, ge
        add x4, x4, #1, lsl #12
        add x5, x5, x10
        add x6, x6, #2
        ins v18.d[0], x4
        asr x5, x5, #1
        add x5, x5, #1, lsl #12
        ins v18.d[1], x5
        shl v19.2D, v18.2D, #26
        sshr v24.2D, v19.2D, #39
        sshr v19.2D, v18.2D, #38
        usra v19.2D, v24.2D, #63
        xtn v18.2S, v24.2D
        xtn2 v18.4S, v19.2D
        neg v18.4S, v18.4S
        shl v19.4S, v18.4S, #6

    subs x3, x3, #1
    b.ne Linvert25519_plain_loop

        smull v3.2D, v18.2S, v0.S[0]
        smlal2 v3.2D, v18.4S, v0.S[2]
        shl v3.4S, v3.4S, #2
        sshr v3.4S, v3.4S, #31
        dup v21.4S, v3.S[0]
        eor v23.16B, v18.16B, v21.16B
        sub v23.4S, v23.4S, v21.4S
        smull v3.2D, v23.2S, v5.S[0]
        shl v22.4S, v23.4S, #6
        smlal2 v3.2D, v23.4S, v5.S[2]
        mul v24.4S, v3.4S, v29.4S
        and v24.16B, v24.16B, v28.16B
        uzp1 v2.4S, v24.4S, v24.4S
        eor v23.16B, v2.16B, v30.16B
        sub v4.4S, v23.4S, v30.4S
        smlsl v3.2D, v4.2S, v31.S[0]
        sshr v20.2D, v3.2D, #24
        smlal v20.2D, v22.2S, v5.S[1]
        smlal2 v20.2D, v22.4S, v5.S[3]
        sshr v24.2D, v20.2D, #30
        and v5.16B, v20.16B, v27.16B
        smlal v24.2D, v22.2S, v6.S[0]
        smlal2 v24.2D, v22.4S, v6.S[2]
        sshr v23.2D, v24.2D, #30
        smlal v23.2D, v22.2S, v6.S[1]
        smlal2 v23.2D, v22.4S, v6.S[3]
        and v6.16B, v24.16B, v27.16B
        sli v5.2D, v6.2D, #32
        sshr v3.2D, v23.2D, #30
        and v6.16B, v23.16B, v27.16B
        smlal v3.2D, v22.2S, v7.S[0]
        smlal2 v3.2D, v22.4S, v7.S[2]
        sshr v1.2D, v3.2D, #30
        and v24.16B, v3.16B, v27.16B
        smlal v1.2D, v22.2S, v7.S[1]
        sli v6.2D, v24.2D, #32
        smlal2 v1.2D, v22.4S, v7.S[3]
        sshr v3.2D, v1.2D, #30
        smlal v3.2D, v22.2S, v16.S[0]
        movi v2.4S, #0
        smlal2 v3.2D, v22.4S, v16.S[2]
        uzp2 v25.4S, v5.4S, v5.4S
        and v24.16B, v3.16B, v27.16B
        sshr v3.2D, v3.2D, #30
        uzp1 v19.4S, v5.4S, v5.4S
        smlal v3.2D, v22.2S, v16.S[1]
        smlal2 v3.2D, v22.4S, v16.S[3]
        uzp1 v21.4S, v6.4S, v6.4S
        uzp2 v26.4S, v6.4S, v6.4S
        sshr v7.2D, v3.2D, #30
        and v16.16B, v3.16B, v27.16B
        smlal v7.2D, v22.2S, v17.S[0]
        smlal2 v7.2D, v22.4S, v17.S[2]
        smlal v7.2D, v4.2S, v31.S[1]
        movi v22.4S, #1
        sshr v17.2D, v7.2D, #30
        sshr v6.4S, v17.4S, #15
        zip1 v23.4S, v6.4S, v2.4S
        and v6.16B, v7.16B, v27.16B
        and v7.16B, v1.16B, v27.16B
        mla v19.2S, v23.2S, v31.S[0]
        sli v16.2D, v6.2D, #32
        sli v7.2D, v24.2D, #32
        smull v3.2D, v19.2S, v22.S[0]
        uzp2 v4.4S, v7.4S, v7.4S
        uzp1 v1.4S, v7.4S, v7.4S
        uzp1 v24.4S, v16.4S, v16.4S
        sshr v2.2D, v3.2D, #30
        and v5.16B, v3.16B, v27.16B
        smlal v2.2D, v25.2S, v22.S[0]
        sshr v19.2D, v2.2D, #30
        and v6.16B, v2.16B, v27.16B
        uzp2 v2.4S, v16.4S, v16.4S
        smlal v19.2D, v21.2S, v22.S[0]
        uzp1 v17.4S, v17.4S, v17.4S
        sli v5.2D, v6.2D, #32
        sshr v20.2D, v19.2D, #30
        and v6.16B, v19.16B, v27.16B
        shl v3.2S, v23.2S, #15
        smlal v20.2D, v26.2S, v22.S[0]
        sshr v19.2D, v20.2D, #30
        and v16.16B, v20.16B, v27.16B
        sub v20.2S, v17.2S, v3.2S
        smlal v19.2D, v1.2S, v22.S[0]
        sli v6.2D, v16.2D, #32
        umov x16, v5.d[0]
        umov x4, v6.d[0]
        sshr v3.2D, v19.2D, #30
        and v7.16B, v19.16B, v27.16B
        and x10, x16, #0x3fffffff
        ubfx x16, x16, #32, #30
        smlal v3.2D, v4.2S, v22.S[0]
        orr x15, x10, x16, lsl                 #30
        and x9, x4, #0xf
        and v4.16B, v3.16B, v27.16B
        ubfx x6, x4, #32, #30
        orr x5, x15, x9, lsl               #60
        ubfx x12, x4, #4, #26
        orr x14, x12, x6, lsl                 #26
        sshr v25.2D, v3.2D, #30
        sli v7.2D, v4.2D, #32
        smlal v25.2D, v24.2S, v22.S[0]
        umov x11, v7.d[0]
        sshr v26.2D, v25.2D, #30
        and v16.16B, v25.16B, v27.16B
        and x10, x11, #0xff
        orr x13, x14, x10, lsl                   #56
        smlal v26.2D, v2.2S, v22.S[0]
        ubfx x10, x11, #8, #22
        ubfx x14, x11, #32, #30
        orr x10, x10, x14, lsl                 #22
        sshr v3.2D, v26.2D, #30
        and v2.16B, v26.16B, v27.16B
        smlal v3.2D, v20.2S, v22.S[0]
        sli v16.2D, v2.2D, #32
        umov x14, v16.d[0]
        mov v17.16B, v3.16B
        and x3, x14, #0xfff
        umov x11, v17.d[0]
        orr x12, x10, x3, lsl                 #52
        ubfx x10, x14, #12, #18
        ubfx x14, x14, #32, #30
        orr x10, x10, x14, lsl               #18
        and x14, x11, #0xffff
        orr x4, x10, x14, lsl               #48

        stp x5, x13, [x0]
        stp x12, x4, [x0, #16]

    ret

.size invert25519, .-invert25519
