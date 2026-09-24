# Eros — course vers la droite

Généré par `python3 generate.py`. Seule la tête vient du dessin original
(`EROS_walk_right.aseprite`) ; manteau, bras, jambes et chaussures sont reconstruits à chaque
frame avec la palette d'Eros et un contour noir.

- `out/EROS_run_right.aseprite` / `out/eros_run_right.png` : 6 frames 32×32, 80 ms, tag `run_right`
- `out/preview_run_x6.gif` : course avec sol qui défile

| # | Pose | Rebond |
|---|---|---|
| 0 | Contact : pied proche devant, pied du fond levé derrière, bras proche en arrière | +1 |
| 1 | Réception : corps au plus bas | 0 |
| 2 | Poussée : genou du fond qui monte, pan du manteau qui flotte | +1 |
| 3-5 | Même chose de l'autre côté | |

La jambe et le bras du fond sont plus sombres pour lire la profondeur. La queue de cheval
réagit au rebond avec un temps de retard. Même canevas et même ancrage que la marche.
