// Modèle saisonnier : pour un temps continu (jours de l'année), calcule le
// stade de chaque plante (dormance, débourrement, floraison, fructification,
// chute des feuilles, neige) et interpole DOUCEMENT couleurs et échelles.
//
// Principe : le catalogue (src/data/plants.js) donne des repères par mois
// (moisFloraison, moisFructification, feuillage par saison). On les convertit
// en courbes continues sur l'année :
//   - couleur feuillage : échantillonnée au milieu de chaque saison puis
//     interpolée (lerp de three) → pas de saut au changement de saison ;
//     pour un caduc, la transition hiver glisse vers le brun des rameaux
//     proportionnellement à la chute de la masse foliaire (double adoucissement) ;
//   - intensité floraison / fruits : cloches gaussiennes centrées sur les
//     fenêtres `moisFloraison` / `moisFructification` → montée et descente
//     progressives ;
//   - masse foliaire : 0 en hiver (caduc) → débourrement progressif au
//     printemps → pleine feuille en été → chute progressive en automne ;
//   - échelle globale : les stades du catalogue (graine/jeune_pousse/mature)
//     sont réservés à la CROISSANCE pluri-annuelle ; ici on interpole la
//     taille des organes (feuilles, fleurs, fruits) avec la même douceur.
import * as THREE from 'three';
import { DAYS_PER_YEAR } from './simulationClock.js';
import { decalageFloraison, vigueur } from './climate.js';

// Convertit un mois (1..12) en temps continu au CENTRE du mois, en jours.
// Centre du mois m ≈ (m - 0.5) * 365/12 ; fin décembre ≡ début janvier (boucle).
function moisVersJours(mois) {
  return ((mois - 0.5) * DAYS_PER_YEAR) / 12;
}

// Cloche gaussienne normalisée : 1 au centre, retombe vers 0 à ±largeurJours*2.
function cloche(jours, centreJours, largeurJours) {
  const d = deltaCycle(jours, centreJours);
  const t = d / (largeurJours * 2);
  return Math.exp(-t * t * 4); // ~0 au-delà de 2 largeurs
}

// Différence la plus courte sur l'annee cyclique (gère le passage déc→jan).
function deltaCycle(a, b) {
  let d = a - b;
  if (d > DAYS_PER_YEAR / 2) d -= DAYS_PER_YEAR;
  if (d < -DAYS_PER_YEAR / 2) d += DAYS_PER_YEAR;
  return d;
}

// Interpolation lissée (smoothstep) — évite les dérivées brusques du lerp brut.
export function smoothstep(t) {
  t = Math.min(1, Math.max(0, t));
  return t * t * (3 - 2 * t);
}

/**
 * Masse foliaire continue 0..1 pour une plante à `jours`.
 * Caduc : 0 en hiver, montée sur mars–avril (débourrement), plateau été,
 * descente sur octobre–novembre (chute des feuilles).
 * Persistant (feuillage.hiver ≠ null) : jamais sous ~0.7, teinte hivernale.
 */
export function masseFoliaire(plante, jours) {
  const feuillage = plante.feuillage || {};
  if (feuillage.hiver !== null && feuillage.hiver !== undefined) {
    return 1; // persistant : couverture constante (la couleur change, pas la masse)
  }
  // Repères (jours) : débourrement ~1er mars, plein feuillage ~15 mai,
  // début de chute ~1er octobre, branches nues ~1er décembre.
  const bourre = moisVersJours(3) - 12; // fin février
  const plein = moisVersJours(5);
  const chute = moisVersJours(10);
  const nu = moisVersJours(12);

  if (jours >= bourre && jours < plein) {
    return smoothstep((jours - bourre) / (plein - bourre));
  }
  if (jours >= plein && jours < chute) {
    return 1;
  }
  if (jours >= chute && jours < nu) {
    return 1 - smoothstep((jours - chute) / (nu - chute));
  }
  return 0; // hiver profond
}

/**
 * Couleur du feuillage (THREE.Color) interpolée continûment sur l'année.
 * Pour un caduc dont la masse est faible, la couleur glisse vers le brun des
 * rameaux (la feuille disparaît de toute façon par l'échelle/opacité).
 */
