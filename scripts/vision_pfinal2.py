#!/usr/bin/env python3
"""Vision : pfinal_petit.jpg."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

q = "Cette image : vue 3D subjective de jardin (arbres, ciel) ou grille 2D de dessus ? 2 phrases."
try:
    print(analyze('preuves/pfinal_petit.jpg', q)[:300])
except Exception as e:
    print('ERREUR:', e)
