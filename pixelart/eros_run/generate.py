"""Eros : course vers la droite, basée sur le modèle BASE_running_right
(2 frames de passage + 2 frames de foulée large avec rebond d'1 px).

Entrées : EROS_walk_right.aseprite (perso), BASE_running_right.aseprite (timing/poses)
Sorties : out/
"""
import os
import struct
import zlib

from PIL import Image

from read_ase import load

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "EROS_walk_right.aseprite")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

O = (0, 0, 0)
CMAP = {"#": O, "s": (242, 233, 190), "P": (222, 174, 148), "r": (148, 43, 65),
        "R": (117, 31, 45), "q": (193, 51, 75), "k": (32, 45, 50), "W": (255, 255, 255),
        "y": (232, 191, 123)}

walk, _ = load(SRC)


def grid(img):
    return {(x, y): img.getpixel((x, y))[:3] for y in range(32) for x in range(32)
            if img.getpixel((x, y))[3]}


F = [grid(f) for f in walk]


def is_head(x, y, i):
    b = 1 if i in (1, 3) else 0
    return y <= 19 - b or (y <= 20 - b and x < 10)


HEAD = {p: c for p, c in F[0].items() if is_head(*p, 0)}
PONY = {p: c for p, c in HEAD.items() if p[0] <= 8}
BODY = [{p: c for p, c in F[i].items() if not is_head(*p, i)} for i in range(4)]


def rows_to_px(rows, x0):
    d = {}
    for y, row in rows.items():
        for i, ch in enumerate(row):
            if ch != ".":
                d[(x0 + i, y)] = CMAP[ch]
    return d


# Foulée A (modèle frame 1) : bras avant, jambe arrière en poussée loin derrière
LEGS_A = rows_to_px({
    26: ".###############",
    27: "#WWWkkkk#...#kk#",
    28: "#kWW#kk#....#kWWW#",
    29: ".###.##......####",
}, 4)
# Foulée B (modèle frame 3) : bras arrière, pied arrière au sol, genou avant levé
LEGS_B = rows_to_px({
    25: "...#rrrRRrrR",
    26: "..###########....",
    27: "..#kk#.....#kkWWW#",
    28: ".#WWk#.....######",
    29: ".####",
}, 8)


def stride(i, legs, cut):
    L = {p: c for p, c in BODY[i].items() if p[1] < cut}
    L.update(legs)
    return L


LEAN = 1   # la tête avance d'1 px : le perso penche vers l'avant


def frame(body, bob, pony_lift):
    L = dict(body)
    head = {p: c for p, c in HEAD.items() if p not in PONY}
    for (x, y), c in head.items():
        L[(x + LEAN, y - bob)] = c
    for (x, y), c in PONY.items():
        L[(x + LEAN, y - bob - pony_lift)] = c
    return L


run = [
    frame(BODY[0], 0, 0),                    # passage
    frame(stride(3, LEGS_A, 26), 1, 1),      # foulée A (rebond)
    frame(BODY[2], 0, 0),                    # passage
    frame(stride(1, LEGS_B, 25), 1, 1),      # foulée B (rebond)
]
DUR = [80, 80, 80, 80]


def render(L, w=32, h=32):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in L.items():
        if 0 <= x < w and 0 <= y < h:
            img.putpixel((x, y), c + (255,))
    return img


imgs = [render(L) for L in run]
sheet = Image.new("RGBA", (32 * 4, 32), (0, 0, 0, 0))
for i, im in enumerate(imgs):
    sheet.alpha_composite(im, (i * 32, 0))
sheet.save(os.path.join(OUT, "eros_run_right.png"))

# ------------------------------------------------------------ .aseprite
ORIG = open(SRC, "rb").read()


def orig_chunks(types):
    off, end = 128 + 16, 128 + struct.unpack_from("<I", ORIG, 128)[0]
    res = []
    while off < end:
        csize, ctype = struct.unpack_from("<IH", ORIG, off)
        if ctype in types:
            res.append(ORIG[off:off + csize])
        off += csize
    return res


