// Soleil — version propre. Voir seasons.js pour le modèle saisonnier complet.
import * as THREE from 'three';
import { DAYS_PER_YEAR } from './simulationClock.js';

const ZENITH_HIVER = new THREE.Color('#ffd9a8');
const ZENITH_ETE = new THREE.Color('#fff4de');
const BAS_HORIZON = new THREE.Color('#ff9d5c');
const NUIT = new THREE.Color('#aebfff');

const _z = new THREE.Color();
const _c = new THREE.Color();

export function smoothstep01(t) {
  t = Math.min(1, Math.max(0, t));
  return t * t * (3 - 2 * t);
}

/**
 * Position/couleur/intensité du soleil pour (jours 0..365, heure 0..24).
 * Latitude ~46.5°N : journée de ~8h fin décembre, ~15.5h fin juin.
 */
export function etatSoleil(jours, heure) {
  const fractionAnnee = jours / DAYS_PER_YEAR;
  const declinaison = 23.44 * Math.sin(2 * Math.PI * (fractionAnnee - 80 / DAYS_PER_YEAR)) * (Math.PI / 180);
  const latitude = (46.5 * Math.PI) / 180;

  // Demi-jour en radians d'angle horaire : cos H0 = -tan φ · tan δ
  const cosH0 = -Math.tan(latitude) * Math.tan(declinaison);
  const H0 = Math.acos(Math.min(1, Math.max(-1, cosH0)));
  const demiJourHNorm = (H0 / Math.PI) * 12; // demi-journée en heures (H0 ∈ 0..π → 0..12h)
  const dureeJourH = demiJourHNorm * 2;

  // Angle horaire courant : 15°/h, midi = 0 (H ∈ -π..π sur 24h)
  const H = ((heure - 12) * Math.PI) / 12;
  const jour = Math.abs(H) < H0;

  // Élévation sin(alt) exacte
  const sinAlt = Math.sin(latitude) * Math.sin(declinaison)
    + Math.cos(latitude) * Math.cos(declinaison) * Math.cos(H);
  const alt = Math.asin(Math.min(1, Math.max(-1, sinAlt)));

  // Azimut (approx) : est le matin, ouest le soir
  const azimut = H; // -H0..H0 sur la journée

  const rayon = 120;
  const direction = new THREE.Vector3(
    Math.sin(azimut) * rayon,
    Math.max(Math.sin(alt), 0.05) * rayon,
    -Math.cos(azimut) * rayon,
  );

  if (!jour || alt <= 0.02) {
    return {
      direction,
      intensite: 0.05,
      couleur: NUIT.clone(),
      dureeJourH,
      nuit: true,
      hauteurNorm: 0,
    };
  }

  const hauteurNorm = Math.sin(alt); // 0 horizon → 1 zénith
  const chaleurEte = smoothstep01((Math.sin(declinaison) + 1) / 2);
  const zenith = _z.copy(ZENITH_HIVER).lerp(ZENITH_ETE, chaleurEte);
  const couleur = _c.copy(BAS_HORIZON).lerp(zenith, smoothstep01(Math.min(hauteurNorm * 2.4, 1)));
  const intensite = 0.35 + hauteurNorm * 1.55;

  return { direction, intensite, couleur, dureeJourH, nuit: false, hauteurNorm };
}
