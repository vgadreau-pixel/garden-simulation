#!/usr/bin/env python3
"""Vision : printemps final (40 s d'attente)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

q = "Vue subjective jardin 3D printemps. 1) Feuillage vert des arbres visible ? 2) Vue 3D immersive a hauteur d homme ou grille 2D ? 3) Decris brievement l ambiance. 3 lignes max."
try:
    print(analyze('preuves/onirique_printemps_final.png', q)[:400])
except Exception as e:
    print('ERREUR:', e)
