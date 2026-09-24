# Héros — épée + attaque (vers la droite)

Généré par `python3 generate.py` à partir de `HERO_walk_right.aseprite` (dessin original).

| Fichier (`out/`) | Contenu |
|---|---|
| `HERO_walk_sword_right.aseprite` / `hero_walk_sword_right.png` | Marche avec épée, 4 frames 32×32, 100 ms |
| `HERO_attack_right.aseprite` | Attaque, 8 frames 64×64, calques **Hero** + **VFX**, tag `attack_right` |
| `hero_attack_right.png` | Planche complète (perso + VFX) |
| `hero_attack_right_body.png` / `_vfx.png` | Perso seul / VFX seuls (pour les séparer dans le moteur) |
| `HERO_attack_right.aseprite` → `hit_fx.*` | Impact seul 32×32, 4 frames, à poser sur le monstre |
| `preview_*.gif` | Aperçus agrandis (le slime n'est qu'une cible de démo) |

## Frames d'attaque

| # | Durée | Pose |
|---|---|---|
| 0 | 140 ms | Garde |
| 1 | 110 ms | Anticipation : recul, lame armée en arrière |
| 2 | 90 ms | Éclat sur la lame |
| 3 | 50 ms | Smear : fente avant, lame qui s'illumine |
| 4 | 110 ms | **Impact** : croissant d'énergie + étoile d'impact (déclencher les dégâts ici) |
| 5 | 90 ms | Suite du geste, onde de choc, étincelles |
| 6 | 90 ms | Dissipation, retour |
| 7 | 120 ms | Retour en garde |

## Alignement

Dans les frames 64×64, le canevas 32×32 d'origine est placé en **(10, 30)** : les pieds
tombent au même endroit que dans l'animation de marche. Point d'impact : **(50, 49)**
dans la frame 64×64.
