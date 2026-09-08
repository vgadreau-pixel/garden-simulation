# Jardin des Saisons

Jardin 3D zen (vue de dessus, three.js) où la végétation vit au rythme des
saisons : croissance, floraison, fructification, neige — sous le climat de
votre choix, avec nappe musicale procédurale.

## Lancer

```bash
npm install
npm run dev        # serveur de dev (Vite)
npm run build      # build de production → dist/
npm run preview    # sert le build (port 4173 par défaut)
```

## Contrôles

| Action | Contrôle |
|---|---|
| Déplacer la vue | Glisser (clic gauche maintenu) |
| Zoomer | Molette (zoom vers le curseur) ou pincement |
| Planter | Choisir une espèce dans le **Catalogue** (panneau gauche), puis cliquer sur une parcelle libre |
| Arracher | Cliquer une parcelle occupée, ou **clic droit** dessus |
| Tout arracher | Bouton « 🗑 Tout arracher » en bas du catalogue |
| Choisir le climat | Panneau **Climat** (haut droite) : tempéré, méditerranéen, tropical, continental/montagnard, aride |
| Vitesse du temps | Barre du bas : ⏸ pause, ×1 temps réel, 1 jour/s, 1 semaine/s, 1 mois/s |
| Changer la date | Slider de la barre du bas (scrubbing sur l'année) |
| Musique | Contrôle audio (bouton ▶/⏸ + volume) : nappe procédurale qui suit la saison et la météo |

## Comment ça marche

- **Climat** : chaque climat définit température, précipitations et
  ensoleillement mensuels (interpolés en continu). Il module la vigueur des
  espèces, décale les floraisons (±6 j/°C) et pilote la météo à particules
  (pluie, neige, brume).
- **Temps** : horloge continue 0–365 j avec vitesses d'accélération et
  scrubbing ; le soleil suit la déclinaison réelle (46,5° N) — durée du jour,
  hauteur, teinte et intensité varient avec la saison.
- **Végétaux** : 19 espèces réelles (arbres, arbustes, fleurs, légumes) avec
  stades de croissance, feuillage saisonnier, floraison et fructification.
  Le rendu interpole tout en douceur (smoothstep + cloches gaussiennes).
- **Sauvegarde** : le plan du jardin (espèces + parcelles + maturité) et le
  climat sont persistés dans `localStorage` et restaurés au démarrage.
- **Audio** : 100 % procédural (Web Audio) — drones, vent, carillons
  pentatoniques, réverbération ; démarrage au clic (autoplay-safe), variations
  par saison et météo en fondus.

## URL

`?climat=<id>` pré-sélectionne un climat au chargement
(`tempre`, `mediterraneen`, `tropical`, `continental`, `aride`).

## Vérifications

Scripts sous `scripts/` (nécessitent un Chrome headless avec CDP et
`npm run preview` actif) :

- `verify_finale.py` — parcours complet : climat → plantations au clic →
  retrait clic droit → musique → année accélérée → caméra → bilan erreurs.
- `verify_timelapse_instru.py` — mesure exacte du time-lapse (instrumentation
  de l'horloge : jours parcourus avec wraps, fps effectif).
- `check-climat.mjs`, `check-continuite.mjs`, `check-annee.mjs`,
  `check-data.mjs`, `check-multipas.mjs` — tests logiques (node).

> Note : dans un environnement headless **sans GPU**, le rendu passe par
> SwiftShader (logiciel) et le FPS chute à quelques images/s ; sur un matériel
> réel avec GPU, la scène reste fluide (la logique JS coûte < 1 ms/frame à
> 50 plantes).
