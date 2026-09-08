#!/usr/bin/env python3
"""Vision GLM finale : les 6 captures oniriques distinctes."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

P = os.path.join(os.path.dirname(__file__), '..', 'preuves')
QUESTIONS = {
    'onirique_ete_fps.png': "Vue subjective (à hauteur d'homme) d'un jardin 3D en été, vers 10h. Réponds brièvement : 1) Voit-on des arbres avec feuillage vert, du sol, de l'herbe, un bassin d'eau ? 2) Le ciel est-il bleu en haut ? 3) Le rendu est-il plat/schématique ou avec du relief et de la lumière ?",
    'onirique_hiver_fps.png': "Vue subjective d'un jardin 3D en hiver vers 10h. Réponds brièvement : 1) Les arbres caducs sont-ils nus ? 2) L'ambiance est-elle froide/pâle ? 3) Différente d'un jardin d'été ?",
    'onirique_ete_golden_fps.png': "Vue subjective d'un jardin 3D en fin d'après-midi (18h45, golden hour). Réponds brièvement : 1) La lumière est-elle dorée/chaude ? 2) Voit-on des rais de lumière ou une brume lumineuse ? 3) Ambiance reposante ?",
    'onirique_ete_nuit_fps.png': "Vue subjective d'un jardin 3D de nuit (22h30 en été). Réponds brièvement : 1) La scène est-elle sombre avec un ciel nuit ? 2) Voit-on des points lumineux (lucioles/étoiles) ?",
    'onirique_printemps_fps.png': "Vue subjective d'un jardin 3D au printemps vers 10h. Réponds brièvement : 1) Le feuillage est-il vert clair ? 2) Y a-t-il du pollen ou des particules lumineuses dans l'air ? 3) Le sol et les allées sont-ils visibles ?",
    'onirique_automne_fps.png': "Vue subjective d'un jardin 3D en automne vers 10h. Réponds brièvement : 1) Les feuillages ont-ils des teintes orangées/jaunes ? 2) Y a-t-il des pétales/feuilles qui flottent ? 3) Ambiance automnale ?",
}
for f, q in QUESTIONS.items():
    path = os.path.join(P, f)
    try:
        print('===', f, '===')
        print(analyze(path, q)[:600])
        print()
    except Exception as e:
        print(f, 'ERREUR:', e)
