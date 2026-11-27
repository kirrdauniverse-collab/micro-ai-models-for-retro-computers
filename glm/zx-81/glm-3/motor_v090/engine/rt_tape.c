/* rt_tape.c - RT-turbo block codec over a pulse stream (see rt_tape.h).
 *
 * The decoder is a plain sequential state machine, so the very same C code
 * runs on the host simulator (pulses from a file) and on real hardware
 * (HAL counts CPU cycles between cassette port edges and converts to us).
 */
#include "rt_tape.h"

#define IN_RANGE(v, base, tol) \
    ((v) >= (base) * (100 - (tol)) / 100 && (v) <= (base) * (100 + (tol)) / 100)

rt_u16 rt_crc16(const rt_u8 *p, long n)
{
    rt_u16 crc = 0xFFFF;
    long i;
    int b;
    for (i = 0; i < n; i++) {
        crc ^= (rt_u16)((rt_u16)p[i] << 8);
        for (b = 0; b < 8; b++)
            crc = (rt_u16)((crc & 0x8000) ? (crc << 1) ^ 0x1021 : (crc << 1));
    }
    return crc;
}

/* pulse() == 0 means "no edge within timeout" (motor stopped / unplugged):
 * every caller treats it as an abort condition. */
static int rd_bit(rt_pulse_fn pulse)
{
    rt_u16 t = pulse();
    if (t == 0)
        return -1;
    if (IN_RANGE(t, RT_T_ZERO_US, 25))
        return 0;
    if (IN_RANGE(t, RT_T_ONE_US, 25))
        return 1;
    return -1;
}

static int rd_u16(rt_pulse_fn pulse, rt_u16 *out)
{
    int i, b;
    rt_u16 v = 0;
    for (i = 15; i >= 0; i--) {
        b = rd_bit(pulse);
        if (b < 0)
            return -1;
        if (b)
            v = (rt_u16)(v | ((rt_u16)1 << i));
    }
    *out = v;
    return 0;
}

long rt_tape_read_block(rt_u8 *buf, long maxlen, rt_pulse_fn pulse)
{
    long run = 0, i;
    rt_u16 crc, want;
    int b, byte, bit;

    /* 1. hunt for the pilot train */
    while (run < RT_T_PILOT_MIN) {
        rt_u16 t = pulse();
        if (t == 0)
            return -1; /* timeout, no tape */
        if (IN_RANGE(t, RT_T_PILOT_US, 25))
            run++;
        else
            run = 0;
    }

    /* 2. pilot continues until the SYNC PAIR shows up */
    for (;;) {
        rt_u16 t = pulse();
        if (t == 0)
            return -1;
        if (IN_RANGE(t, RT_T_PILOT_US, 25))
            continue;
        if (IN_RANGE(t, RT_T_SYNC_US, 20)) {
            rt_u16 t2 = pulse();
            if (t2 != 0 && IN_RANGE(t2, RT_T_SYNC_US, 20))
                break;
        }
        return -1; /* junk right after the pilot */
    }

    /* 3. header: payload length */
    if (rd_u16(pulse, &want) < 0)
        return -1;
    if (want > maxlen)
        return -2;

    /* 4. payload */
    for (i = 0; i < (long)want; i++) {
        byte = 0;
        for (bit = 7; bit >= 0; bit--) {
            b = rd_bit(pulse);
            if (b < 0)
                return -1;
            if (b)
                byte |= 1 << bit;
        }
        buf[i] = (rt_u8)byte;
    }

    /* 5. crc */
    if (rd_u16(pulse, &crc) < 0)
        return -1;
    if (crc != rt_crc16(buf, want))
        return -3;

    return want;
}

static void wr_bit(int bit, rt_pulse_out_fn out)
{
    out((rt_u16)(bit ? RT_T_ONE_US : RT_T_ZERO_US));
}

static void wr_u16(rt_u16 v, rt_pulse_out_fn out)
{
    int i;
    for (i = 15; i >= 0; i--)
        wr_bit((v >> i) & 1, out);
}

int rt_tape_write_block(const rt_u8 *buf, long len, rt_pulse_out_fn out)
{
    long i;
    int b;
    if (len < 0 || len > 65535)
        return -1;

    for (i = 0; i < 64; i++)
        out((rt_u16)RT_T_PILOT_US);
    out((rt_u16)RT_T_SYNC_US);
    out((rt_u16)RT_T_SYNC_US);
    wr_u16((rt_u16)len, out);
    for (i = 0; i < len; i++)
        for (b = 7; b >= 0; b--)
            wr_bit((buf[i] >> b) & 1, out);
    wr_u16(rt_crc16(buf, len), out);
    out(3000); /* end marker (optional for the reader) */
    return 0;
}
