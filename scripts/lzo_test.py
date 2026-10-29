#!/usr/bin/env python3
"""LZO1X decompressor (minilzo `lzo1x_decompress`), stdlib only.

LZO is very common in Korean game engines of this era, and the .table payloads
are measurably image-derived but match no standard codec.
"""
import struct
import sys
import zlib


def lzo1x_decompress(src, srclen, dstlen):
    out = bytearray(dstlen)
    ip = 0
    op = 0
    if srclen < 3:
        return None
    t = 0
    if src[ip] > 17:
        t = src[ip] - 17
        ip += 1
        if t < 4:
            pass
        else:
            if op + t > dstlen or ip + t > srclen:
                return None
            out[op:op + t] = src[ip:ip + t]
            op += t
            ip += t
    while True:
        if ip >= srclen:
            return None
        t = src[ip]
        ip += 1
        if t >= 16:
            # match
            m_pos = 0
            if t >= 64:
                m_pos = op - 1
                m_pos -= (t >> 2) & 7
                m_pos -= src[ip] << 3
                ip += 1
                t = (t >> 5) - 1
            elif t >= 32:
                t &= 31
                if t == 0:
                    while src[ip] == 0:
                        t += 255
                        ip += 1
                    t += 31 + src[ip]
                    ip += 1
                m_pos = op - 1
                m_pos -= (src[ip] >> 2) + (src[ip + 1] << 6)
                ip += 2
            elif t >= 16:
                m_pos = op
                m_pos -= (t & 8) << 11
                t &= 7
                if t == 0:
                    while src[ip] == 0:
                        t += 255
                        ip += 1
                    t += 7 + src[ip]
                    ip += 1
                m_pos -= (src[ip] >> 2) + (src[ip + 1] << 6)
                ip += 2
                if m_pos == op:
                    return bytes(out[:op])          # end of stream
                m_pos -= 0x4000
            else:
                m_pos = op - 1
                m_pos -= t >> 2
                m_pos -= src[ip] << 2
                ip += 1
                # copy 2
                if m_pos < 0 or op + 2 > dstlen:
                    return None
                for k in range(2):
                    out[op] = out[m_pos]
                    op += 1
                    m_pos += 1
                continue
            if m_pos < 0 or m_pos >= op:
                return None
            t += 2
            if op + t > dstlen:
                return None
            for k in range(t):
                out[op] = out[m_pos]
                op += 1
                m_pos += 1
            continue
        # literal run
        if t == 0:
            while ip < srclen and src[ip] == 0:
                t += 255
                ip += 1
            t += 15 + src[ip]
            ip += 1
        t += 3
        if op + t > dstlen or ip + t > srclen:
            return None
        out[op:op + t] = src[ip:ip + t]
        op += t
        ip += t
        # first literal run: must be followed by an M2 match
        if ip >= srclen:
            return bytes(out[:op])
        t = src[ip]
        ip += 1
        if t >= 16:
            # handle as match by backing up
            ip -= 1
            continue
        m_pos = op - 1 - 0x0800
        m_pos -= t >> 2
        if ip >= srclen:
            return None
        m_pos -= src[ip] << 2
        ip += 1
        if m_pos < 0 or op + 3 > dstlen:
            return None
        for k in range(3):
            out[op] = out[m_pos]
            op += 1
            m_pos += 1


def main():
    p = sys.argv[1]
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    b = open(p, "rb").read()
    print(f"{p} size={len(b)}")
    for off in range(0, 8):
        src = b[off:]
        # try a range of dstlen guesses around the w*h targets
        for dl in ([target] if target else
                   [18944, 56832, 75776, 150480, 30096, 451440]):
            r = lzo1x_decompress(src, len(src), dl)
            if r and len(r) > 100:
                print(f"  LZO off={off} dstlen={dl}: produced {len(r)}")
                return
    print("  LZO1X did not decode")


if __name__ == "__main__":
    main()