def chunk(t, data):
    return struct.pack("<IH", len(data) + 6, t) + data


def astr(s):
    b = s.encode()
    return struct.pack("<H", len(b)) + b


frames_b = []
for f, (im, dur) in enumerate(zip(imgs, DUR)):
    ch = []
    if f == 0:
        ch += orig_chunks((0x2007, 0x2019))
        ch.append(chunk(0x2004, struct.pack("<HHHHHHB3x", 3, 0, 0, 0, 0, 0, 255) + astr("Eros")))
        ch.append(chunk(0x2018, struct.pack("<H8x", 1) +
                        struct.pack("<HHBH6x3Bx", 0, 3, 0, 0, 80, 160, 255) + astr("run_right")))
    bb = im.getbbox()
    crop = im.crop(bb)
    ch.append(chunk(0x2005, struct.pack("<HhhBHh5x", 0, bb[0], bb[1], 255, 2, 0) +
                    struct.pack("<HH", crop.width, crop.height) + zlib.compress(crop.tobytes())))
    body = b"".join(ch)
    frames_b.append(struct.pack("<IHHH2xI", 16 + len(body), 0xF1FA, len(ch), dur, len(ch)) + body)
allf = b"".join(frames_b)
hdr = bytearray(ORIG[:128])
struct.pack_into("<IHHHHH", hdr, 0, 128 + len(allf), 0xA5E0, 4, 32, 32, 32)
open(os.path.join(OUT, "EROS_run_right.aseprite"), "wb").write(bytes(hdr) + allf)


# ------------------------------------------------------------ aperçus
def backdrop(w, h, scroll=0):
    bg = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            xx = x + scroll
            col = [(58, 66, 108), (54, 61, 101)][((xx // 16) + (y // 16)) % 2]
            if xx % 16 == 15 or y % 16 == 15:
                col = (36, 40, 70)
            elif xx % 16 == 0 or y % 16 == 0:
                col = (78, 90, 136)
            bg.putpixel((x, y), col + (255,))
    return bg


def shadow(img, cx, cy, rx):
    for x in range(cx - rx, cx + rx + 1):
        for yy in (cy, cy + 1):
            p = img.getpixel((x, yy))
            img.putpixel((x, yy), tuple(int(v * 0.6) for v in p[:3]) + (255,))


# course sur place avec sol qui défile + comparaison marche / course
S = 6
frames = []
for t in range(16):
    b = backdrop(32, 32, t * 4)
    shadow(b, 16, 29, 6)
    b.alpha_composite(imgs[t % 4])
    frames.append(b.convert("RGB").resize((32 * S, 32 * S), Image.NEAREST))
frames[0].save(os.path.join(OUT, "preview_run_x6.gif"), save_all=True,
               append_images=frames[1:], duration=80, loop=0)

cmp_frames = []
for t in range(24):
    b = Image.new("RGBA", (72, 32))
    b.paste(backdrop(32, 32, t * 2), (0, 0))
    b.paste(backdrop(32, 32, t * 4), (40, 0))
    shadow(b, 16, 29, 6)
    shadow(b, 56, 29, 6)
    wi = walk[(t // 2) % 4] if False else walk[(t * 80 // 100) % 4]
    b.alpha_composite(wi, (0, 0))
    b.alpha_composite(imgs[t % 4], (40, 0))
    cmp_frames.append(b.convert("RGB").resize((72 * S, 32 * S), Image.NEAREST))
cmp_frames[0].save(os.path.join(OUT, "preview_walk_vs_run_x6.gif"), save_all=True,
                   append_images=cmp_frames[1:], duration=80, loop=0)

strip = backdrop(32 * 4, 32)
strip.alpha_composite(sheet)
strip.resize((128 * 8, 32 * 8), Image.NEAREST).save(os.path.join(OUT, "run_strip_x8.png"))
print("ok")
