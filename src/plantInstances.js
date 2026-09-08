// Instances de plantes du jardin + rendu saisonnier.
//
// Chaque instance = { plante (réf. catalogue), position, rotationY, maturité }.
// La maturité (0..1) pilote le stade de CROISSANCE du catalogue
// (graine → jeune_pousse → mature, échelle 0..1) ; le moteur saisonnier
// pilote ensuite l'aspect annuel (feuilles, fleurs, fruits, neige).
//
// Performance : chaque plante est un petit groupe de meshes low-poly
// (tronc + houppier + fleurs + fruits + neige). Avec ~24 plantes, on reste
// très loin d'un budget de draw calls problématique ; les matériaux sont
// partagés par instance pour que la mise à jour saisonnière soit 1 `color.set`
// + 1 `scale` par organe — aucune reconstruction de géométrie par frame.
import * as THREE from 'three';
import { PLANTES } from './data/plants.js';
import { etatPlante } from './seasons.js';
import { PLOT_SIZE } from './constants.js';
import { majVegetation, habillerInstance } from './vegetation.js';

const COULEUR_BOIS = new THREE.Color('#7a5230');
const COULEUR_BOIS_FROID = new THREE.Color('#8a7460');
const COULEUR_NEO = new THREE.Color('#e8f4ff');

/**
 * Échelle de croissance continue 0..1 à partir des stades du catalogue.
 * Interpolation linéaire entre les paliers echelle[] (0 → 1).
 */
export function echelleCroissance(plante, maturite) {
  const stades = plante.stades || [];
  if (stades.length < 2) return maturite;
  const t = Math.min(1, Math.max(0, maturite)) * (stades.length - 1);
  const i = Math.min(Math.floor(t), stades.length - 2);
  const f = t - i;
  return stades[i].echelle + (stades[i + 1].echelle - stades[i].echelle) * f;
}

/**
 * Peuple le jardin : répartit `n` instances de plantes (choisies dans le
 * catalogue, avec une maturité variée) sur les parcelles libres de la grille.
 * `plantation.matureToute(s)` permet au moteur temporel de tout vieillir d'un coup.
 */
export function creerJardin(scene, { nombre = 24, graine = 7 } = {}) {
  const rng = mulberry32(graine);
  const group = new THREE.Group();
  group.name = 'plantes';

  // Mélange déterministe d'espèces : au moins un représentant par espèce si
  // nombre ≥ PLANTES.length, sinon tirage.
  const especes = [...PLANTES];
  for (let i = especes.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [especes[i], especes[j]] = [especes[j], especes[i]];
  }

  // Positions : quinconce sur les centres de parcelles (1 plante par parcelle,
  // on en parcourt un sous-ensemble), au milieu de la terre cultivée.
  const spots = [];
  const pas = PLOT_SIZE / 2.2;
  for (let a = 0; a < 5; a++) {
    for (let b = 0; b < 5; b++) {
      spots.push(new THREE.Vector3((a - 2) * pas * 1.9, 0, (b - 2) * pas * 1.9));
    }
  }
  for (let i = spots.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [spots[i], spots[j]] = [spots[j], spots[i]];
  }

  const instances = [];
  const n = Math.min(nombre, especes.length, spots.length);
  for (let i = 0; i < n; i++) {
    const plante = especes[i % especes.length];
    const pos = spots[i];
    const maturite = 0.55 + rng() * 0.45; // jardin déjà établi, quelques jeunes
    const inst = creerInstancePlante(plante, pos, maturite, rng());
    group.add(inst.group);
    instances.push(inst);
  }

  scene.add(group);
  return { group, instances };
}

