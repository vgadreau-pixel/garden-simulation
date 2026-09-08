#!/usr/bin/env python3
"""Vision GLM sur les captures FPS adultes (le vrai test visuel)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

preuves = os.path.join(os.path.dirname(__file__), '..', 'preuves')
questions = {
    'fps_adulte_ete.png': "Capture 3D à hauteur d'homme dans un jardin en été (15 juillet midi). Question unique : vois-tu des arbres avec un feuillage vert fourni et texturé (vraies feuilles sur branches), distincts de cubes/sphères unies ? 3 phrases max.",
    'fps_adulte_dessous.png': "Capture 3D depuis le sol, regard vers le haut dans le houppier d'un arbre en été. Question unique : vois-tu des FEUILLES au-dessus de toi (vu de dessous) ou du vide ? 3 phrases max.",
    'fps_adulte_automne.png': "Capture 3D à hauteur d'homme dans un jardin en automne (17 octobre midi). Question unique : les feuillages montrent-ils des teintes orangées/rouges/brunes ? 3 phrases max.",
    'fps_adulte_hiver.png': "Capture 3D à hauteur d'homme dans un jardin en hiver (16 janvier midi). Question unique : les arbres caducs sont-ils nus (branches sans feuilles) ? 3 phrases max.",
}
for nom, q in questions.items():
    p = os.path.join(preuves, nom)
    print(f'=== {nom} ===')
    try:
        print(analyze(p, q))
    except Exception as e:
        print('ERREUR', e)
    print()
