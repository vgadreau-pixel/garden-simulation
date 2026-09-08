#!/usr/bin/env python3
"""Verif ponctuelle : la capture 'dessous' montre-t-elle bien un houppier vu par en dessous ?"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

q = ("Cette capture montre-t-elle une vue depuis DESSOUS un houppier "
     "(feuilles vues par en dessous, ciel en fond) ? Ou une vue de dessus ? "
     "Reponds en 3 phrases max.")
print(analyze(os.path.join(os.path.dirname(__file__), '..', 'preuves', 'vegV3_ete_dessous.png'), q))
