"""Chambre de départ — JRPG rétro-futuriste, tiles 16x16.

Génère :
  room.png          la pièce composée (taille native, 224x176)
  room_x4.png       la pièce agrandie x4 (pixels nets)
  room_grid_x4.png  idem avec la grille 16x16 superposée
  tileset.png       tiles uniques (taille native, prêt pour un moteur)
  tileset_x4.png    tileset agrandi x4
  map.json          la tilemap (indices dans tileset.png)
"""
import json
import os
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))
T = 16
TW, TH = 14, 11
W, H = TW * T, TH * T

# ---------------------------------------------------------------- palette
K0 = (10, 8, 20)        # contour
K1 = (20, 18, 38)
N1 = (30, 32, 60)
N2 = (46, 52, 88)
N3 = (64, 74, 118)
N4 = (88, 104, 150)
N5 = (122, 142, 184)
N6 = (174, 192, 222)
WH = (236, 242, 252)
C1 = (18, 70, 104)
C2 = (30, 156, 196)
C3 = (92, 228, 240)
C4 = (206, 255, 255)
M1 = (104, 28, 88)
M2 = (190, 48, 136)
M3 = (255, 112, 190)
A1 = (130, 66, 28)
A2 = (228, 138, 40)
A3 = (255, 212, 112)
G1 = (18, 74, 58)
G2 = (38, 146, 88)
G3 = (126, 222, 118)
GL = (10, 40, 30)
R2 = (230, 60, 72)

FA = (58, 66, 108)      # sol, teinte A
FB = (54, 61, 101)      # sol, teinte B
FH = (78, 90, 136)      # sol, reflet
FS = (36, 40, 70)       # sol, joint
FD = (26, 28, 52)

WT = (18, 16, 34)       # masse du mur (vue de dessus)
WT2 = (25, 23, 46)
WB = (44, 46, 84)       # face du mur
WB2 = (40, 42, 78)

img = Image.new("RGB", (W, H), K0)
P = img.load()


# ---------------------------------------------------------------- helpers
def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        P[x, y] = c


def rect(x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(x, y, c)


def hline(x0, x1, y, c):
    rect(x0, y, x1, y, c)


def vline(x, y0, y1, c):
    rect(x, y0, x, y1, c)


def mix(a, b, t):
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


def blend(x, y, c, a):
    if 0 <= x < W and 0 <= y < H:
        P[x, y] = mix(P[x, y], c, a)


def brect(x0, y0, x1, y1, c, a):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            blend(x, y, c, a)


def rrect(x0, y0, x1, y1, fill, line=K0):
    """Rectangle à coins coupés avec contour."""
    rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)
    hline(x0 + 1, x1 - 1, y0, line)
    hline(x0 + 1, x1 - 1, y1, line)
    vline(x0, y0 + 1, y1 - 1, line)
    vline(x1, y0 + 1, y1 - 1, line)


def ellipse_shadow(cx, cy, rx, ry, a=0.4):
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2
            if d <= 1:
                blend(x, y, K0, a if d < 0.55 else a * 0.6)


def sprite(x0, y0, rows, cmap, outline=None):
    pts = {}
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                pts[(x0 + i, y0 + j)] = cmap[ch]
    if outline:
        for (x, y) in list(pts):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in pts:
                    px(*q, outline)
    for (x, y), c in pts.items():
        px(x, y, c)


# ---------------------------------------------------------------- sol
def floor_tile(tx, ty, variant="plain"):
    x0, y0 = tx * T, ty * T
    base = FA if (tx + ty) % 2 == 0 else FB
    rect(x0, y0, x0 + 15, y0 + 15, base)
    hline(x0, x0 + 14, y0, FH)
    vline(x0, y0, y0 + 14, FH)
    hline(x0 + 1, x0 + 15, y0 + 15, FS)
    vline(x0 + 15, y0 + 1, y0 + 15, FS)
    px(x0 + 15, y0, base)
    px(x0, y0 + 15, base)
    for rx, ry in ((2, 2), (13, 2), (2, 13), (13, 13)):
        px(x0 + rx, y0 + ry, N5)
        px(x0 + rx + 1, y0 + ry + 1, FS)
    # petites éraflures
    for sx, sy in ((6, 5), (7, 5), (10, 10)):
        px(x0 + sx, y0 + sy, mix(base, FH, 0.5))
    px(x0 + 5, y0 + 11, mix(base, FS, 0.6))
    if variant == "vent":
        rect(x0 + 3, y0 + 4, x0 + 12, y0 + 11, FD)
        for yy in (5, 7, 9):
            hline(x0 + 4, x0 + 11, y0 + yy, K1)
            hline(x0 + 4, x0 + 11, y0 + yy + 1, mix(FD, C2, 0.35))
        hline(x0 + 3, x0 + 12, y0 + 12, FH)
        vline(x0 + 13, y0 + 4, y0 + 12, FH)


