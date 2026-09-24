# Relaeh — coup de poing (vers la droite)

Généré par `python3 generate.py` à partir de `RELAEH_walk_right.aseprite` (dessin original).

| Fichier (`out/`) | Contenu |
|---|---|
| `RELAEH_punch_right.aseprite` | Dash-punch, 8 frames 64×64, calques **Relaeh** + **VFX**, tag `punch_right` |
| `relaeh_punch_right.png` | Planche complète (perso + VFX) |
| `relaeh_punch_right_body.png` / `_vfx.png` | Perso seul / VFX seuls |
| `punch_hit_fx.aseprite` / `.png` | Impact seul 32×32, 4 frames, à poser sur le monstre |
| `preview_punch_x4.gif`, `punch_strip_x4.png` | Aperçus agrandis (le slime n'est qu'une cible de démo) |

## Frames

| # | Durée | Pose |
|---|---|---|
| 0 | 140 ms | Garde |
| 1 | 110 ms | Anticipation : recul, poing armé en arrière |
| 2 | 90 ms | Charge : le poing s'embrase |
| 3 | 50 ms | Dash (+4 px) : bras qui part, traînée de vitesse |
| 4 | 120 ms | **Impact** (+6 px) : explosion en étoile + onde de choc (déclencher les dégâts ici) |
| 5 | 90 ms | Onde de choc qui s'étend, étincelles |
| 6 | 90 ms | Retour (+3 px), fumée, braises |
| 7 | 120 ms | Garde |

## Alignement

Même format et même ancrage que l'attaque du héros : le canevas 32×32 d'origine est placé
en **(10, 30)** dans la frame 64×64. Point d'impact : **(43, 50)**. Le perso avance de 6 px
pendant le coup puis revient ; ce déplacement est inclus dans les frames.
