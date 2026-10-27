"""Tiny MP4 atom walker: report mvhd/tkhd/mdhd durations, elst, stts sample counts, iTunSMPB."""
import struct, sys
CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"edts", b"udta", b"ilst", b"dinf"}
def walk(b, start, end, depth, out):
    i = start
    while i + 8 <= end:
        size, typ = struct.unpack(">I4s", b[i:i+8]); hdr = 8
        if size == 1: size = struct.unpack(">Q", b[i+8:i+16])[0]; hdr = 16
        elif size == 0: size = end - i
        body = i + hdr
        out.append((depth, typ, i, size, body))
        if typ in CONTAINERS: walk(b, body, i + size, depth + 1, out)
        elif typ == b"meta": walk(b, body + 4, i + size, depth + 1, out)
        i += size
def info(path):
    b = open(path, "rb").read(); out = []; walk(b, 0, len(b), 0, out); res = {}
    for depth, typ, off, size, body in out:
        if typ in (b"mvhd", b"mdhd"):
            v = b[body]
            if v == 0: ts, dur = struct.unpack(">II", b[body+12:body+20])
            else: ts, dur = struct.unpack(">IQ", b[body+20:body+32])
            res.setdefault(typ.decode(), []).append((v, ts, dur, round(dur/ts, 4), off))
        elif typ == b"tkhd":
            v = b[body]; dur = struct.unpack(">I", b[body+20:body+24])[0] if v == 0 else struct.unpack(">Q", b[body+28:body+36])[0]
            res.setdefault("tkhd", []).append((v, dur, off))
        elif typ == b"elst":
            v = b[body]; n = struct.unpack(">I", b[body+4:body+8])[0]
            ents = [struct.unpack(">IiI", b[body+8+12*k: body+20+12*k]) for k in range(n)] if v == 0 else [struct.unpack(">QqI", b[body+8+20*k: body+28+20*k]) for k in range(n)]
            res.setdefault("elst", []).append((v, ents, off))
        elif typ == b"stts":
            n = struct.unpack(">I", b[body+4:body+8])[0]; ents = [struct.unpack(">II", b[body+8+8*k: body+16+8*k]) for k in range(n)]
            res.setdefault("stts", []).append((sum(c*d for c, d in ents), ents[:3]))
    k = b.find(b"iTunSMPB")
    if k >= 0: res["iTunSMPB"] = b[k: k+120].split(b"\x00data")[-1][8:100].decode("latin-1", "replace")
    return res
if __name__ == "__main__":
    for p in sys.argv[1:]: print(p.split("/")[-1], info(p))
