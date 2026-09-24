"""Héros : marche avec épée + attaque à l'épée avec VFX (monstre à droite).

Entrée  : HERO_walk_right.aseprite (32x32, 4 frames)
Sorties : voir README.md
"""
import math
import os
import struct
import zlib

from PIL import Image

from read_ase import load

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "HERO_walk_right.aseprite")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------ palette du perso
O = (0, 0, 0)
s_ = (242, 233, 190)
P_ = (222, 174, 148)
r_ = (148, 43, 65)
R_ = (117, 31, 45)
q_ = (193, 51, 75)
k_ = (32, 45, 50)
W_ = (255, 255, 255)
y_ = (232, 191, 123)
l_ = (195, 150, 88)
h_ = (130, 86, 43)
H_ = (76, 50, 27)
b_ = (49, 110, 196)

# lame
BL1 = (240, 248, 255)
BL2 = (150, 172, 204)
BL3 = (104, 122, 160)
# VFX (énergie cyan, cohérente avec la chambre)
FX0 = (255, 255, 255)
FX1 = (206, 255, 255)
FX2 = (92, 228, 240)
FX3 = (30, 156, 196)
FX4 = (22, 88, 150)
SPK = (255, 226, 120)
SPK2 = (255, 160, 64)
DU1 = (190, 198, 214)
DU2 = (132, 142, 170)

frames_src, _ = load(SRC)


def grid(img):
    g = {}
    for y in range(img.height):
        for x in range(img.width):
            p = img.getpixel((x, y))
            if p[3]:
                g[(x, y)] = p[:3]
    return g


F = [grid(f) for f in frames_src]


def is_head(x, y, i):
    bob = 1 if i in (1, 3) else 0
    return y <= 19 - bob or (y <= 20 - bob and x < 10)


HEAD = {p: c for p, c in F[0].items() if is_head(*p, 0)}
BODY = [{p: c for p, c in F[i].items() if not is_head(*p, i)} for i in range(4)]
HAND = {0: (15, 24), 1: (13, 23), 2: (15, 24), 3: (16, 23)}   # coin haut-gauche de la main


def hand_px(x, y):
    return {(x, y): s_, (x + 1, y): s_, (x, y + 1): P_, (x + 1, y + 1): P_}


# torse de la frame 3 sans le bras (coordonnées frame 3, x10..)
TORSO_NOARM_ROWS = {
    19: "...#qqR###",
    20: "...#RRrrk.",
    21: "..#rRRrrk.",
    22: "..#rrRrryR",
    23: "..#rrRrrWR",
    24: ".#rrrRrryR",
    25: ".#rrrRRrrR",
}
CMAP = {"#": O, "s": s_, "P": P_, "r": r_, "R": R_, "q": q_, "k": k_, "W": W_,
        "y": y_, "l": l_, "h": h_, "H": H_, "b": b_}


def rows_to_px(rows, x0):
    d = {}
    for y, row in rows.items():
        for i, ch in enumerate(row):
            if ch != ".":
                d[(x0 + i, y)] = CMAP[ch]
    return d


TORSO_NOARM = rows_to_px(TORSO_NOARM_ROWS, 10)
LEGS3 = {p: c for p, c in BODY[3].items() if p[1] >= 26}

# bras tendu vers l'avant (coord. frame 3)
ARM_FWD = rows_to_px({
    20: "......kkk###",
    21: ".....rqqqRss#",
    22: ".....RrrrRPP#",
    23: ".....kkkk###",
}, 10)
HAND_FWD = (20, 21)

# bras levé vers l'avant-haut (coord. frame 3)
ARM_UP = rows_to_px({
    18: "...........##",
    19: "........kk#ss#",
    20: "......kqqRRPP#",
    21: ".....rqrrR###",
    22: ".....RrRkk",
    23: ".....kkk",
}, 10)
HAND_UP = (21, 19)


