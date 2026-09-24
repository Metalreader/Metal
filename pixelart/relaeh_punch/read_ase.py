"""Lecteur minimal .aseprite (RGBA, cels compressés) -> liste d'images PIL."""
import struct, zlib
from PIL import Image

def load(path):
    d = open(path, 'rb').read()
    _, _, frames, w, h, depth = struct.unpack_from('<IHHHHH', d, 0)
    assert depth == 32
    out, durs = [], []
    off = 128
    for _ in range(frames):
        fsize, _, old, dur = struct.unpack_from('<IHHH', d, off)
        nch = struct.unpack_from('<I', d, off + 12)[0] or old
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        co = off + 16
        for _ in range(nch):
            csize, ctype = struct.unpack_from('<IH', d, co)
            if ctype == 0x2005:
                li, x, y, op, ct = struct.unpack_from('<HhhBH', d, co + 6)
                if ct in (0, 2):
                    cw, chh = struct.unpack_from('<HH', d, co + 22)
                    raw = d[co + 26:co + csize]
                    if ct == 2:
                        raw = zlib.decompress(raw)
                    cel = Image.frombytes('RGBA', (cw, chh), raw)
                    img.alpha_composite(cel, (x, y))
            co += csize
        out.append(img)
        durs.append(dur)
        off += fsize
    return out, durs
