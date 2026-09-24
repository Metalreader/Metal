"""Eros : cycle de course vers la droite (6 frames), corps reconstruit pièce par pièce.

On garde la tête du dessin original (EROS_walk_right.aseprite) ; manteau, bras, jambes
et chaussures sont redessinés à chaque frame avec la palette d'Eros et un contour noir.
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
s_ = (242, 233, 190)
P_ = (222, 174, 148)
r_ = (148, 43, 65)
R_ = (117, 31, 45)
q_ = (193, 51, 75)
d_ = (88, 27, 22)       # rouge très sombre (bras / jambe du fond)
k_ = (58, 74, 86)       # pantalon (jambe proche)
K_ = (32, 45, 50)       # pantalon (jambe du fond)
W_ = (255, 255, 255)
G_ = (170, 176, 190)    # chaussure du fond
y_ = (232, 191, 123)

walk, _ = load(SRC)
F0 = {(x, y): walk[0].getpixel((x, y))[:3] for y in range(32) for x in range(32)
      if walk[0].getpixel((x, y))[3]}
HEAD = {p: c for p, c in F0.items() if p[1] <= 19 or (p[1] == 20 and p[0] < 10)}
PONY = {p for p in HEAD if p[0] <= 8}


# ------------------------------------------------------------ primitives
def line(a, b):
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    return [(round(x0 + (x1 - x0) * t / n), round(y0 + (y1 - y0) * t / n)) for t in range(n + 1)]


def thick(a, b):
    pts = set()
    for (x, y) in line(a, b):
        pts |= {(x, y), (x, y + 1)}
    return pts


class Part:
    def __init__(self):
        self.px = {}

    def add(self, pts, c):
        for p in pts:
            self.px[p] = c
        return self


def outline(part, canvas, inner=O):
    """dessine la pièce avec son contour : noir sur le vide, `inner` sur ce qui est déjà dessiné"""
    ring = set()
    for (x, y) in part.px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in part.px:
                ring.add(q)
    for q in ring:
        canvas[q] = inner if q in canvas else O
    canvas.update(part.px)


# ------------------------------------------------------------ pièces du corps
def torso(b, flap):
    t = Part()
    rows = {20: (14, 18), 21: (13, 18), 22: (13, 19), 23: (13, 19), 24: (13, 19), 25: (13, 19)}
    for y, (a, z) in rows.items():
        for x in range(a, z + 1):
            t.px[(x, y - b)] = r_
    for y in (21, 22, 23, 24, 25):
        t.px[(13, y - b)] = R_
        t.px[(14, y - b)] = R_ if y >= 24 else r_
    t.px[(14, 20 - b)] = q_
    t.px[(15, 20 - b)] = q_
    t.px[(16, 20 - b)] = R_
    for y, c in ((22, R_), (23, W_), (24, W_), (25, y_)):
        t.px[(18, y - b)] = c
        t.px[(19, y - b)] = R_
    # pan du manteau qui flotte derrière
    for x in range(13 - flap, 20):
        t.px[(x, 26 - b)] = R_ if x < 15 else r_
    for i in range(flap):
        t.px[(12 - i, 25 - b + (1 if i == flap - 1 else 0))] = R_
        t.px[(12 - i, 26 - b)] = R_
    return t


def leg(hip, foot, near, lifted):
    p = Part()
    pts = thick(hip, (foot[0], foot[1] - 1))
    p.add(pts, k_ if near else K_)
    fx, fy = foot
    shoe = W_ if near else G_
    if lifted:
        p.add({(fx - 1, fy - 1), (fx, fy - 1)}, shoe)
        p.add({(fx + 1, fy - 1)}, shoe)
    else:
        p.add({(fx - 1, fy), (fx, fy), (fx + 1, fy), (fx + 2, fy)}, shoe)
    return p


def arm(shoulder, hand, near):
    a = Part()
    a.add(thick(shoulder, hand), r_ if near else d_)
    hx, hy = hand
    if near:
        a.add({(hx, hy), (hx + 1, hy)}, s_)
        a.add({(hx, hy + 1), (hx + 1, hy + 1)}, P_)
    else:
        a.add({(hx, hy), (hx, hy + 1)}, P_)
    return a


# ------------------------------------------------------------ cycle de course (6 frames)
# b = rebond (px vers le haut), pieds (x, y) avec y=28 au sol, mains (x, y)
CYCLE = [
    # contact : pied proche devant, pied lointain derrière
    dict(b=1, flap=2, nf=(20, 28), nl=False, ff=(9, 26), fl=True, nh=(10, 24), fh=(20, 22)),
    # réception : corps au plus bas
    dict(b=0, flap=1, nf=(17, 28), nl=False, ff=(11, 27), fl=True, nh=(11, 24), fh=(19, 23)),
    # poussée : jambe proche pousse, genou lointain monte
    dict(b=1, flap=3, nf=(12, 28), nl=False, ff=(19, 26), fl=True, nh=(15, 25), fh=(15, 25)),
    # contact (autre côté)
    dict(b=1, flap=2, nf=(9, 26), nl=True, ff=(20, 28), fl=False, nh=(19, 22), fh=(10, 24)),
    dict(b=0, flap=1, nf=(11, 27), nl=True, ff=(17, 28), fl=False, nh=(18, 23), fh=(11, 24)),
    dict(b=1, flap=3, nf=(19, 26), nl=True, ff=(12, 28), fl=False, nh=(15, 25), fh=(15, 25)),
]
PONY_LAG = [1, 0, 0, 1, 0, 0]


def build(f, i):
    c = {}
    b = f["b"]
    hip_n, hip_f = (16, 26 - b), (15, 26 - b)
    sh = (15, 21 - b)
    outline(leg(hip_f, f["ff"], False, f["fl"]), c)
    if f["fh"][0] < 13 or f["fh"][0] > 18:
        outline(arm(sh, (f["fh"][0], f["fh"][1] - b), False), c)
    outline(torso(b, f["flap"]), c)
    outline(leg(hip_n, f["nf"], True, f["nl"]), c)
    outline(arm(sh, (f["nh"][0], f["nh"][1] - b), True), c, inner=d_)
    for (x, y), col in HEAD.items():
        dy = -b + (PONY_LAG[i] if (x, y) in PONY else 0)
        c[(x, y + dy)] = col
    return c


frames = [build(f, i) for i, f in enumerate(CYCLE)]
DUR = [80] * len(frames)


def render(L):
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for (x, y), col in L.items():
        if 0 <= x < 32 and 0 <= y < 32:
            img.putpixel((x, y), col + (255,))
    return img


imgs = [render(L) for L in frames]
N = len(imgs)
sheet = Image.new("RGBA", (32 * N, 32), (0, 0, 0, 0))
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


fb = []
for f, (im, dur) in enumerate(zip(imgs, DUR)):
    ch = []
    if f == 0:
        ch += orig_chunks((0x2007, 0x2019))
        ch.append(chunk(0x2004, struct.pack("<HHHHHHB3x", 3, 0, 0, 0, 0, 0, 255) + astr("Eros")))
        ch.append(chunk(0x2018, struct.pack("<H8x", 1) +
                        struct.pack("<HHBH6x3Bx", 0, N - 1, 0, 0, 80, 160, 255) + astr("run_right")))
    bb = im.getbbox()
    cr = im.crop(bb)
    ch.append(chunk(0x2005, struct.pack("<HhhBHh5x", 0, bb[0], bb[1], 255, 2, 0) +
                    struct.pack("<HH", cr.width, cr.height) + zlib.compress(cr.tobytes())))
    body = b"".join(ch)
    fb.append(struct.pack("<IHHH2xI", 16 + len(body), 0xF1FA, len(ch), dur, len(ch)) + body)
allf = b"".join(fb)
hdr = bytearray(ORIG[:128])
struct.pack_into("<IHHHHH", hdr, 0, 128 + len(allf), 0xA5E0, N, 32, 32, 32)
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


S = 6
gif = []
for t in range(N * 3):
    b = backdrop(32, 32, t * 4)
    shadow(b, 16, 29, 6)
    b.alpha_composite(imgs[t % N])
    gif.append(b.convert("RGB").resize((32 * S, 32 * S), Image.NEAREST))
gif[0].save(os.path.join(OUT, "preview_run_x6.gif"), save_all=True, append_images=gif[1:],
            duration=80, loop=0)

strip = backdrop(32 * N, 32)
strip.alpha_composite(sheet)
strip.resize((32 * N * 8, 32 * 8), Image.NEAREST).save(os.path.join(OUT, "run_strip_x8.png"))
print("ok", N)