# ------------------------------------------------------------ épée
def axis(p0, n, sx, sy, count, phase=0, major="x"):
    pts = []
    for i in range(count):
        if major == "x":
            pts.append((p0[0] + i * sx, p0[1] + ((i + phase) // n) * sy))
        else:
            pts.append((p0[0] + ((i + phase) // n) * sx, p0[1] + i * sy))
    return pts


def sword(ax, second, perp, hide_pommel=False, glow=False):
    """ax: points de l'axe (pommeau->pointe). second: décalage de la 2e ligne de lame.
    perp: vecteur perpendiculaire pour la garde."""
    px = {}
    if not hide_pommel:
        px[ax[0]] = y_
    px[ax[1]] = H_
    px[ax[2]] = h_
    g = ax[3]
    px[g] = b_
    px[(g[0] + perp[0], g[1] + perp[1])] = y_
    px[(g[0] - perp[0], g[1] - perp[1])] = l_
    blade = ax[4:]
    for i, p in enumerate(blade):
        last = i == len(blade) - 1
        px[p] = FX1 if glow else BL1
        if not last:
            q = (p[0] + second[0], p[1] + second[1])
            px[q] = (FX2 if glow else (BL3 if i == 0 else BL2))
    out = {}
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px:
                out[q] = O
    out.update(px)
    return out


def sword_low(hx, hy):
    ax = axis((hx - 1, hy), 3, 1, 1, 13, phase=1)
    return sword(ax, (0, 1), (0, 1))


# ------------------------------------------------------------ calques
def put(layer, pts, dx=0, dy=0):
    for (x, y), c in pts.items():
        layer[(x + dx, y + dy)] = c


def render(layer, w, h, ox=0, oy=0):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in layer.items():
        X, Y = x + ox, y + oy
        if 0 <= X < w and 0 <= Y < h:
            img.putpixel((X, Y), c + (255,) if len(c) == 3 else c)
    return img


# ------------------------------------------------------------ 1) marche avec épée
walk = []
for i in range(4):
    L = {}
    put(L, BODY[i])
    put(L, HEAD, 0, -1 if i in (1, 3) else 0)
    hx, hy = HAND[i]
    put(L, sword_low(hx, hy))
    put(L, hand_px(hx, hy))
    walk.append(L)


# ------------------------------------------------------------ VFX helpers
def crescent(L, cx, cy, r_out, in_dx, r_in, th_tail, th_head, dither_tail=0.35,
             darken=0, head_taper=0.10, tail_taper=0.45):
    """Croissant de slash. Angles en degrés (0 = droite, + = bas)."""
    span = th_head - th_tail
    for y in range(int(cy - r_out - 1), int(cy + r_out + 2)):
        for x in range(int(cx - r_out - 1), int(cx + r_out + 2)):
            ddx, ddy = x - cx, y - cy
            d = math.hypot(ddx, ddy)
            if d > r_out or d < 1:
                continue
            th = math.degrees(math.atan2(ddy, ddx))
            t = (th - th_tail) / span
            if not 0 <= t <= 1:
                continue
            ux = ddx / d
            a = ux * in_dx
            disc = a * a - (in_dx * in_dx - r_in * r_in)
            if disc < 0:
                continue
            di = a + math.sqrt(disc)
            w = r_out - di
            if w <= 0:
                continue
            taper = min(1.0, t / tail_taper, (1 - t) / head_taper if head_taper else 1)
            allowed = w * max(0.0, taper)
            u = r_out - d
            if u > allowed:
                continue
            ratio = u / max(allowed, 1)
            idx = 0 if ratio < 0.18 else 1 if ratio < 0.38 else 2 if ratio < 0.62 else 3 if ratio < 0.85 else 4
            if t < 0.5:
                idx += 1
            if t < 0.22:
                idx += 1
            idx += darken
            if t < dither_tail and (x + y) % 2 == 0:
                continue
            if idx > 4:
                if (x + 2 * y) % 3:
                    continue
                idx = 4
            L[(x, y)] = (FX0, FX1, FX2, FX3, FX4)[idx]


def star(L, x, y, arm, cols, diag=0, dcols=None):
    L[(x, y)] = cols[0]
    for i in range(1, arm + 1):
        c = cols[min(len(cols) - 1, i * len(cols) // (arm + 1))]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            L[(x + dx * i, y + dy * i)] = c
    dcols = dcols or cols[1:]
    for i in range(1, diag + 1):
        c = dcols[min(len(dcols) - 1, i - 1)]
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            L[(x + dx * i, y + dy * i)] = c


def disc(L, x, y, r, c):
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            if i * i + j * j <= r * r + r * 0.8:
                L[(x + i, y + j)] = c


def ring(L, x, y, r, c, gap=0):
    n = int(2 * math.pi * r * 1.6)
    for k in range(n):
        if gap and k % gap == 0:
            continue
        a = 2 * math.pi * k / n
        L[(round(x + r * math.cos(a)), round(y + r * math.sin(a)))] = c


def ray(L, x, y, ang, r0, r1, cols):
    a = math.radians(ang)
    n = max(1, int(r1 - r0))
    for i in range(n + 1):
        rr = r0 + i
        c = cols[min(len(cols) - 1, i * len(cols) // (n + 1))]
        L[(round(x + rr * math.cos(a)), round(y + rr * math.sin(a)))] = c


def puff(L, x, y, r):
    disc(L, x, y, r, DU2)
    disc(L, x, y - 1 if r > 1 else y, max(0, r - 1), DU1)


def clean(L):
    """retire les pixels isolés"""
    for p in list(L):
        n = sum((p[0] + dx, p[1] + dy) in L for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                if dx or dy)
        if n == 0:
            del L[p]


# ------------------------------------------------------------ 2) attaque
AW, AH = 64, 64
BX, BY = 10, 30          # position du canevas 32x32 d'origine dans la frame 64x64
IMPACT = (40, 19)        # point d'impact (coord. perso)
SC = (19, 16)            # centre de rotation du slash (coord. perso)

atk_hero, atk_fx, atk_dur = [], [], []


def frame(hero, fx, dur):
    atk_hero.append(hero)
    atk_fx.append(fx)
    atk_dur.append(dur)


# A0 garde
Hh = {}
put(Hh, walk[0])
frame(Hh, {}, 140)

# A1 anticipation : recul, épée armée vers l'arrière-bas
def anticip(glint):
    Hh = {}
    hx, hy = HAND[1]
    dx = -1
    ax = axis((hx + 2, hy), 3, -1, 1, 13, phase=1)
    put(Hh, BODY[1], dx, 0)
    put(Hh, HEAD, dx, 0)
    put(Hh, sword(ax, (0, 1), (0, 1)), dx, 0)
    put(Hh, hand_px(hx, hy), dx, 0)
    fx = {}
    tip = ax[-1]
    if glint:
        star(fx, tip[0] + dx, tip[1], 3, (FX0, FX0, FX1, FX2), diag=1, dcols=(FX1,))
        fx[(ax[8][0] + dx, ax[8][1])] = FX0
    else:
        fx[(tip[0] + dx, tip[1])] = FX1
    return Hh, fx


frame(*anticip(False), 110)
frame(*anticip(True), 90)

# A3 smear : fente vers l'avant, lame à mi-course
Hh, fx = {}, {}
dx = 2
put(Hh, BODY[3], dx, 0)
put(Hh, HEAD, dx, -1)
hx, hy = HAND[3]
ax = axis((hx - 1, hy), 2, 1, 1, 11)
crescent(fx, SC[0], SC[1] + 1, 17, -4, 15, 118, 34, dither_tail=0.45, head_taper=0.0)
put(Hh, sword(ax, (0, 1), (0, 1), glow=True), dx, 0)
put(Hh, hand_px(hx, hy), dx, 0)
for i, yy in enumerate((22, 25, 27)):
    for xx in range(4 - i, 9 - i):
        if (xx + yy) % 3:
            fx[(xx, yy)] = FX3 if xx < 6 - i else FX2
puff(fx, 11, 28, 1)
clean(fx)
frame(Hh, fx, 50)


def lunge_body(Hh, dx):
    put(Hh, LEGS3, dx - 1, 0)
    put(Hh, TORSO_NOARM, dx, 0)
    put(Hh, HEAD, dx, -1)


# A4 impact
Hh, fx = {}, {}
dx = 3
lunge_body(Hh, dx)
put(Hh, ARM_FWD, dx, 0)
ax = axis((19, 21), 999, 1, 0, 14)
put(Hh, sword(ax, (0, 1), (0, 1), hide_pommel=True, glow=True), dx, 0)
put(Hh, hand_px(*HAND_FWD), dx, 0)
crescent(fx, *SC, 23, -5, 21, 78, -72, head_taper=0.14, tail_taper=0.35)
ix, iy = IMPACT
disc(fx, ix, iy, 3, FX1)
disc(fx, ix, iy, 2, FX0)
star(fx, ix, iy, 9, (FX0, FX0, FX1, FX1, FX2, FX3), diag=4, dcols=(FX0, FX1, FX2, FX3))
for ang, r0, r1 in ((-60, 5, 9), (-25, 6, 11), (20, 5, 10), (55, 6, 9), (-100, 6, 8)):
    ray(fx, ix, iy, ang, r0, r1, (SPK, SPK, SPK2))
puff(fx, 9, 28, 2)
puff(fx, 6, 27, 1)
clean(fx)
frame(Hh, fx, 110)

# A5 suite du geste : lame vers l'avant-haut, slash qui s'amincit
Hh, fx = {}, {}
dx = 3
lunge_body(Hh, dx)
put(Hh, ARM_UP, dx, 0)
ax = axis((20, 21), 1, 1, -1, 12)
put(Hh, sword(ax, (1, 0), (1, 1)), dx, 0)
put(Hh, hand_px(*HAND_UP), dx, 0)
crescent(fx, *SC, 23, -5, 21, 40, -96, darken=1, dither_tail=0.55, head_taper=0.18)
ring(fx, ix, iy, 5, FX2)
ring(fx, ix, iy, 4, FX1, gap=3)
fx[(ix, iy)] = FX0
for ang, r0, r1 in ((-60, 9, 12), (-25, 11, 14), (20, 10, 13), (55, 9, 11), (-100, 8, 10)):
    ray(fx, ix, iy, ang, r0, r1, (SPK, SPK2))
puff(fx, 7, 27, 2)
puff(fx, 3, 26, 1)
clean(fx)
frame(Hh, fx, 90)

# A6 dissipation : on revient, particules
Hh, fx = {}, {}
dx = 1
put(Hh, BODY[0], dx, 0)
put(Hh, HEAD, dx, 0)
hx, hy = HAND[0]
put(Hh, sword_low(hx, hy), dx, 0)
put(Hh, hand_px(hx, hy), dx, 0)
crescent(fx, *SC, 23, -4, 21, -30, -104, darken=2, dither_tail=1.0, head_taper=0.3)
for (px_, py_, c) in ((31, 6, FX2), (35, 9, FX1), (38, 13, FX2), (40, 18, FX3), (36, 3, FX3),
                      (42, 24, FX2), (29, 2, FX3), (44, 15, FX3)):
    fx[(px_, py_)] = c
ring(fx, ix, iy, 7, FX3, gap=2)
for ang, r in ((-60, 13), (-25, 15), (20, 14), (55, 12)):
    a = math.radians(ang)
    fx[(round(ix + r * math.cos(a)), round(iy + r * math.sin(a)))] = SPK2
puff(fx, 4, 26, 1)
frame(Hh, fx, 90)

# A7 retour en garde
Hh, fx = {}, {}
put(Hh, walk[0])
for (px_, py_, c) in ((33, 4, FX3), (41, 11, FX3), (45, 21, FX3)):
    fx[(px_, py_)] = c
frame(Hh, fx, 120)


# ------------------------------------------------------------ export PNG
S = 4


def up(img, s=S):
    return img.resize((img.width * s, img.height * s), Image.NEAREST)


def sheet(imgs, w, h):
    sh = Image.new("RGBA", (w * len(imgs), h), (0, 0, 0, 0))
    for i, im in enumerate(imgs):
        sh.alpha_composite(im, (i * w, 0))
    return sh


walk_imgs = [render(L, 32, 32) for L in walk]
sheet(walk_imgs, 32, 32).save(os.path.join(OUT, "hero_walk_sword_right.png"))

hero_imgs = [render(L, AW, AH, BX, BY) for L in atk_hero]
fx_imgs = [render(L, AW, AH, BX, BY) for L in atk_fx]
full_imgs = []
for hi, fi in zip(hero_imgs, fx_imgs):
    im = hi.copy()
    im.alpha_composite(fi)
    full_imgs.append(im)
sheet(full_imgs, AW, AH).save(os.path.join(OUT, "hero_attack_right.png"))
sheet(hero_imgs, AW, AH).save(os.path.join(OUT, "hero_attack_right_body.png"))
sheet(fx_imgs, AW, AH).save(os.path.join(OUT, "hero_attack_right_vfx.png"))


# ------------------------------------------------------------ effet d'impact seul (à poser sur le monstre)
hit_imgs = []
for k in range(4):
    L = {}
    c = (16, 16)
    if k == 0:
        disc(L, *c, 4, FX1)
        disc(L, *c, 3, FX0)
        star(L, *c, 10, (FX0, FX0, FX1, FX1, FX2, FX3), diag=5, dcols=(FX0, FX1, FX2, FX3))
    elif k == 1:
        disc(L, *c, 2, FX0)
        ring(L, *c, 6, FX2)
        ring(L, *c, 5, FX1, gap=3)
        star(L, *c, 4, (FX0, FX1, FX2))
        for ang in (-60, -20, 25, 70, 150, 200, 245):
            ray(L, *c, ang, 7, 10, (SPK, SPK2))
    elif k == 2:
        ring(L, *c, 9, FX3, gap=2)
        ring(L, *c, 8, FX2, gap=4)
        for ang in (-60, -20, 25, 70, 150, 200, 245):
            ray(L, *c, ang, 11, 13, (SPK2,))
    else:
        for ang in (-50, 10, 80, 160, 230, 290):
            a = math.radians(ang)
            L[(round(16 + 12 * math.cos(a)), round(16 + 12 * math.sin(a)))] = FX3
    hit_imgs.append(render(L, 32, 32))
sheet(hit_imgs, 32, 32).save(os.path.join(OUT, "hit_fx.png"))


# ------------------------------------------------------------ export .aseprite
ORIG = open(SRC, "rb").read()


def orig_chunks(types):
    off = 128 + 16
    fsize = struct.unpack_from("<I", ORIG, 128)[0]
    res = []
    while off < 128 + fsize:
        csize, ctype = struct.unpack_from("<IH", ORIG, off)
        if ctype in types:
            res.append(ORIG[off:off + csize])
        off += csize
    return res


def ase_string(s):
    b = s.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def chunk(ctype, data):
    return struct.pack("<IH", len(data) + 6, ctype) + data


def layer_chunk(name):
    return chunk(0x2004, struct.pack("<HHHHHHB3x", 3, 0, 0, 0, 0, 0, 255) + ase_string(name))


def cel_chunk(li, img):
    bbox = img.getbbox()
    if not bbox:
        return None
    crop = img.crop(bbox)
    data = struct.pack("<HhhBHh5x", li, bbox[0], bbox[1], 255, 2, 0)
    data += struct.pack("<HH", crop.width, crop.height) + zlib.compress(crop.tobytes())
    return chunk(0x2005, data)


def tags_chunk(tags):
    data = struct.pack("<H8x", len(tags))
    for name, a, b, col in tags:
        data += struct.pack("<HHBH6x3Bx", a, b, 0, 0, *col) + ase_string(name)
    return chunk(0x2018, data)


def write_ase(path, w, h, layers, durs, tags):
    """layers: [(nom, [images par frame])]"""
    frames_bytes = []
    for f, dur in enumerate(durs):
        chunks = []
        if f == 0:
            chunks += orig_chunks((0x2007, 0x2019))
            chunks += [layer_chunk(n) for n, _ in layers]
            if tags:
                chunks.append(tags_chunk(tags))
        for li, (_, imgs) in enumerate(layers):
            c = cel_chunk(li, imgs[f])
            if c:
                chunks.append(c)
        body = b"".join(chunks)
        hdr = struct.pack("<IHHH2xI", 16 + len(body), 0xF1FA, min(len(chunks), 0xFFFF),
                          dur, len(chunks))
        frames_bytes.append(hdr + body)
    allf = b"".join(frames_bytes)
    header = bytearray(ORIG[:128])
    struct.pack_into("<IHHHHH", header, 0, 128 + len(allf), 0xA5E0, len(durs), w, h, 32)
    with open(path, "wb") as fh:
        fh.write(bytes(header) + allf)


write_ase(os.path.join(OUT, "HERO_walk_sword_right.aseprite"), 32, 32,
          [("Hero", walk_imgs)], [100] * 4, [("walk_sword_right", 0, 3, (80, 160, 255))])
write_ase(os.path.join(OUT, "HERO_attack_right.aseprite"), AW, AH,
          [("Hero", hero_imgs), ("VFX", fx_imgs)], atk_dur,
          [("attack_right", 0, len(atk_dur) - 1, (255, 90, 120))])
write_ase(os.path.join(OUT, "hit_fx.aseprite"), 32, 32,
          [("VFX", hit_imgs)], [60, 70, 70, 70], [("hit", 0, 3, (92, 228, 240))])


# ------------------------------------------------------------ aperçus GIF (avec un slime cible)
def slime(flash=False, squash=0):
    L = {}
    cx, base, rx, ry = 0, 0, 9 + squash, 7 - squash
    body = set()
    for y in range(-2 * ry, 1):
        for x in range(-rx - 1, rx + 2):
            yy = (y + ry) / ry
            if (x / (rx + 0.5)) ** 2 + yy ** 2 <= 1 or (y > -3 and abs(x) <= rx):
                body.add((x, y))
    for (x, y) in body:
        for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx_, y + dy_) not in body:
                L[(x + dx_, y + dy_)] = O
    for (x, y) in body:
        if flash:
            L[(x, y)] = FX0
            continue
        t = (y + 2 * ry) / (2 * ry)
        c = (126, 222, 118) if t < 0.3 else (38, 146, 88) if t < 0.8 else (18, 96, 64)
        if x > rx - 3 and t > 0.3:
            c = (18, 96, 64)
        L[(x, y)] = c
    if not flash:
        for (x, y) in ((-5, -2 * ry + 3), (-4, -2 * ry + 3), (-5, -2 * ry + 4)):
            L[(x, y)] = W_
        for ex in (-4, 2):
            L[(ex, -ry)] = O
            L[(ex, -ry + 1)] = O
            L[(ex, -ry - 1)] = W_ if ex < 0 else O
    return L


FLOOR = [(58, 66, 108), (54, 61, 101)]


def backdrop(w, h):
    bg = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    for y in range(h):
        for x in range(w):
            tx, ty = x // 16, y // 16
            c = FLOOR[(tx + ty) % 2]
            lx, ly = x % 16, y % 16
            if lx == 15 or ly == 15:
                c = (36, 40, 70)
            elif lx == 0 or ly == 0:
                c = (78, 90, 136)
            bg.putpixel((x, y), c + (255,))
    return bg


def shadow(img, cx, cy, rx):
    for x in range(cx - rx, cx + rx + 1):
        for yy in (cy, cy + 1):
            if 0 <= x < img.width and 0 <= yy < img.height:
                p = img.getpixel((x, yy))
                img.putpixel((x, yy), tuple(int(v * 0.6) for v in p[:3]) + (255,))


PW, PH = 96, 64
SX = 60   # x du slime
bg = backdrop(PW, PH)
gif_frames, gif_durs = [], []
# 4 frames de marche puis 2 cycles d'attaque
slime_state = {4: (True, 1, 2), 5: (False, 1, 2), 6: (False, 0, 1)}
for loop in range(2):
    for i, (hi, fi, d) in enumerate(zip(hero_imgs, fx_imgs, atk_dur)):
        im = bg.copy()
        flash, sq, kb = slime_state.get(i, (False, 0, 0))
        shadow(im, BX + 16, BY + 29, 7)
        shadow(im, SX + kb, 60, 9)
        sl = render(slime(flash, sq), PW, PH, SX + kb, 59)
        im.alpha_composite(sl)
        im.alpha_composite(hi, (0, 0))
        im.alpha_composite(fi, (0, 0))
        gif_frames.append(im)
        gif_durs.append(d)
    im = bg.copy()
    shadow(im, BX + 16, BY + 29, 7)
    shadow(im, SX, 60, 9)
    im.alpha_composite(render(slime(), PW, PH, SX, 59))
    im.alpha_composite(hero_imgs[0])
    gif_frames.append(im)
    gif_durs.append(400)


def save_gif(path, imgs, durs, s=S):
    ims = [up(i.convert("RGB"), s) for i in imgs]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0,
                disposal=2, optimize=False)


save_gif(os.path.join(OUT, "preview_attack_x4.gif"), gif_frames, gif_durs)

wbg = backdrop(32, 32)
wf = []
for im in walk_imgs:
    b = wbg.copy()
    shadow(b, 16, 29, 6)
    b.alpha_composite(im)
    wf.append(b)
save_gif(os.path.join(OUT, "preview_walk_sword_x6.gif"), wf, [110] * 4, 6)

# planche de contrôle (x4)
strip = Image.new("RGBA", (AW * len(full_imgs), AH), (0, 0, 0, 255))
for i, im in enumerate(full_imgs):
    b = backdrop(AW, AH)
    b.alpha_composite(im)
    strip.paste(b, (i * AW, 0))
up(strip).save(os.path.join(OUT, "attack_strip_x4.png"))
print("ok", len(atk_dur), "frames d'attaque")
