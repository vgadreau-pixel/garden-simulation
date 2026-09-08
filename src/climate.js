// Système de climat — détermine la météo et module la simulation.
//
// Un climat décrit, pour chaque mois de l'année :
//   - temperatureMoyenneC : moyenne mensuelle (°C)
//   - precipitationsMm    : cumul mensuel approximatif (mm)
//   - ensoleillementH     : moyenne mensuelle d'ensoleillement (heures/jour)
// De ces triplets découlent :
//   - la météo courante (état interpolé en continu, sans à-coup) ;
//   - les particules affichées (pluie, neige, brume, éclat du soleil) ;
//   - la vigueur des plantes (facteur de croissance) et le décalage
//     des dates de floraison (somme de température, modèle simplifié).
//
// Tout est construit par interpolation linéaire entre centres de mois :
// aucune valeur ne saute, le rendu reste continu par construction.
// (La boucle du DeltaT ci-dessous est stable pour 12 points cycliques.)

/** Interpolation linéaire. */
function lerp(a, b, t) {
  return a + (b - a) * t;
}

/** 12 valeurs mensuelles → valeur continue pour jours ∈ 0..365. */
export function valeurAnnuelle(mensuel, jours) {
  const fm = (jours / 365) * 12; // position continue en "mois"
  const i0 = Math.floor(fm);
  const i1 = (i0 + 1) % 12;
  const t = fm - i0;
  return lerp(mensuel[i0 % 12], mensuel[i1], t);
}

/**
 * Climats disponibles. Les températures/précipitations/ensoleillement sont
 * des moyennes mensuelles plausibles (nord de la France pour océanique /
 * continental, pourtour méditerranéen pour méditerranéen / aride).
 */
export const CLIMATS = {
  tempre: {
    label: 'Tempéré',
    description: 'Quatre saisons marquées, pluie régulière, hivers frais.',
    temperatureMoyenneC: [3, 4, 7, 10, 14, 18, 20, 20, 17, 12, 7, 4],
    precipitationsMm: [60, 50, 55, 55, 65, 55, 55, 55, 55, 70, 70, 70],
    ensoleillementH: [2.2, 3.1, 4.4, 5.6, 6.6, 7.4, 7.8, 7.2, 5.9, 4.1, 2.6, 1.9],
  },
  mediterraneen: {
    label: 'Méditerranéen',
    description: 'Étés chauds et secs, hivers doux et pluvieux.',
    temperatureMoyenneC: [7, 8, 11, 14, 18, 22, 25, 25, 21, 17, 11, 8],
    precipitationsMm: [65, 55, 50, 55, 40, 20, 10, 15, 45, 80, 75, 70],
    ensoleillementH: [4.5, 5.2, 6.5, 7.6, 8.8, 9.9, 10.8, 9.8, 8.0, 6.2, 4.7, 4.2],
  },
  tropical: {
    label: 'Tropical',
    description: 'Chaud et humide toute l’année, saison des pluies marquée.',
    temperatureMoyenneC: [26, 26, 27, 28, 28, 27, 27, 27, 27, 27, 27, 26],
    precipitationsMm: [180, 170, 190, 200, 190, 160, 120, 100, 110, 140, 170, 190],
    ensoleillementH: [6.0, 6.2, 6.4, 6.6, 6.8, 6.6, 6.4, 6.2, 6.0, 5.8, 5.6, 5.8],
  },
  continental: {
    label: 'Continental / Montagnard',
    description: 'Hivers longs et froids, étés courts, neige abondante.',
    temperatureMoyenneC: [-4, -3, 1, 6, 11, 15, 17, 16, 12, 7, 2, -2],
    precipitationsMm: [55, 50, 55, 60, 75, 85, 85, 80, 70, 65, 65, 60],
    ensoleillementH: [2.0, 2.8, 4.0, 5.2, 6.2, 7.0, 7.4, 6.8, 5.4, 3.6, 2.2, 1.6],
  },
  aride: {
    label: 'Aride',
    description: 'Très chaud et sec, ciel dégagé, lumière écrasante.',
    temperatureMoyenneC: [12, 14, 17, 21, 26, 31, 34, 34, 29, 23, 17, 13],
    precipitationsMm: [20, 18, 15, 10, 5, 2, 1, 2, 5, 12, 18, 22],
    ensoleillementH: [7.5, 8.0, 8.6, 9.2, 10.0, 10.8, 11.2, 10.8, 9.4, 8.4, 7.8, 7.4],
  },
};

export const CLIMAT_IDS = Object.keys(CLIMATS);
export const CLIMAT_DEFAUT = 'tempre';

/** Validité d'un identifiant de climat. */
export function climatValide(id) {
  return Object.prototype.hasOwnProperty.call(CLIMATS, id);
}

/** État climatique continu pour un climat et un jour de l'année (0..365). */
export function etatClimat(climatId, jours) {
  const c = CLIMATS[climatId] || CLIMATS[CLIMAT_DEFAUT];
  const temperature = valeurAnnuelle(c.temperatureMoyenneC, jours);
  const precipitation = valeurAnnuelle(c.precipitationsMm, jours);
  const ensoleillement = valeurAnnuelle(c.ensoleillementH, jours);
  return {
    id: c === c ? climatId : CLIMAT_DEFAUT,
    label: c.label,
    temperature,
    precipitation,
    ensoleillement,
  };
}

