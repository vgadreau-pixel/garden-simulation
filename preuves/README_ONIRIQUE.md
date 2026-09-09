# Jardin des Saisons — couche onirique (intégration finale)

## Ce qui a été livré
- `src/onirique.js` (nouveau) : couche shaders custom GLSL
  - **Herbe instanciée** : InstancedMesh (~26 000 brins, réductible via `?herbe=N`),
    vertex shader d'ondulation multi-octaves (fléchit vers la pointe, déphasage
    par instance + position), palette saisonnière (vert clair → automne doré →
    hiver gris), brume FogExp2 partagée avec la scène.
  - **Bassin** (angle sud-ouest de la pelouse) : shader d'eau (caustiques 2 couches,
    fresnel, spéculaire soleil, vagues centimétriques), fond sombre, anneau de
    pierres ; **obstacle de collision** pour la marche FPS.
  - **Particules saisonnières** : pollen (printemps, jour), pétales (automne, jour),
    lucioles (nuits d'été) — points additifs à texture radiale, dérive lente,
    fondu progressif selon saison/heure/météo.
  - **Rais de lumière** : plans billboardés additifs (stries descendantes lentes),
    intensité maximale aux heures dorées, éteints la nuit et par temps couvert.
- `src/main.js` : branchement (création + `update()` par frame piloté par
  soleil/saison/météo/brume), exposition `window.__jardin.onirique`.
- `src/fpsControls.js` : collision du bassin (on ne marche pas sur l'eau).

## Vérifications (Chrome headless dédié, SwiftShader, CDP)
- Build `vite build` OK ; 0 erreur console au chargement.
- scene_check : 1 InstancedMesh d'herbe + 8 meshes d'eau + 3 systèmes de
  particules présents ; socle intact (orbital, plantation, climats, horloge).
- Marche FPS + collision bassin OK (rejet à 6,1 m du centre du bassin).
- 6 captures plein écran 1280x720 **pixel-distinctes** (hash uniques) :
  - `onirique_ete_fps.png` — été 10h : canopée verte, ciel bleu, relief, ombres (validé GLM)
  - `onirique_hiver_fps.png` — hiver 10h : arbres caducs nus, ambiance froide (validé GLM)
  - `onirique_automne_fps.png` — automne 10h : teintes roux/or/brun, golden hour rasante (validé GLM)
  - `onirique_ete_golden_fps.png` — été 18h45 : lumière dorée + rais de lumière volumétriques (validé GLM)
  - `onirique_ete_nuit_fps.png` — été 22h30 : ciel bleu nuit + points lumineux (lucioles/étoiles) (validé GLM)
  - `onirique_printemps_fps.png` — printemps (jour 105) : la vision GLM décrit une
    vue plongeante « grille » ; toutes les tentatives (jours 75/105, attentes 15-40 s,
    navigateurs frais) donnent ce rendu → **capture non validée par vision**,
    à reprendre lors d'une passe de reprise.

## Limite connue (SwiftShader)
Sur la VM sans GPU, le rendu tombe à ~0,3 fps (1 frame / 3 s). Les captures sont
faites après attente ≥ 2 frames. Sur un vrai GPU intégré récent, la charge reste
modérée (herbe 26 k brins = 1 draw call, particules 3 draw calls, rais 7 quads).

## Reproduire
```
cd jardin-des-saisons
node node_modules/vite/bin/vite.js build
node node_modules/vite/bin/vite.js preview --port 4183 --strictPort
google-chrome --headless=new --remote-debugging-port=9335 --use-gl=angle \
  --use-angle=swiftshader --enable-unsafe-swiftshader --user-data-dir=/tmp/chX about:blank
CDP_PORT=9335 python3 scripts/verify_onirique.py   # ou verify_onirique10/11/13 par saison
```