const _c1 = new THREE.Color();
const _c2 = new THREE.Color();
export function couleurFeuillage(plante, jours, cible) {
  const out = cible || new THREE.Color();
  const f = plante.feuillage || {};
  // Points d'échantillonnage : centre de chaque saison, avec la couleur de la
  // saison du centre (hiver = centre de l'hiver ≈ mi-janvier, via boucle).
  const pts = [
    { j: moisVersJours(4), c: f.printemps }, // printemps (avril)
    { j: moisVersJours(7), c: f.ete }, // été (juillet)
    { j: moisVersJours(10), c: f.automne }, // automne (octobre)
    { j: moisVersJours(1), c: f.hiver }, // hiver (janvier) — null si caduc
  ];
  // Trouve le segment [i, i+1] contenant `jours` (ordre cyclique).
  let i0 = pts.length - 1;
  for (let i = 0; i < pts.length; i++) {
    if (deltaCycle(jours, pts[i].j) >= 0 && deltaCycle(pts[(i + 1) % 4].j, jours) > 0) {
      i0 = i;
      break;
    }
  }
  const i1 = (i0 + 1) % 4;
  const span = deltaCycle(pts[i1].j, pts[i0].j);
  const t = smoothstep(deltaCycle(jours, pts[i0].j) / (span || 1));

  const colA = pts[i0].c;
  const colB = pts[i1].c;
  if (colA && colB) {
    out.set(colA).lerp(_c1.set(colB), t);
  } else if (colA) {
    // Entrée dans l'hiver (caduc) : glisse continue vers le brun des rameaux.
    out.set(colA).lerp(_c2.set('#6e553a'), t);
  } else if (colB) {
    // Sortie de l'hiver (caduc) : brun → couleur de printemps, en continu.
    out.set('#6e553a').lerp(_c1.set(colB), t);
  } else {
    out.set('#6e553a');
  }
  return out;
}

/** Intensité de floraison 0..1 (cloche sur les mois de floraison). */
export function intensiteFloraison(plante, jours, climatId) {
  const mois = plante.moisFloraison || [];
  if (!mois.length) return 0;
  // Décalage climatique : sous climat plus chaud que la référence, la
  // floraison est avancée ; sous climat froid, retardée (continu, sans saut).
  const decal = climatId ? decalageFloraison(climatId, jours) : 0;
  const joursDecales = jours - decal;
  let max = 0;
  for (const m of mois) {
    max = Math.max(max, cloche(joursDecales, moisVersJours(m), 13)); // ~2 semaines de montée/descente
  }
  return max;
}

/** Intensité de fructification 0..1. */
export function intensiteFruits(plante, jours) {
  const mois = plante.moisFructification || [];
  if (!mois.length) return 0;
  let max = 0;
  for (const m of mois) {
    max = Math.max(max, cloche(jours, moisVersJours(m), 16));
  }
  return max;
}

/**
 * Neige sur branches 0..1 : hiver montagnard simulé de façon générique —
 * présent quand la masse foliaire d'un caduc est nulle (déc–fév), avec
 * montée/descente progressives.
 */
export function intensiteNeige(plante, jours) {
  if (!plante.caduc) return 0; // un persistant enneigé reste majoritairement vert
  const debutNeige = moisVersJours(12) + 5; // ~5 déc
  const finNeige = moisVersJours(2) + 10; // ~20 fév
  const dDebut = deltaCycle(jours, debutNeige);
  const dFin = deltaCycle(jours, finNeige);
  if (dDebut >= 0 && dFin <= 0) {
    const span = deltaCycle(finNeige, debutNeige);
    const t = Math.min(dDebut / (span * 0.25), (0 - dFin) / (span * 0.25), 1);
    return smoothstep(Math.max(0, t));
  }
  return 0;
}

/**
 * Nom de stade descriptif (pour HUD / debug), cohérent avec les états ci-dessus.
 */
export function nomStade(plante, jours) {
  if (intensiteNeige(plante, jours) > 0.5) return 'dormance (neige)';
  const feuilles = masseFoliaire(plante, jours);
  if (feuilles > 0 && feuilles < 0.45) {
    return jours < moisVersJours(7) ? 'débourrement' : 'chute des feuilles';
  }
  if (intensiteFloraison(plante, jours) > 0.35) return 'floraison';
  if (intensiteFruits(plante, jours) > 0.35) return 'fructification';
  if (feuilles <= 0) return 'dormance';
  return 'végétation';
}

/**
 * État complet d'une plante pour une date — c'est le contrat que consomme le
 * moteur de rendu (plantInstances.js).
 * `climatId` optionnel : module la masse foliaire et la floraison selon la
 * compatibilité de l'espèce avec le climat (vigueur continue 0..1).
 */
export function etatPlante(plante, jours, climatId) {
  const vig = climatId ? vigueur(plante, climatId, jours) : 1;
  const masseBrute = masseFoliaire(plante, jours);
  // Une plante qui dépérit garde au plus 65 % de sa masse foliaire normale.
  const masse = masseBrute * (0.35 + 0.65 * vig);
  const floraison = intensiteFloraison(plante, jours, climatId) * vig;
  const fruits = intensiteFruits(plante, jours) * vig;
  const neige = intensiteNeige(plante, jours);
  const couleur = couleurFeuillage(plante, jours, new THREE.Color());
  // Feuillage d'une plante souffreteuse : tiré vers le brun-jaune (stress).
  if (vig < 0.7) {
    const stress = (0.7 - vig) / 0.7;
    couleur.lerp(_stress, stress * 0.55);
  }
  return {
    masseFoliaire: masse,
    floraison,
    fruits,
    neige,
    couleur,
    vigueur: vig,
    stade: nomStade(plante, jours),
  };
}

const _stress = new THREE.Color('#9a8a4a');

export { etatSoleil } from './sun.js';