VENTS = {(10, 7), (3, 8)}
for ty in range(3, 10):
    for tx in range(1, 13):
        floor_tile(tx, ty, "vent" if (tx, ty) in VENTS else "plain")
# sortie en bas
for tx in (6, 7):
    floor_tile(tx, 10)


# ---------------------------------------------------------------- masse des murs
def wall_mass(x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(x, y, WT2 if (x % 4 == 1 and y % 4 == 1) else WT)


wall_mass(0, 0, W - 1, 15)
wall_mass(0, 0, 15, H - 1)
wall_mass(W - 16, 0, W - 1, H - 1)
wall_mass(0, 160, 95, H - 1)
wall_mass(128, 160, W - 1, H - 1)

# arêtes supérieures des murs (lumière)
hline(14, W - 15, 14, N2)
hline(15, W - 16, 15, N4)
vline(14, 14, 161, N2)
vline(15, 15, 160, N4)
vline(W - 15, 14, 161, N2)
vline(W - 16, 15, 160, N4)
hline(15, 95, 160, N4)
hline(14, 94, 161, N2)
hline(128, W - 16, 160, N4)
hline(129, W - 15, 161, N2)
vline(95, 160, H - 1, N4)
vline(94, 161, H - 1, N2)
vline(128, 160, H - 1, N4)
vline(129, 161, H - 1, N2)


# ---------------------------------------------------------------- face du mur du fond
def back_wall():
    for x in range(16, W - 16):
        lx = x % 16
        px(x, 16, N1)
        px(x, 17, N3)
        px(x, 18, N2)
        for y in range(19, 42):
            c = WB if y < 31 else WB2
            if lx == 15:
                c = N1
            elif lx == 0:
                c = (58, 62, 104)
            px(x, y, c)
        px(x, 30, (60, 66, 110))
        px(x, 31, N1)
        px(x, 42, N1)
        px(x, 43, N3)
        px(x, 44, C3)
        px(x, 45, C2)
        px(x, 46, K1)
        px(x, 47, (14, 14, 28))
        if lx in (3, 12):
            for ry in (21, 27, 34, 39):
                px(x, ry, N3)
                px(x, ry + 1, N1)
        blend(x, 41, C2, 0.28)
        blend(x, 40, C2, 0.14)
        blend(x, 39, C2, 0.06)


back_wall()
# ombre des murs latéraux sur la face
for y in range(16, 48):
    blend(16, y, K0, 0.35)
    blend(17, y, K0, 0.15)
    blend(W - 17, y, K0, 0.35)
    blend(W - 18, y, K0, 0.15)

# sol : ombre du mur + reflet du néon
for x in range(16, W - 16):
    blend(x, 48, K0, 0.35)
    blend(x, 48, C2, 0.18)
    blend(x, 49, C2, 0.12)
    blend(x, 50, C2, 0.06)
for y in range(48, 160):
    blend(16, y, K0, 0.32)
    blend(17, y, K0, 0.14)
    blend(W - 17, y, K0, 0.32)
    blend(W - 18, y, K0, 0.14)


# ---------------------------------------------------------------- tapis (cols 5-8, rows 6-7)
def rug():
    x0, y0, x1, y1 = 82, 98, 141, 125
    rrect(x0, y0, x1, y1, (58, 32, 96), K1)
    rrect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, (78, 44, 124), M1)
    rrect(x0 + 4, y0 + 4, x1 - 4, y1 - 4, (58, 32, 96), (98, 58, 150))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for y in range(y0 + 5, y1 - 4):
        for x in range(x0 + 5, x1 - 4):
            d = abs(x - cx) / 2 + abs(y - cy)   # losange
            if 9.5 <= d < 10.5:
                px(x, y, M2)
            elif 5 <= d < 6:
                px(x, y, C2)
            elif d < 2.5:
                px(x, y, C3 if d < 1.5 else C2)
    # franges
    for y in range(y0 + 2, y1 - 1, 2):
        px(x0 - 1, y, N6)
        px(x1 + 1, y, N6)
    # reflet haut
    hline(x0 + 3, x1 - 3, y0 + 1, (96, 60, 146))