/**
 * Nébulosité 0..1 (0 = ciel dégagé) : croît avec la pluie, décroît avec
 * l'ensoleillement. Lisse, continue sur l'année.
 */
export function nebulosite(etat) {
  const indPluie = Math.min(1, etat.precipitation / 170);
  const indSoleil = Math.min(1, etat.ensoleillement / 11);
  return Math.min(1, Math.max(0, indPluie * 1.1 - indSoleil * 0.45 + 0.25));
}

/**
 * Météo instantanée : intensité de pluie, de neige, de brume, éclat solaire.
 * Tout ∈ 0..1, continu (dérive de valeurs mensuelles interpolées).
 * La neige nécessite température ≤ ~1°C ; la pluie nécessite assez d'eau.
 */
export function meteoDuJour(climatId, jours) {
  const et = etatClimat(climatId, jours);
  // Fenêtre de pluie : suit la courbe annuelle des précipitations.
  const pluie = Math.min(1, Math.max(0, (et.precipitation - 30) / 100));
  // Fenêtre de neige : n'apparaît que près/ sous 0°C.
  const froid = Math.max(0, (1.5 - et.temperature) / 8);
  const neige = froid * Math.min(1, et.precipitation / 40);
  // Brume : air humide, frais, peu ensoleillé (automne/hiver océanique).
  const brume = Math.min(1,
    Math.max(0, (1 - et.ensoleillement / 6) * Math.max(0, (12 - et.temperature) / 12) * Math.min(1, et.precipitation / 90)));
  // Éclat solaire : élevé si beaucoup d'heures de soleil et peu de pluie.
  const eclat = Math.min(1, Math.max(0, (et.ensoleillement - 1.5) / 8) * (1 - pluie * 0.35));
  return { temperature: et.temperature, precipitation: et.precipitation, ensoleillement: et.ensoleillement, pluie, neige, brume, eclat, label: et.label };
}

/**
 * Vigueur d'une espèce sous un climat : facteur de croissance multiplié à
 * la vitesse de pousse et à la masse foliaire finale.
 *  - 1.0  : climat listé dans plante.climats → prospère ;
 *  - sinon, pénalité liée à l'écart de température entre climat courant et
 *    le « climat de référence » le plus proche de l'espèce, plafonnée : les
 *    espèces réellement inadaptées (olivier en continental, etc.) dépérissent.
 * Retour ∈ 0..1.
 */
export function vigueur(plante, climatId, jours) {
  if (plante.climats.includes(climatId)) return 1;
  const cur = etatClimat(climatId, jours);
  // Climat de référence le plus proche en température pour cette espèce.
  let meilleure = null;
  for (const cid of plante.climats) {
    const ref = etatClimat(cid, jours);
    const ecart = Math.abs(ref.temperature - cur.temperature);
    if (!meilleure || ecart < meilleure.ecart) meilleure = { ecart, ref };
  }
  // Pénalité douce dès 3°C d'écart, sévère au-delà de 11°C : les espèces
  // réellement inadaptées (olivier en continental) dépérissent vite.
  const ecart = meilleure ? meilleure.ecart : 10;
  const pen = Math.min(1, Math.max(0, (11 - ecart) / 8));
  return 0.05 + pen * 0.75; // jamais 0 : la plante survit misérablement au mieux
}

/** Étiquette courte de santé (HUD / debug). */
export function santeLabel(vig) {
  if (vig >= 0.95) return 'épanouie';
  if (vig >= 0.6) return 'correcte';
  if (vig >= 0.3) return 'souffreteuse';
  return 'dépérit';
}

/**
 * Décalage de floraison (en jours) induit par le climat : les étés chauds
 * avancent la floraison, les climats froids la retardent. Modèle simple de
 * somme de température : ≈ 6 j de retard par °C manquant au printemps,
 * plafonné à ±25 j. Retourne un offset continu (dépend du jour via la
 * température de fin d'hiver/début printemps, donc varie doucement).
 */
export function decalageFloraison(climatId, jours) {
  const cur = etatClimat(climatId, jours);
  const ref = etatClimat(CLIMAT_DEFAUT, jours);
  const ecart = cur.temperature - ref.temperature;
  return Math.max(-25, Math.min(25, -ecart * 6));
}

/**
 * Vitesse de croissance modulée : sous climat chaud et lumineux, tout pousse
 * plus vite ; sous climat froid, tout ralentit. Facteur multiplicatif 0.4..1.5
 * appliqué à la progression de maturité (moteur temporel).
 */
export function facteurCroissance(climatId, jours) {
  const et = etatClimat(climatId, jours);
  const t = (et.temperature - 5) / 25; // 5°C → 0 ; 30°C → 1
  const s = (et.ensoleillement - 2) / 9; // 2 h → 0 ; 11 h → 1
  return Math.max(0.4, Math.min(1.5, 0.65 + 0.5 * Math.max(0, t) + 0.35 * Math.max(0, s) - 0.25 * Math.max(0, -t)));
}
