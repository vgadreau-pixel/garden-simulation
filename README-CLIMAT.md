# Système de climat — Jardin des Saisons (tâche t_d316b27d)

Ce module rend le climat **choisissable et impactant** dans la simulation.

## Nouveaux fichiers

| Fichier | Rôle |
|---|---|
| `src/climate.js` | Définition des 5 climats (températures, précipitations, ensoleillement par mois) + météo continue, vigueur des plantes, décalage de floraison, facteur de croissance. |
| `src/weather.js` | Particules météo : pluie, neige, brume (volutes douces) — intensités continues 0..1 pilotées par le climat. |
| `src/climateUI.js` | Panneau de sélection de climat (haut droite) avec valeurs courantes (°C, mm/mois, h/j de soleil). |
| `src/climateStyles.js` | Styles du panneau (injectés dans `<head>` au démarrage). |

## Fichiers modifiés

- `src/simulationClock.js` : l'horloge porte le climat courant, fait progresser
  la maturité des plantes (0,01/j × facteur de croissance du climat) et expose
  `setClimat(id)`.
- `src/seasons.js` : `etatPlante(plante, jours, climatId)` module la masse
  foliaire, la floraison et la couleur (brun-jaune de stress) selon la vigueur ;
  la floraison est décalée de ±25 j selon la température du climat (modèle de
  somme de température simplifié).
- `src/plantInstances.js` : `appliquerEtat(instance, jours, climatId)`.
- `src/main.js` : câblage complet — météo recalculée chaque frame, particules
  animées, lumière du soleil modulée par l'éclat du climat (aride ≈ 1,35×,
  couvert ≈ 0,72×), ciel grisé sous nuages, panneau UI, pré-sélection via
  `?climat=<id>` dans l'URL.

## Les 5 climats

`tempre` (défaut), `mediterraneen`, `tropical`, `continental` (montagnard), `aride`.

Chacun définit 12 valeurs mensuelles de température moyenne (°C), précipitations
(mm/mois) et ensoleillement (h/jour) ; tout le reste est interpolé en continu.

## Effets sur la simulation

1. **Vigueur des espèces** — une espèce listée pour le climat prospère (1.0) ;
   sinon la pénalité suit l'écart thermique entre le climat courant et son
   climat de référence le plus proche : masse foliaire réduite, pas de
   floraison/fruits, feuillage tirant vers le brun-jaune. Ex. : olivier à
   vigueur 0.29 en continental, 1.0 en méditerranéen.
2. **Floraison décalée** — ±6 j/°C d'écart avec le climat tempéré, plafonné
   ±25 j (lavande au 25 juin : floraison 0.95 en méditerranéen, 0.45 en continental).
3. **Vitesse de croissance** — facteur 0.4 (froid) à 1.5 (chaud et lumineux),
   appliqué à la progression de maturité de chaque plante.
4. **Particules météo** — pluie (intensité ∝ précipitations), neige
   (température ≤ 1,5 °C seulement), brume (humide + frais + peu de soleil) ;
   éclat solaire modulant l'intensité des lumières et la teinte du ciel.

## Vérifications

- `node scripts/check-climat.mjs` — 16 tests logiques (continuité, botanique,
  floraison, croissance, cohérence météo).
- `python3 scripts/verify_climat_cdp.py` — vérification complète sous Chrome :
  0 erreur console, 5 climats à empreintes pixel distinctes à date constante,
  vigueurs conformes, floraison décalée, croissance plus rapide en aride.
- `python3 scripts/verify_neige_cdp.py` — neige visible en continental/hiver,
  absente en méditerranéen/aride.
- Preuves visuelles dans `preuves/` (5 climats en été + 4 en hiver).
