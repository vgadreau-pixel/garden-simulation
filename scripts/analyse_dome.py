#!/usr/bin/env python3
"""Diagnostic pipeline rendu : vertex shader du dôme sous caméra ortho.
L'ortho va du haut (y=100) vers le bas. Les fragments du dôme au-dessus de la
ligne de visée... En ortho, dir.y calculé depuis vWorldPos normalisé est la
direction DEPUIS L'ORIGINE MONDE, pas depuis la caméra : le haut de l'écran
montre le dôme côté -z (loin), le bas côté +z. h = dir.y avec dir=(x,380?,z)/len.
Sur les bords haut/bas du frustum : |z| jusqu'à ~ (distance écran). Vérifions
numériquement ce que dir.y vaut aux 4 coins du sol vu par la caméra."""
import json, math

# caméra : pos (0,100,0), lookAt (0,0,0), up (0,0,-1), ortho top=30 (VIEW_HEIGHT/2), aspect 1600/757
# demi-hauteur frustum = 30 m sur le plan sol.
# Coin haut écran : point sol (0,0,-30). Rayon ortho direction (0,-1,0), origine (0,100,-30).
# Fragment dôme touché : dôme rayon 380 centré origine. Le point d'entrée du rayon
# x=0,y=100-t,z=-30 → (100-t)^2+900=380^2 → 100-t = sqrt(144400-900)=378.8 → t=-278 (derrière!)
# Le rayon part de y=100 vers le bas : il ne PEUT pas toucher un dôme de rayon 380
# centré à l'origine AVANT le sol... si : |(0,100,-30)|=104 < 380 → la caméra est
# DANS le dôme. Le rayon vers le bas touche la PAROI INFÉRIEURE du dôme :
# (100-t)=-378.6 → t=478 > far=500 ? Non : 478 < 500 OK.
# dir = normalize(vWorldPos) = normalize(0,-378.6,-30) → dir.y = -0.996 → h=clamp(dir.y,0,1)=0
# → couleur cHorizon PARTOUT. Confirmé analytiquement !
print('Analyse : en vue ortho plongeante, h=0 partout sur le dôme → cHorizon plein écran.')
print('Le dôme gradient ne peut pas montrer de dégradé en plongée : normal.')
print('MAIS la couleur de fond vue = cHorizon, donc c est cHorizon qui doit porter la couleur ciel perçue.')
