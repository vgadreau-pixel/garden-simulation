#!/usr/bin/env python3
"""Vision GLM sur les captures orbitales zoomées."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

preuves = os.path.join(os.path.dirname(__file__), '..', 'preuves')
questions = {
    'veg_fix_orb_ete.png': "Capture 3D vue de dessus d'un jardin en été. Décris : voit-on des houppiers d'arbres avec feuillage vert, du sol texturé (pelouse, chemin) ? Les arbres ont-ils l'air d'arbres réalistes texturés ou de primitives (cubes, sphères unies) ?",
    'veg_fix_orb_automne.png': "Capture 3D vue de dessus d'un jardin en automne. Les feuillages ont-ils des teintes orangées/brunes d'automne ? Décris ce qu'on voit.",
    'veg_fix_orb_hiver.png': "Capture 3D vue de dessus d'un jardin en hiver. Les arbres caducs paraissent-ils nus (branches visibles sans feuillage) ? Y a-t-il de la neige ?",
}
for nom, q in questions.items():
    p = os.path.join(preuves, nom)
    print(f'=== {nom} ===')
    try:
        print(analyze(p, q))
    except Exception as e:
        print('ERREUR', e)
    print()
