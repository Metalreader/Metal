# Eros — course vers la droite

Généré par `python3 generate.py` à partir de `EROS_walk_right.aseprite` (perso) en suivant
la structure de `BASE_running_right.aseprite` (modèle de course).

- `out/EROS_run_right.aseprite` / `out/eros_run_right.png` : 4 frames 32×32, 80 ms, tag `run_right`
- `out/preview_run_x6.gif` : course avec sol qui défile
- `out/preview_walk_vs_run_x6.gif` : marche (gauche) et course (droite) côte à côte

| # | Pose |
|---|---|
| 0 | Passage (jambes réunies) |
| 1 | Foulée A : rebond +1 px, bras avant, jambe arrière en poussée |
| 2 | Passage |
| 3 | Foulée B : rebond +1 px, bras arrière, genou avant levé |

La tête est avancée d'1 px (le perso penche en courant) et la queue de cheval se soulève
pendant les foulées. Même canevas et même point d'ancrage que la marche.
