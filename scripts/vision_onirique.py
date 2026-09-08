#!/usr/bin/env python3
"""Vision GLM sur les captures oniriques (via le module vision_glm)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

P = os.path.join(os.path.dirname(__file__), '..', 'preuves')
QUESTIONS = {
    'dbg_13h.png': "Vue d'un jardin 3D. Décris : parcelles, chemins, plantes, arbres, eau ? Réaliste ou schématique ?",
    'dbg_22h.png': "Jardin 3D de nuit. Décris l'ambiance : nuit sombre, étoiles ?",
    'onirique_ete_golden_fps.png': "Vue subjective dans un jardin à l'heure dorée. Y voit-on arbres, herbe, bassin, lumière dorée, brume ? Décris.",
    'onirique_hiver_fps.png': "Vue subjective d'un jardin en hiver. Arbres nus ? Ambiance froide ? Décris.",
}

for f, q in QUESTIONS.items():
    path = os.path.join(P, f)
    if not os.path.exists(path):
        print(f, 'ABSENT'); continue
    try:
        print('===', f, '===')
        print(analyze(path, q)[:900])
    except Exception as e:
        print(f, 'ERREUR:', e)
