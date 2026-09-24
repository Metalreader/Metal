"""Relaeh : coup de poing (dash-punch) avec VFX vers un monstre à droite.

Entrée  : RELAEH_walk_right.aseprite (32x32, 4 frames)
Sorties : out/ (voir README.md)
"""
import math
import os
import struct
import zlib

from PIL import Image

from read_ase import load

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "RELAEH_walk_right.aseprite")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------ palette du perso
O = (0, 0, 0)
c_ = (242, 204, 179)
e_ = (222, 174, 148)
o_ = (201, 143, 112)
h_ = (116, 73, 56)
f_ = (32, 45, 50)
i_ = (44, 62, 68)
g_ = (120, 36, 28)
j_ = (157, 47, 37)
n_ = (126, 95, 22)
l_ = (28, 65, 84)
m_ = (37, 86, 111)
r_ = (20, 48, 61)
k_ = (255, 255, 255)
p_ = (199, 214, 219)

# VFX : énergie de frappe orange/rouge
E0 = (255, 255, 255)
E1 = (255, 242, 170)
E2 = (255, 206, 84)
E3 = (255, 140, 46)
E4 = (226, 64, 42)
E5 = (130, 28, 36)
SM1 = (176, 170, 178)
SM2 = (118, 112, 126)
SM3 = (74, 70, 84)

CMAP = {"#": O, "c": c_, "e": e_, "o": o_, "h": h_, "f": f_, "i": i_, "g": g_,
        "j": j_, "n": n_, "l": l_, "m": m_, "r": r_, "k": k_, "p": p_}

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
    b = 1 if i in (1, 3) else 0
    return y <= 16 - b or (y == 17 - b and (x <= 13 or x >= 17))


HEAD = {p: c for p, c in F[0].items() if is_head(*p, 0)}
BODY = [{p: c for p, c in F[i].items() if not is_head(*p, i)} for i in range(4)]


def rows_to_px(rows, x0):
    d = {}
    for y, row in rows.items():
        for i, ch in enumerate(row):
            if ch != ".":
                d[(x0 + i, y)] = CMAP[ch]
    return d


# torse de la frame 3 sans le bras ni la main (coord. frame 3, x à partir de 9)
TORSO_NOARM = rows_to_px({
    17: "...#nnnn#g#",
    18: "...#fiijjjg#",
    19: "...#ffijjjg#",
    20: "...#ffijjjg#",
    21: "....#ffgjgg#",
    22: "....##ff#mm#",
    23: "...#mll#mmml#",
    24: "..#mmmlmmmml##",
    25: ".#lmmmmmmmr#p#",
}, 9)
LEGS3 = {p: c for p, c in BODY[3].items() if p[1] >= 26}

# bras tendu + poing (coord. frame 3)
ARM_PUNCH = rows_to_px({
    18: "......##########",
    19: ".....iiiiiiin#cce#",
    20: ".....fiiiiffn#ceeo#",
    21: ".....ffffffnn#eooh#",
    22: "......#######h##hh#",
    23: "..............####",
}, 9)
FIST_PUNCH = (23, 19)    # coin haut-gauche du poing
# bras à mi-course (smear)
ARM_MID = rows_to_px({
    19: "......#######",
    20: ".....iiiiin#ce#",
    21: ".....fffffn#eeo#",
    22: "......#####hoh#",
    23: "...........###",
}, 9)


# ------------------------------------------------------------ calques
def put(layer, pts, dx=0, dy=0):
    for (x, y), c in pts.items():
        layer[(x + dx, y + dy)] = c


def render(layer, w, h, ox=0, oy=0):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in layer.items():
        X, Y = x + ox, y + oy
        if 0 <= X < w and 0 <= Y < h:
            img.putpixel((X, Y), c + (255,))
    return img


# ------------------------------------------------------------ VFX helpers
def disc(L, x, y, r, c):
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            if i * i + j * j <= r * r + r * 0.8:
                L[(x + i, y + j)] = c