rug()


# ---------------------------------------------------------------- poster (cols 1-2, row 1)
def poster():
    x0, y0, x1, y1 = 21, 20, 42, 37
    rect(x0, y0, x1, y1, K0)
    sky = [(40, 16, 70), (56, 20, 88), (80, 26, 104), (112, 34, 118),
           (150, 44, 128), (190, 56, 130)]
    for y in range(y0 + 1, 31):
        i = min(len(sky) - 1, (y - y0 - 1) * len(sky) // 10)
        hline(x0 + 1, x1 - 1, y, sky[i])
    cx, cy, r = 31.5, 30, 7
    suncols = [A3, A3, A2, A2, M3, M3, M2]
    for y in range(y0 + 1, 31):
        if y in (27, 29):
            continue
        for x in range(x0 + 1, x1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px(x, y, suncols[max(0, min(6, y - 23))])
    for y in range(31, y1):
        hline(x0 + 1, x1 - 1, y, (26, 8, 44))
    for y in (31, 33, 36):
        hline(x0 + 1, x1 - 1, y, M3 if y == 31 else M2)
    for k in range(-4, 5):
        for y in range(32, y1):
            x = round(cx + k * (y - 30) * 1.3)
            if x0 < x < x1:
                px(x, y, M2)
    # scotch + ombre
    for cx_, cy_ in ((x0, y0), (x1, y0)):
        px(cx_, cy_, N6)
    vline(x1 + 1, y0 + 1, y1 + 1, mix(WB, K0, 0.5))
    hline(x0 + 1, x1 + 1, y1 + 1, mix(WB, K0, 0.5))


poster()


# ---------------------------------------------------------------- fenêtre (cols 4-6, rows 1-2)
def window():
    ox = 64
    fx0, fy0, fx1, fy1 = ox + 2, 20, ox + 45, 42
    rect(fx0, fy0, fx1, fy1, K0)
    rect(fx0 + 1, fy0 + 1, fx1 - 1, fy1 - 1, N4)
    hline(fx0 + 1, fx1 - 1, fy0 + 1, N5)
    vline(fx0 + 1, fy0 + 1, fy1 - 1, N5)
    vline(fx1 - 1, fy0 + 2, fy1 - 1, N3)
    gx0, gy0, gx1, gy1 = fx0 + 4, fy0 + 3, fx1 - 4, 38
    rect(gx0 - 1, gy0 - 1, gx1 + 1, gy1 + 1, N2)
    sky = [(14, 10, 34)] * 2 + [(20, 14, 46)] * 2 + [(30, 18, 62)] * 2 + \
          [(44, 24, 82)] * 2 + [(62, 30, 98)] * 2 + [(86, 36, 112)] * 2 + \
          [(116, 44, 122)] * 2 + [(150, 56, 128)] + [(184, 76, 132)]
    for y in range(gy0, gy1 + 1):
        i = min(len(sky) - 1, y - gy0)
        for x in range(gx0, gx1 + 1):
            c = sky[i]
            if i + 1 < len(sky) and sky[i + 1] != c and (x + y) % 2 == 0:
                c = sky[i + 1]
            px(x, y, c)
    # étoiles
    for sx, sy, c in ((3, 1, WH), (9, 3, N6), (14, 0, N5), (20, 2, WH),
                      (27, 4, N5), (6, 6, N5), (33, 1, N6), (24, 7, N5),
                      (11, 8, N5), (31, 6, WH)):
        px(gx0 + sx, gy0 + sy, c)
    px(gx0 + 20, gy0 + 1, N5); px(gx0 + 20, gy0 + 3, N5)
    px(gx0 + 19, gy0 + 2, N5); px(gx0 + 21, gy0 + 2, N5)
    # planète à anneau
    pcx, pcy, pr = gx0 + 28, gy0 + 4, 3.2
    for y in range(gy0, gy0 + 10):
        for x in range(pcx - 5, pcx + 6):
            d = ((x - pcx) ** 2 + (y - pcy) ** 2) ** 0.5
            if d <= pr:
                shade = (x - pcx) + (y - pcy)
                px(x, y, A3 if shade < -1 else (A2 if shade < 2 else A1))
    for x in range(pcx - 6, pcx + 7):
        y = pcy + round((x - pcx) * -0.3)
        if abs(x - pcx) > 2 or x > pcx:
            px(x, y + 1, N6 if x < pcx + 3 else N5)
    # skyline
    blds = [(0, 3, 30), (4, 7, 27), (8, 9, 32), (10, 14, 25), (15, 17, 29),
            (18, 21, 23), (22, 23, 31), (24, 28, 26), (29, 31, 30), (32, 35, 24)]
    for bx0, bx1, top in blds:
        for x in range(gx0 + bx0, gx0 + bx1 + 1):
            for y in range(top, gy1 + 1):
                px(x, y, (24, 16, 46))
        px(gx0 + bx0, top, (40, 28, 70))
        for y in range(top + 2, gy1, 2):
            for x in range(gx0 + bx0 + 1, gx0 + bx1, 2):
                h = (x * 7 + y * 13) % 11
                if h < 3:
                    px(x, y, [A3, C3, M3][h])
    near = [(0, 5, 35), (6, 12, 34), (13, 16, 36), (17, 24, 33), (25, 29, 35), (30, 35, 34)]
    for bx0, bx1, top in near:
        for x in range(gx0 + bx0, gx0 + bx1 + 1):
            for y in range(top, gy1 + 1):
                px(x, y, (12, 10, 26))
    # antenne + balise
    vline(gx0 + 19, 20, 22, (40, 28, 70))
    px(gx0 + 19, 19, R2)
    # enseigne néon
    hline(gx0 + 11, gx0 + 13, 27, M3)
    hline(gx0 + 11, gx0 + 13, 28, M2)
    # voiture volante
    hline(gx0 + 3, gx0 + 5, gy0 + 9, C2)
    px(gx0 + 6, gy0 + 9, C4)
    px(gx0 + 2, gy0 + 9, C1)
    # reflets sur la vitre
    for y in range(gy0, gy1 + 1):
        for x in range(gx0, gx1 + 1):
            k = (x + y) % 22
            if k in (0, 1) or k == 4:
                blend(x, y, C4, 0.14)
    # ombre intérieure du cadre
    hline(gx0, gx1, gy0, mix(sky[0], K0, 0.5))
    for y in range(gy0, gy1 + 1):
        blend(gx0, y, K0, 0.3)
    # meneau
    mx = (gx0 + gx1) // 2
    vline(mx, gy0 - 1, gy1, N5)
    vline(mx + 1, gy0 - 1, gy1, N3)
    # rebord
    rect(fx0 - 1, 39, fx1 + 1, 42, K0)
    hline(fx0, fx1, 39, N6)
    hline(fx0, fx1, 40, N5)
    hline(fx0, fx1, 41, N3)
    brect(fx0, 43, fx1, 43, K0, 0.35)


window()


# ---------------------------------------------------------------- déco col 7 : grille + tuyau
def wall_vent():
    ox = 112
    rect(ox + 4, 22, ox + 11, 28, K0)
    rect(ox + 5, 23, ox + 10, 27, N1)
    for y in (23, 25, 27):
        hline(ox + 5, ox + 10, y, N3)
    hline(ox + 4, ox + 11, 29, (58, 62, 104))
    # tuyau vertical
    vline(ox + 7, 17, 21, N4)
    vline(ox + 8, 17, 21, N2)
    px(ox + 6, 17, K0); px(ox + 9, 17, K0)
    # petit panneau d'état
    rect(ox + 4, 33, ox + 11, 37, K0)
    rect(ox + 5, 34, ox + 10, 36, N1)
    px(ox + 6, 35, G3)
    px(ox + 8, 35, A2)
    hline(ox + 5, ox + 10, 38, mix(WB2, K0, 0.4))


wall_vent()


# ---------------------------------------------------------------- écran mural + bureau (cols 8-9)
def terminal():
    ox = 128
    # halo
    for y in range(17, 41):
        for x in range(ox, ox + 32):
            if not (ox + 2 <= x <= ox + 29 and 19 <= y <= 38):
                blend(x, y, C2, 0.16)
    rect(ox + 2, 19, ox + 29, 37, K0)
    rect(ox + 3, 20, ox + 28, 36, N1)
    hline(ox + 3, ox + 28, 20, N3)
    sx0, sy0, sx1, sy1 = ox + 5, 22, ox + 26, 34
    rect(sx0, sy0, sx1, sy1, (10, 40, 62))
    hline(sx0, sx1, sy0, C1)
    hline(sx0 + 1, sx0 + 8, sy0 + 1, C3)
    px(sx1 - 1, sy0 + 1, M3)
    px(sx1 - 3, sy0 + 1, A3)
    for y, ln in ((sy0 + 4, 9), (sy0 + 6, 6), (sy0 + 8, 8)):
        for x in range(sx0 + 1, sx0 + 1 + ln):
            if (x * 3 + y) % 7:
                px(x, y, C2 if x % 5 else C3)
    rect(sx0 + 1, sy0 + 10, sx0 + 2, sy0 + 11, C4)
    # mini graphe
    for i, h in enumerate((3, 5, 4, 7, 6, 8)):
        vline(sx1 - 7 + i, sy1 - 1 - h, sy1 - 1, M3 if i % 2 else M2)
    hline(sx1 - 8, sx1, sy1 - 1, C2)
    # lignes de balayage
    for y in range(sy0, sy1 + 1, 2):
        for x in range(sx0, sx1 + 1):
            blend(x, y, K0, 0.18)
    # reflet
    for x in range(sx0, sx0 + 4):
        blend(x, sy0 + (x - sx0), C4, 0.25)
    px(ox + 27, 36, G3)
    # support
    rect(ox + 14, 38, ox + 17, 40, N1)
    hline(ox + 14, ox + 17, 38, N3)


def desk():
    ox = 128
    x0, x1 = ox + 1, ox + 30
    # ombre au sol
    brect(x0, 61, x1 + 1, 63, K0, 0.35)
    brect(x1 + 1, 50, x1 + 1, 61, K0, 0.3)
    # côtés
    rect(x0, 50, x0 + 4, 61, K0)
    rect(x0 + 1, 51, x0 + 3, 60, N3)
    vline(x0 + 1, 51, 60, N4)
    rect(x1 - 4, 50, x1, 61, K0)
    rect(x1 - 3, 51, x1 - 1, 60, N3)
    vline(x1 - 3, 51, 60, N4)
    # dessous
    rect(x0 + 5, 51, x1 - 5, 60, (22, 22, 42))
    hline(x0 + 5, x1 - 5, 51, K0)
    # tour PC
    rect(x1 - 11, 53, x1 - 6, 60, K0)
    rect(x1 - 10, 54, x1 - 7, 60, N2)
    px(x1 - 9, 55, C3); px(x1 - 9, 57, C2); px(x1 - 8, 55, M3)
    # plateau
    rect(x0, 41, x1, 50, K0)
    rect(x0 + 1, 42, x1 - 1, 48, N5)
    hline(x0 + 1, x1 - 1, 42, N6)
    hline(x0 + 1, x1 - 1, 49, N3)
    hline(x0 + 2, x1 - 2, 50, C2)   # liseré lumineux
    # clavier
    rect(ox + 8, 44, ox + 21, 47, K0)
    rect(ox + 9, 45, ox + 20, 46, N1)
    for x in range(ox + 9, ox + 21, 2):
        px(x, 45, N3)
        px(x + 1, 46, N3)
    brect(ox + 8, 44, ox + 21, 44, C3, 0.3)
    # tasse
    rect(ox + 24, 43, ox + 27, 47, K0)
    rect(ox + 25, 44, ox + 26, 46, A2)
    px(ox + 25, 44, A3)
    px(ox + 26, 44, A1)
    px(ox + 28, 45, K0)
    px(ox + 25, 42, N6)
    px(ox + 26, 41, N6)


terminal()
desk()


# ---------------------------------------------------------------- porte (cols 10-11)
def door():
    ox = 160
    rect(ox + 1, 17, ox + 30, 47, K0)
    rect(ox + 2, 18, ox + 29, 47, N4)
    hline(ox + 2, ox + 29, 18, N6)
    vline(ox + 2, 18, 47, N5)
    vline(ox + 29, 19, 47, N2)
    # voyant
    rect(ox + 11, 18, ox + 20, 20, K0)
    hline(ox + 12, ox + 19, 19, G3)
    px(ox + 12, 19, G2); px(ox + 19, 19, G2)
    brect(ox + 10, 17, ox + 21, 17, G3, 0.3)
    # battants
    dx0, dx1, dy0 = ox + 5, ox + 26, 21
    rect(dx0 - 1, dy0 - 1, dx1 + 1, 47, K0)
    for (a, b) in ((dx0, ox + 15), (ox + 16, dx1)):
        rect(a, dy0, b, 47, N3)
        vline(a, dy0, 47, N4)
        vline(b, dy0, 47, N2)
        hline(a, b, dy0, N5)
        # hublot
        rect(a + 3, 25, b - 3, 30, K0)
        rect(a + 4, 26, b - 4, 29, (16, 40, 64))
        px(a + 4, 26, C3)
        px(a + 5, 26, C2)
    vline(ox + 15, dy0, 47, K0)
    vline(ox + 16, dy0, 47, N5)
    # bande de danger
    for y in range(37, 41):
        for x in range(dx0, dx1 + 1):
            if x in (ox + 15, ox + 16):
                continue
            px(x, y, A2 if ((x + y) // 2) % 2 == 0 else K1)
    hline(dx0, dx1, 36, N2)
    hline(dx0, dx1, 41, N2)
    vline(ox + 15, 37, 40, K0)
    # seuil au sol
    rect(ox + 3, 48, ox + 28, 51, N2)
    hline(ox + 3, ox + 28, 48, K0)
    hline(ox + 3, ox + 28, 49, N4)
    hline(ox + 3, ox + 28, 51, FS)
    for x in range(ox + 5, ox + 27, 3):
        px(x, 50, C2)


def keypad():
    ox = 192
    rect(ox + 2, 27, ox + 8, 36, K0)
    rect(ox + 3, 28, ox + 7, 35, N1)
    hline(ox + 4, ox + 6, 29, G3)
    for y in (31, 33):
        for x in (ox + 4, ox + 6):
            px(x, y, N4)
    px(ox + 5, 35, C3)
    vline(ox + 9, 28, 37, mix(WB, K0, 0.5))


door()
keypad()


# ---------------------------------------------------------------- lit (cols 1-2, rows 3-5)
def bed():
    x0, x1 = 18, 45
    # ombre
    brect(x1 + 1, 50, x1 + 3, 94, K0, 0.35)
    brect(x0 + 1, 94, x1 + 2, 95, K0, 0.35)
    # tête de lit
    rrect(x0, 35, x1, 48, N4)
    hline(x0 + 1, x1 - 1, 36, N6)
    hline(x0 + 1, x1 - 1, 37, N5)
    hline(x0 + 1, x1 - 1, 47, N2)
    hline(x0 + 3, x1 - 3, 42, C3)
    px(x0 + 2, 42, C2); px(x1 - 2, 42, C2)
    brect(x0 + 3, 41, x1 - 3, 41, C3, 0.25)
    brect(x0 + 3, 43, x1 - 3, 43, C3, 0.25)
    # cadre
    rrect(x0, 48, x1, 93, N2)
    # matelas / drap
    rect(x0 + 2, 49, x1 - 2, 86, N6)
    vline(x0 + 2, 49, 86, WH)
    vline(x1 - 2, 49, 86, N5)
    # oreiller
    rrect(x0 + 4, 50, x1 - 4, 58, WH, N5)
    hline(x0 + 5, x1 - 5, 57, N6)
    vline((x0 + x1) // 2, 51, 57, N6)
    px(x0 + 6, 51, WH)
    brect(x0 + 4, 59, x1 - 4, 59, K0, 0.2)
    # couverture
    bx0, bx1 = x0 + 1, x1 - 1
    rect(bx0, 62, bx1, 88, M2)
    vline(bx0, 62, 88, M3)
    vline(bx0 + 1, 63, 88, mix(M2, M3, 0.5))
    vline(bx1, 62, 88, M1)
    hline(bx0, bx1, 61, K0)
    hline(bx0, bx1, 62, WH)
    hline(bx0, bx1, 63, N6)
    hline(bx0, bx1, 64, M1)
    for y in (73, 74):
        hline(bx0 + 1, bx1 - 1, y, C3 if y == 73 else C2)
    for y in range(66, 87):
        for x in range(bx0 + 2, bx1):
            if (x + y) % 9 == 0 and y not in (73, 74):
                px(x, y, mix(M2, M1, 0.55))
    rect(bx0, 87, bx1, 89, M1)
    hline(bx0, bx1, 87, mix(M1, M2, 0.5))
    vline(x0, 61, 89, K0)
    vline(x1, 61, 89, K0)
    # façade du lit
    rect(x0, 90, x1, 93, K0)
    rect(x0 + 1, 90, x1 - 1, 92, N3)
    hline(x0 + 1, x1 - 1, 90, N4)
    px(x0 + 4, 91, C3); px(x0 + 7, 91, C2)


bed()


# ---------------------------------------------------------------- table de chevet + lampe (col 3)
def nightstand():
    ox = 48
    brect(ox + 14, 46, ox + 14, 61, K0, 0.3)
    brect(ox + 2, 61, ox + 14, 62, K0, 0.35)
    rect(ox + 1, 43, ox + 13, 60, K0)
    rect(ox + 2, 44, ox + 12, 49, N5)
    hline(ox + 2, ox + 12, 44, N6)
    rect(ox + 2, 50, ox + 12, 59, N3)
    hline(ox + 2, ox + 12, 50, N2)
    hline(ox + 2, ox + 12, 54, N1)
    vline(ox + 2, 51, 59, N4)
    px(ox + 7, 52, C3)
    px(ox + 7, 57, C3)
    # lampe
    ellipse_shadow(ox + 7, 47, 3, 1, 0.3)
    hline(ox + 5, ox + 9, 47, K0)
    hline(ox + 5, ox + 9, 46, N1)
    vline(ox + 7, 38, 45, N4)
    vline(ox + 8, 39, 45, N2)
    shade = ["....KKK....",
             "...KAAAK...",
             "..KAAAAAK..",
             ".KaaaaaaaK.",
             "KaaaaaaaaaK",
             "KwwwwwwwwwK"]
    sprite(ox + 2, 31, shade, {"K": K0, "A": A3, "a": A2, "w": WH})
    for y in range(28, 43):
        for x in range(ox - 2, ox + 17):
            d = ((x - ox - 7) ** 2 + (y - 35) ** 2) ** 0.5
            if d < 9 and P[x, y] != K0:
                blend(x, y, A3, 0.10 * (1 - d / 9))


nightstand()


# ---------------------------------------------------------------- plante (col 12, row 3)
def plant():
    ox = 192
    ellipse_shadow(ox + 8, 62, 6, 1, 0.35)
    # feuilles
    leaves = ["......g.......",
              ".....gG....g..",
              "....gGG...gG..",
              "..g.gGl..gGG..",
              ".gG.gGl.gGl...",
              ".gGG.Gl.Gl..g.",
              "..gGGGlGl..gG.",
              "...gGGGl..gGl.",
              "g...gGGl.gGl..",
              "gG...gGGgGl...",
              ".gGG.gGGGl....",
              "..gGGgGGl.....",
              "...ggGGl......",
              ".....gl.......",
              ]
    sprite(ox + 1, 39, leaves, {"g": G1, "G": G2, "l": G3}, outline=GL)
    # pot
    rect(ox + 3, 52, ox + 12, 61, K0)
    rect(ox + 4, 53, ox + 11, 60, N4)
    vline(ox + 4, 53, 60, N6)
    vline(ox + 5, 53, 60, N5)
    vline(ox + 10, 53, 60, N3)
    vline(ox + 11, 53, 60, N2)
    hline(ox + 4, ox + 11, 53, N6)
    hline(ox + 4, ox + 11, 57, C2)
    px(ox + 4, 57, C3)
    rect(ox + 5, 52, ox + 9, 52, (66, 44, 34))


plant()


# ---------------------------------------------------------------- chaise (devant le bureau)
def chair():
    cx = 144
    ellipse_shadow(cx, 76, 7, 2, 0.4)
    hline(cx - 6, cx + 6, 74, K0)
    hline(cx - 5, cx + 5, 73, N1)
    for wx in (cx - 6, cx, cx + 6):
        px(wx, 75, K0)
    vline(cx - 1, 68, 72, N2)
    vline(cx, 68, 72, N1)
    rrect(cx - 7, 64, cx + 6, 69, M1)
    hline(cx - 6, cx + 5, 65, M2)
    back = ["..KKKKKKKK..",
            ".KMMMMMMmmK.",
            "KMMmmmmmmmdK",
            "KMmmmmmmmmdK",
            "KMmmmmmmmmdK",
            "KMdddddddddK",
            "KMmmmmmmmmdK",
            "KMmmmmmmmmdK",
            ".KddddddddK.",
            "..KKKKKKKK..",
            ]
    sprite(cx - 6, 56, back, {"K": K0, "M": M3, "m": M2, "d": M1})


chair()


# ---------------------------------------------------------------- robot compagnon (col 3, row 5)
def robot():
    ox, oy = 50, 78
    ellipse_shadow(ox + 6, 94, 4, 1, 0.35)
    brect(ox + 4, 91, ox + 8, 92, C3, 0.35)
    rob = ["......M.....",
           "......n.....",
           "....WWWWW...",
           "...WWWWWWw..",
           "..WWkkkkkws.",
           "..Wkckkkcks.",
           "..Wkckkkcks.",
           "..wkkkkkkks.",
           "..wwwwwwwss.",
           "...swwwwss..",
           "....sssss...",
           ]
    sprite(ox, oy, rob, {"M": M3, "n": N4, "W": WH, "w": N6, "s": N5,
                         "k": K1, "c": C3}, outline=K0)
    px(ox + 4, oy + 3, WH)
    px(ox + 5, oy + 5, C4)
    px(ox + 9, oy + 5, C4)
    px(ox + 7, oy + 11, C3)
    px(ox + 7, oy + 12, C2)


robot()


# ---------------------------------------------------------------- caisses (col 12, rows 8-9)
def crates():
    ox, oy = 192, 128
    brect(ox + 15, 138, ox + 15, 158, K0, 0.3)
    brect(ox + 2, 158, ox + 15, 159, K0, 0.35)
    # grande caisse
    rect(ox + 1, 139, ox + 14, 157, K0)
    rect(ox + 2, 140, ox + 13, 145, N5)
    hline(ox + 2, ox + 13, 140, N6)
    rect(ox + 2, 146, ox + 13, 156, N3)
    hline(ox + 2, ox + 13, 146, N2)
    vline(ox + 2, 147, 156, N4)
    for y in range(148, 156):
        for x in (ox + 3, ox + 4, ox + 11, ox + 12):
            px(x, y, A2 if ((x + y) // 2) % 2 == 0 else K1)
    rect(ox + 6, 149, ox + 9, 153, N1)
    hline(ox + 7, ox + 8, 151, C3)
    # petite caisse dessus
    rect(ox + 4, 129, ox + 12, 140, K0)
    rect(ox + 5, 130, ox + 11, 133, N6)
    rect(ox + 5, 134, ox + 11, 139, N4)
    hline(ox + 5, ox + 11, 134, N3)
    px(ox + 8, 136, M3)
    brect(ox + 5, 141, ox + 12, 141, K0, 0.3)


crates()


# ---------------------------------------------------------------- tapis de sortie
def exit_mat():
    rect(98, 163, 125, H - 1, K1)
    hline(98, 125, 163, N1)
    vline(98, 163, H - 1, N1)
    vline(125, 163, H - 1, N1)
    for k, y in enumerate((165, 169)):
        for i in range(4):
            px(111 - i, y + 3 - i, C3 if k else C2)
            px(112 + i, y + 3 - i, C3 if k else C2)


exit_mat()


# ---------------------------------------------------------------- export
img.save(os.path.join(OUT, "room.png"))
S = 4
big = img.resize((W * S, H * S), Image.NEAREST)
big.save(os.path.join(OUT, "room_x4.png"))

grid = big.copy()
G = grid.load()
for y in range(H * S):
    for x in range(W * S):
        if x % (T * S) == 0 or y % (T * S) == 0:
            G[x, y] = mix(G[x, y], (255, 255, 255), 0.35)
grid.save(os.path.join(OUT, "room_grid_x4.png"))

tiles, index, tmap = [], {}, []
for ty in range(TH):
    row = []
    for tx in range(TW):
        t = img.crop((tx * T, ty * T, tx * T + T, ty * T + T))
        key = t.tobytes()
        if key not in index:
            index[key] = len(tiles)
            tiles.append(t)
        row.append(index[key])
    tmap.append(row)

COLS = 8
rows = (len(tiles) + COLS - 1) // COLS
sheet = Image.new("RGBA", (COLS * T, rows * T), (0, 0, 0, 0))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % COLS) * T, (i // COLS) * T))
sheet.save(os.path.join(OUT, "tileset.png"))

pad = 4
prev = Image.new("RGB", (COLS * (T * S + pad) + pad, rows * (T * S + pad) + pad), (24, 22, 36))
for i, t in enumerate(tiles):
    prev.paste(t.resize((T * S, T * S), Image.NEAREST),
               (pad + (i % COLS) * (T * S + pad), pad + (i // COLS) * (T * S + pad)))
prev.save(os.path.join(OUT, "tileset_x4.png"))

with open(os.path.join(OUT, "map.json"), "w") as f:
    json.dump({"tilewidth": T, "tileheight": T, "width": TW, "height": TH,
               "tileset": "tileset.png", "columns": COLS, "data": tmap}, f, indent=1)

print(f"{len(tiles)} tiles uniques")
