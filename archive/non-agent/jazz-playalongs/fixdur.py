"""Nudge Spotify-computed durations of specific local files up by <0.1 s so they match playlist URIs.
M4A: rewrite iTunSMPB (same length) to priming=0, padding=0, samples=stts total.  MP3: append copies of the last 3 frames (before any ID3v1/APE tail)."""
import os, re, shutil, struct, sys, json
BK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dur_fix_backup"); os.makedirs(BK, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mp4atoms
BR = {1: [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0]}  # MPEG1 Layer III
SR = {3: [44100, 48000, 32000]}
def fix_m4a(p):
    b = bytearray(open(p, "rb").read()); total = mp4atoms.info(p)["stts"][0][0]
    k = b.find(b"iTunSMPB"); assert k > 0, "no iTunSMPB"
    m = re.compile(rb" [0-9A-F]{8} [0-9A-F]{8} [0-9A-F]{8} [0-9A-F]{16}").search(bytes(b), k, k + 200); assert m
    new = b" 00000000 00000000 00000000 " + f"{total:016X}".encode()
    assert len(new) == m.end() - m.start()
    b[m.start():m.end()] = new; open(p, "wb").write(b); return total
def fix_mp3(p):
    b = open(p, "rb").read(); i = 0
    if b[:3] == b"ID3": i = 10 + ((b[6]<<21)|(b[7]<<14)|(b[8]<<7)|b[9])
    tail = len(b)
    if b[-128:-125] == b"TAG": tail -= 128
    if b[tail-32:tail-24] == b"APETAGEX": tail -= struct.unpack("<I", b[tail-20:tail-16])[0] + 32
    frames = []
    while i + 4 <= tail:
        h = b[i:i+4]
        if h[0] == 0xFF and (h[1] & 0xE0) == 0xE0 and ((h[1] >> 3) & 3) == 3 and ((h[1] >> 1) & 3) == 1:
            br = BR[1][h[2] >> 4] * 1000; sr = SR[3][(h[2] >> 2) & 3]; pad = (h[2] >> 1) & 1
            if br and sr: 
                L = 144 * br // sr + pad
                if i + L <= tail: frames.append((i, L)); i += L; continue
        i += 1
    last = frames[-3:]; extra = b"".join(b[o:o+L] for o, L in last)
    end_of_audio = frames[-1][0] + frames[-1][1]
    open(p, "wb").write(b[:end_of_audio] + extra + b[end_of_audio:]); return len(frames), len(extra)
if __name__ == "__main__":
    import mutagen
    for p in sys.argv[1:]:
        shutil.copy2(p, os.path.join(BK, os.path.basename(p)))
        before = mutagen.File(p).info.length
        r = fix_m4a(p) if p.lower().endswith(".m4a") else fix_mp3(p)
        print(f"{os.path.basename(p)[:45]:45s} {before:.3f}s -> {mutagen.File(p).info.length:.3f}s  ({r})")