/** Crée une plante (groupe de meshes + matériaux pilotés par le moteur saisonnier). */
export function creerInstancePlante(plante, position, maturite, rotationY = 0) {
  const group = new THREE.Group();
  group.position.copy(position);

  // ── Matériaux (1 jeu par instance : mis à jour par applyEtat) ──
  const matTronc = new THREE.MeshStandardMaterial({ color: COULEUR_BOIS.clone(), roughness: 0.95 });
  const matFeuilles = new THREE.MeshStandardMaterial({ color: 0x3f7d2c, roughness: 0.85 });
  const matFleurs = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.7 });
  const matFruits = new THREE.MeshStandardMaterial({ color: 0xcc2222, roughness: 0.55 });
  const matNeige = new THREE.MeshStandardMaterial({ color: COULEUR_NEO.clone(), roughness: 0.9, transparent: true, opacity: 0 });

  const baseType = plante.type; // arbre/arbuste : silhouettes différentes

  // ── Tronc ──
  const hTronc = baseType === 'arbre' ? 1.6 : baseType === 'arbuste' ? 0.5 : 0.22;
  const tronc = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.14, hTronc, 6), matTronc);
  tronc.position.y = hTronc / 2;
  tronc.castShadow = true;
  group.add(tronc);

  // ── Houppier (feuillage) : 2-3 sphères low-poly ──
  const feuilles = new THREE.Group();
  feuilles.position.y = hTronc;
  const nBoules = baseType === 'arbre' ? 3 : baseType === 'arbuste' ? 3 : 1;
  const geoFeuille = new THREE.IcosahedronGeometry(1, 1); // partagée par boules
  for (let i = 0; i < nBoules; i++) {
    const r = baseType === 'fleur' ? 0.18 : baseType === 'legume' ? 0.28 : 0.75 - i * 0.12;
    const m = new THREE.Mesh(geoFeuille, matFeuilles);
    m.position.set((i - (nBoules - 1) / 2) * 0.55, i === 0 ? 0 : 0.45 - i * 0.12, (i % 2 ? 0.18 : -0.22));
    m.scale.setScalar(r);
    m.castShadow = true;
    feuilles.add(m);
  }
  group.add(feuilles);

  // ── Fleurs : petites sphères émergent du houppier ──
  const fleurs = new THREE.Group();
  fleurs.position.y = hTronc;
  const geoFleur = new THREE.IcosahedronGeometry(0.14, 0);
  for (let i = 0; i < 7; i++) {
    const m = new THREE.Mesh(geoFleur, matFleurs);
    const ang = (i / 7) * Math.PI * 2;
    m.position.set(Math.cos(ang) * 0.7, 0.25 + (i % 3) * 0.22, Math.sin(ang) * 0.7);
    m.visible = false;
    fleurs.add(m);
  }
  group.add(fleurs);

  // ── Fruits ──
  const fruits = new THREE.Group();
  fruits.position.y = hTronc;
  const geoFruit = new THREE.IcosahedronGeometry(0.11, 0);
  for (let i = 0; i < 6; i++) {
    const m = new THREE.Mesh(geoFruit, matFruits);
    const ang = (i / 6) * Math.PI * 2 + 0.4;
    m.position.set(Math.cos(ang) * 0.55, 0.05 + (i % 2) * 0.3, Math.sin(ang) * 0.55);
    m.visible = false;
    fruits.add(m);
  }
  group.add(fruits);

  // ── Neige : calottes blanches posées sur le houppier ──
  const neige = new THREE.Group();
  neige.position.y = hTronc;
  const geoNeige = new THREE.SphereGeometry(1, 8, 5, 0, Math.PI * 2, 0, Math.PI / 2.4);
  for (let i = 0; i < nBoules; i++) {
    const r = baseType === 'arbre' ? 0.78 - i * 0.12 : baseType === 'arbuste' ? 0.5 : 0.22;
    const m = new THREE.Mesh(geoNeige, matNeige);
    m.position.copy(feuilles.children[i].position);
    m.scale.setScalar(r);
    m.visible = false;
    neige.add(m);
  }
  group.add(neige);

  const echelleBase = plante.tailleMatureM
    ? Math.max(0.5, Math.min(1.4, plante.tailleMatureM / 6)) // arbres ~1.3, fleurs ~0.5
    : 0.5;
  const instance = {
    plante,
    group,
    maturite,
    mats: { matTronc, matFeuilles, matFleurs, matFruits, matNeige },
    parties: { feuilles, fleurs, fruits, neige, tronc },
    echelleBase,
    dernierEtat: null,
  };
  return instance;
}

/**
 * Applique l'état saisonnier calculé (etatPlante) à une instance.
 * Tout est interpolé en amont (cloches + smoothstep) : ici de simples
 * affectations continues — aucune transition brutale possible.
 */
export function appliquerEtat(instance, jours, climatId) {
  const et = etatPlante(instance.plante, jours, climatId);
  const { mats, parties } = instance;

  // Croissance (stades du catalogue)
  const ech = echelleCroissance(instance.plante, instance.maturite);
  const s = Math.max(0.05, ech) * instance.echelleBase * (1 + et.masseFoliaire * 0.12);
  instance.group.scale.setScalar(s);
  parties.feuilles.visible = et.masseFoliaire > 0.02 && !instance.vegActif;

  // ── Modèle 3D texturé (végétation réaliste) : teinte + masse foliaire ──
  // Le feuillage rétrécit avec la masse (arbre nu en hiver), la teinte suit
  // le feuillage saisonnier ; tronc, fleurs et fruits sont conservés.
  if (instance.vegActif) {
    instance.veg.groupe.visible = instance.veg.leafMats.every((m) => m.opacity !== 0);
    majVegetation(instance, et);
  }

  // Fleurs : visibles et grossissantes pendant la floraison
  parties.fleurs.visible = et.floraison > 0.05;
  mats.matFleurs.color.set(instance.plante.couleurFloraison || '#ffffff');
  mats.matFleurs.opacity = Math.min(1, et.floraison * 1.6);
  mats.matFleurs.transparent = et.floraison < 1;
  const sf = Math.max(0.001, et.floraison);
  for (const m of parties.fleurs.children) m.scale.setScalar(sf);

  // Fruits
  parties.fruits.visible = et.fruits > 0.05;
  mats.matFruits.color.set(instance.plante.couleurFruit || '#cc2222');
  const sr = Math.max(0.001, et.fruits * 1.1);
  for (const m of parties.fruits.children) m.scale.setScalar(sr);

  // Neige sur branches
  parties.neige.visible = et.neige > 0.03;
  mats.matNeige.opacity = et.neige;
  mats.matNeige.transparent = true;
  for (const m of parties.neige.children) m.scale.setScalar(1 + et.neige * 0.15);

  // Bois un peu plus froid/matté en hiver
  mats.matTronc.color.copy(COULEUR_BOIS).lerp(COULEUR_BOIS_FROID, Math.max(et.neige, 1 - et.masseFoliaire) * 0.5);

  instance.dernierEtat = et;
  return et;
}

/** RNG déterministe (mulberry32). */
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