def oval_ring(L, x, y, rx, ry, c, gap=0, arc=None):
    n = int(2 * math.pi * max(rx, ry) * 1.8)
    for k in range(n):
        if gap and k % gap == 0:
            continue
        a = 2 * math.pi * k / n
        deg = math.degrees(a)
        deg = deg - 360 if deg > 180 else deg
        if arc and not arc[0] <= deg <= arc[1]:
            continue
        L[(round(x + rx * math.cos(a)), round(y + ry * math.sin(a)))] = c


def ray(L, x, y, ang, r0, r1, cols):
    a = math.radians(ang)
    n = max(1, int(r1 - r0))
    for i in range(n + 1):
        rr = r0 + i
        c = cols[min(len(cols) - 1, i * len(cols) // (n + 1))]
        L[(round(x + rr * math.cos(a)), round(y + rr * math.sin(a)))] = c


def burst(L, cx, cy, radii, rot=0, sx=1.0, cols=(E0, E1, E2, E3, E4)):
    """étoile d'impact à pointes (rayons alternés), remplie en dégradé"""
    n = len(radii)
    pts = []
    for k, r in enumerate(radii):
        a = math.radians(rot + k * 360 / n)
        pts.append((cx + r * math.cos(a) * sx, cy + r * math.sin(a)))
    R = max(radii)
    for y in range(int(cy - R - 1), int(cy + R + 2)):
        for x in range(int(cx - R * sx - 1), int(cx + R * sx + 2)):
            inside = False
            for a_, b_ in zip(pts, pts[1:] + pts[:1]):
                if (a_[1] > y) != (b_[1] > y):
                    xi = a_[0] + (y - a_[1]) * (b_[0] - a_[0]) / (b_[1] - a_[1])
                    if x < xi:
                        inside = not inside
            if not inside:
                continue
            ang = math.degrees(math.atan2(y - cy, (x - cx) / sx)) - rot
            k = (ang % 360) / (360 / n)
            k0 = int(k) % n
            t = k - int(k)
            edge = radii[k0] * (1 - t) + radii[(k0 + 1) % n] * t
            d = math.hypot((x - cx) / sx, y - cy) / max(edge, 1)
            idx = 0 if d < 0.34 else 1 if d < 0.52 else 2 if d < 0.7 else 3 if d < 0.87 else 4
            L[(x, y)] = cols[min(idx, len(cols) - 1)]


def puff(L, x, y, r, dark=False):
    disc(L, x, y, r, SM3 if dark else SM2)
    if r > 1:
        disc(L, x - 1, y - 1, r - 1, SM2 if dark else SM1)
    else:
        L[(x - 1, y - 1)] = SM1


def speed_lines(L, rows, x0, x1, cols=(E3, E2, E1)):
    for (y, a, b) in rows:
        for x in range(x0 + a, x1 - b):
            t = (x - x0 - a) / max(1, (x1 - b) - (x0 + a))
            if t < 0.3 and x % 2:
                continue
            L[(x, y)] = cols[min(len(cols) - 1, int(t * len(cols)))]


def glow_outline(L, pts, cols=(E3, E2)):
    for (x, y) in list(pts):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in pts:
                L[q] = cols[(q[0] + q[1]) % len(cols)]


# ------------------------------------------------------------ poses
AW, AH = 64, 64
BX, BY = 10, 30         # même ancrage que l'attaque du héros

atk_hero, atk_fx, atk_dur = [], [], []


def frame(hero, fx, dur):
    atk_hero.append(hero)
    atk_fx.append(fx)
    atk_dur.append(dur)


def idle(dx=0):
    Hh = {}
    put(Hh, BODY[0], dx, 0)
    put(Hh, HEAD, dx, 0)
    return Hh


def lunge(Hh, dx, arm):
    put(Hh, LEGS3, dx - 1, 0)
    put(Hh, TORSO_NOARM, dx, 0)
    put(Hh, HEAD, dx, -1)
    put(Hh, arm, dx, 0)


# F0 garde
frame(idle(), {}, 140)

# F1-F2 anticipation : recul, poing armé en arrière (frame 1), charge
FIST_BACK = [(x, y) for (x, y), c in BODY[1].items() if c in (c_, e_, o_) and y >= 23]


def anticip(charge):
    Hh, fx = {}, {}
    dx = -1
    put(Hh, BODY[1], dx, 0)
    put(Hh, HEAD, dx, 0)
    fist = {(x + dx, y) for (x, y) in FIST_BACK}
    fcx = sum(p[0] for p in fist) / len(fist)
    fcy = sum(p[1] for p in fist) / len(fist)
    if charge == 0:
        for ang, r in ((-40, 6), (60, 6), (170, 5), (250, 6)):
            a = math.radians(ang)
            fx[(round(fcx + r * math.cos(a)), round(fcy + r * math.sin(a)))] = E3
    else:
        for ang, r in ((-40, 4), (60, 4), (170, 3), (250, 4), (20, 5), (120, 5), (300, 5)):
            a = math.radians(ang)
            fx[(round(fcx + r * math.cos(a)), round(fcy + r * math.sin(a)))] = E2 if r < 5 else E3
        glow_outline(fx, {p for p in Hh if p in fist or (p[0], p[1]) in fist}, (E2, E3))
        for p in fist:
            Hh[p] = E1 if Hh[p] == c_ else Hh[p]
        fx[(round(fcx), round(fcy) - 4)] = E0
        fx[(round(fcx), round(fcy) - 5)] = E1
    return Hh, fx


frame(*anticip(0), 110)
frame(*anticip(1), 90)

# F3 smear : dash, bras qui part, traînée
Hh, fx = {}, {}
dx = 4
speed_lines(fx, ((19, 3, 0), (20, 0, 0), (21, 2, 0)), -2 + dx, 10 + dx, (E5, E4, E3, E2))
speed_lines(fx, ((13, 4, 3), (25, 2, 4), (8, 6, 5)), 0, 12, (SM3, SM2, SM1))
lunge(Hh, dx, ARM_MID)
glow_outline(fx, {(x + dx, y) for (x, y), c in ARM_MID.items() if c in (c_, e_, o_)}, (E2, E3))
puff(fx, 7, 28, 1)
frame(Hh, fx, 50)

# F4 impact
Hh, fx = {}, {}
dx = 6
lunge(Hh, dx, ARM_PUNCH)
IMPACT = (FIST_PUNCH[0] + 4 + dx, 20)
ix, iy = IMPACT
burst(fx, ix + 1, iy, [12, 5, 9, 4, 11, 5, 8, 4, 12, 5, 9, 4], rot=8, sx=0.85)
burst(fx, ix + 1, iy, [5, 3, 5, 3, 5, 3, 5, 3], rot=0, sx=0.85, cols=(E0, E0, E1, E1, E2))
oval_ring(fx, ix + 5, iy, 3, 10, E3, arc=(-80, 80))
oval_ring(fx, ix + 4, iy, 3, 10, E2, arc=(-60, 60))
for ang, r0, r1 in ((-70, 11, 15), (-35, 12, 17), (30, 11, 16), (65, 11, 14), (-115, 9, 12),
                    (110, 9, 12)):
    ray(fx, ix, iy, ang, r0, r1, (E1, E2, E3))
puff(fx, 9 + dx - 6, 28, 2, True)
puff(fx, 5 + dx - 6, 27, 1)
frame(Hh, fx, 120)

# F5 suite : l'étoile se résorbe, onde de choc qui s'étend
Hh, fx = {}, {}
lunge(Hh, dx, ARM_PUNCH)
burst(fx, ix + 1, iy, [6, 3, 5, 3, 6, 3, 5, 3], rot=22, sx=0.85, cols=(E1, E2, E3, E4, E5))
oval_ring(fx, ix + 7, iy, 4, 13, E4, arc=(-75, 75))
oval_ring(fx, ix + 6, iy, 4, 13, E3, gap=4, arc=(-60, 60))
oval_ring(fx, ix + 2, iy, 8, 8, E4, gap=3, arc=(-105, 105))
for ang, r0, r1 in ((-70, 15, 18), (-35, 17, 20), (30, 16, 19), (65, 14, 16), (-115, 12, 14),
                    (110, 12, 14)):
    ray(fx, ix, iy, ang, r0, r1, (E2, E3, E4))
puff(fx, ix - 1, iy - 7, 1)
puff(fx, ix + 2, iy + 6, 1)
puff(fx, 2, 27, 2, True)
frame(Hh, fx, 90)

# F6 retour : bras qui se replie, fumée et braises
Hh, fx = {}, {}
Hh = idle(3)
for (x, y, r, dk) in ((ix - 1, iy - 9, 2, False), (ix + 3, iy + 7, 2, True), (ix + 6, iy - 3, 1, False)):
    puff(fx, x, y, r, dk)
for ang, r in ((-70, 20), (-35, 22), (30, 21), (65, 17), (-115, 15)):
    a = math.radians(ang)
    fx[(round(ix + r * math.cos(a)), round(iy + r * math.sin(a)))] = E4
oval_ring(fx, ix + 9, iy, 4, 15, E5, gap=2, arc=(-70, 70))
frame(Hh, fx, 90)

# F7 garde
Hh, fx = idle(), {}
for (x, y, c) in ((ix, iy - 12, SM2), (ix + 4, iy + 9, SM3), (ix + 9, iy - 6, E5)):
    fx[(x, y)] = c
frame(Hh, fx, 120)


# ------------------------------------------------------------ effet d'impact seul (monstre)
hit_imgs = []
for k in range(4):
    L = {}
    c = (16, 16)
    if k == 0:
        burst(L, *c, [13, 5, 10, 4, 12, 5, 9, 4, 13, 5, 10, 4], rot=8)
        burst(L, *c, [5, 3, 5, 3, 5, 3, 5, 3], cols=(E0, E0, E1, E1, E2))
    elif k == 1:
        burst(L, *c, [7, 3, 6, 3, 7, 3, 6, 3], rot=22, cols=(E1, E2, E3, E4, E5))
        oval_ring(L, *c, 10, 10, E3, gap=4)
        for ang in (-60, -20, 25, 70, 150, 200, 245):
            ray(L, *c, ang, 11, 14, (E2, E3))
    elif k == 2:
        oval_ring(L, *c, 13, 13, E4, gap=2)
        puff(L, 12, 12, 2)
        puff(L, 20, 19, 1, True)
        for ang in (-60, -20, 25, 70, 150, 200, 245):
            ray(L, *c, ang, 14, 15, (E4,))
    else:
        puff(L, 11, 10, 1)
        puff(L, 21, 20, 1, True)
        for ang in (-50, 10, 80, 160, 230, 290):
            a = math.radians(ang)
            L[(round(16 + 14 * math.cos(a)), round(16 + 14 * math.sin(a)))] = E5
    hit_imgs.append(render(L, 32, 32))


# ------------------------------------------------------------ export PNG
S = 4


def up(img, s=S):
    return img.resize((img.width * s, img.height * s), Image.NEAREST)


def sheet(imgs, w, h):
    sh = Image.new("RGBA", (w * len(imgs), h), (0, 0, 0, 0))
    for i, im in enumerate(imgs):
        sh.alpha_composite(im, (i * w, 0))
    return sh


hero_imgs = [render(L, AW, AH, BX, BY) for L in atk_hero]
fx_imgs = [render(L, AW, AH, BX, BY) for L in atk_fx]
full_imgs = []
for hi, fi in zip(hero_imgs, fx_imgs):
    im = hi.copy()
    im.alpha_composite(fi)
    full_imgs.append(im)
sheet(full_imgs, AW, AH).save(os.path.join(OUT, "relaeh_punch_right.png"))
sheet(hero_imgs, AW, AH).save(os.path.join(OUT, "relaeh_punch_right_body.png"))
sheet(fx_imgs, AW, AH).save(os.path.join(OUT, "relaeh_punch_right_vfx.png"))
sheet(hit_imgs, 32, 32).save(os.path.join(OUT, "punch_hit_fx.png"))


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
    frames_bytes = []
    for f, dur in enumerate(durs):
        chunks = []
        if f == 0:
            chunks += orig_chunks((0x2007, 0x2019))
            chunks += [layer_chunk(n) for n, _ in layers]
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


write_ase(os.path.join(OUT, "RELAEH_punch_right.aseprite"), AW, AH,
          [("Relaeh", hero_imgs), ("VFX", fx_imgs)], atk_dur,
          [("punch_right", 0, len(atk_dur) - 1, (255, 140, 46))])
write_ase(os.path.join(OUT, "punch_hit_fx.aseprite"), 32, 32,
          [("VFX", hit_imgs)], [60, 70, 70, 70], [("punch_hit", 0, 3, (255, 140, 46))])


# ------------------------------------------------------------ aperçu GIF avec un slime cible
def slime(flash=False, squash=0):
    L = {}
    rx, ry = 9 + squash, 7 - squash
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
            L[(x, y)] = E0
            continue
        t = (y + 2 * ry) / (2 * ry)
        col = (126, 222, 118) if t < 0.3 else (38, 146, 88) if t < 0.8 else (18, 96, 64)
        if x > rx - 3 and t > 0.3:
            col = (18, 96, 64)
        L[(x, y)] = col
    if not flash:
        for (x, y) in ((-5, -2 * ry + 3), (-4, -2 * ry + 3), (-5, -2 * ry + 4)):
            L[(x, y)] = k_
        for ex in (-4, 2):
            L[(ex, -ry)] = O
            L[(ex, -ry + 1)] = O
            L[(ex, -ry - 1)] = k_ if ex < 0 else O
    return L


FLOOR = [(58, 66, 108), (54, 61, 101)]


def backdrop(w, h):
    bg = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    for y in range(h):
        for x in range(w):
            col = FLOOR[((x // 16) + (y // 16)) % 2]
            lx, ly = x % 16, y % 16
            if lx == 15 or ly == 15:
                col = (36, 40, 70)
            elif lx == 0 or ly == 0:
                col = (78, 90, 136)
            bg.putpixel((x, y), col + (255,))
    return bg


def shadow(img, cx, cy, rx):
    for x in range(cx - rx, cx + rx + 1):
        for yy in (cy, cy + 1):
            if 0 <= x < img.width and 0 <= yy < img.height:
                p = img.getpixel((x, yy))
                img.putpixel((x, yy), tuple(int(v * 0.6) for v in p[:3]) + (255,))


HERO_X = [0, -1, -1, 4, 6, 6, 3, 0]   # déplacement du perso par frame (pour l'ombre)
PW, PH = 88, 64
SX = 55
bg = backdrop(PW, PH)
gif_frames, gif_durs = [], []
slime_state = {4: (True, 1, 3), 5: (False, 1, 3), 6: (False, 0, 1)}
for loop in range(2):
    for i, (hi, fi, d) in enumerate(zip(hero_imgs, fx_imgs, atk_dur)):
        im = bg.copy()
        flash, sq, kb = slime_state.get(i, (False, 0, 0))
        shadow(im, BX + 16 + HERO_X[i], BY + 29, 6)
        shadow(im, SX + kb, 60, 9)
        im.alpha_composite(render(slime(flash, sq), PW, PH, SX + kb, 59))
        im.alpha_composite(hi)
        im.alpha_composite(fi)
        gif_frames.append(im)
        gif_durs.append(d)
    im = bg.copy()
    shadow(im, BX + 16, BY + 29, 6)
    shadow(im, SX, 60, 9)
    im.alpha_composite(render(slime(), PW, PH, SX, 59))
    im.alpha_composite(hero_imgs[0])
    gif_frames.append(im)
    gif_durs.append(400)

ims = [up(i.convert("RGB")) for i in gif_frames]
ims[0].save(os.path.join(OUT, "preview_punch_x4.gif"), save_all=True, append_images=ims[1:],
            duration=gif_durs, loop=0, disposal=2)

strip = Image.new("RGBA", (AW * len(full_imgs), AH), (0, 0, 0, 255))
for i, im in enumerate(full_imgs):
    b = backdrop(AW, AH)
    b.alpha_composite(im)
    strip.paste(b, (i * AW, 0))
up(strip).save(os.path.join(OUT, "punch_strip_x4.png"))
print("ok", len(atk_dur), "frames, impact (frame 64x64) =", (ix + BX, iy + BY))
