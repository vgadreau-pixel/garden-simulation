// Horloge de simulation : date/heure courantes, vitesses d'accélération,
// scrubbing (saut direct à n'importe quel jour de l'année).
//
// Représentation interne : temps continu en jours décimaux (0.0 = 1er janvier
// 00h00, 364.99… = 31 décembre 23h59). Une année de simulation = 365 jours.
// Le scrubbing et les vitesses manipulent ce nombre : aucune transition
// brutale n'est possible, tout déplacement est continu par construction.
import { saisonDuMois } from './data/plants.js';
import { facteurCroissance } from './climate.js';

export const DAYS_PER_YEAR = 365;
export const SECONDS_PER_DAY = 86400;

/**
 * Vitesses de simulation disponibles.
 *  - `label`           : texte du bouton
 *  - `daysPerSecond`   : jours de simulation écoulés par seconde réelle
 *    (x1 temps réel = 1/86400 j/s ; 1 jour/s ; 1 semaine/s = 7 j/s ;
 *     1 mois/s = 30 j/s)
 */
export const SPEEDS = [
  { id: 'pause', label: '⏸ Pause', daysPerSecond: 0 },
  { id: 'x1', label: '▶ ×1 temps réel', daysPerSecond: 1 / SECONDS_PER_DAY },
  { id: 'jour', label: '⏩ 1 jour/s', daysPerSecond: 1 },
  { id: 'semaine', label: '⏩⏩ 1 semaine/s', daysPerSecond: 7 },
  { id: 'mois', label: '⏩⏩⏩ 1 mois/s', daysPerSecond: 30 },
];

/** Vitesse de base ×1 en jours de simulation par seconde de maturité : la
 * croissance pluri-annuelle progresse à raison de 0,01 de maturité/jour,
 * modulée ensuite par le facteur de croissance du climat. */
export const MATURITE_PAR_JOUR = 0.01;

// Découpage des frames lentes en sous-pas (voir SimulationClock.tick).
const MAX_STEP_MS = 250;
const MAX_STEPS = 4;

const MS_PER_DAY = SECONDS_PER_DAY * 1000;

// Formatage lisible de la date/heure de simulation.
const MOIS_NOMS = [
  'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
];
const SAISON_LABEL = {
  printemps: 'Printemps',
  ete: 'Été',
  automne: 'Automne',
  hiver: 'Hiver',
};

/** Convertit un temps continu en jours → objet Date JS (année fixe 2026, non bissextile). */
export function jourVersDate(jours) {
  return new Date(Date.UTC(2026, 0, 1) + jours * MS_PER_DAY);
}

/** Convertit une Date JS (année quelconque) → temps continu en jours 0..365. */
export function dateVersJours(date) {
  const debut = Date.UTC(date.getUTCFullYear(), 0, 1);
  return (date.getTime() - debut) / MS_PER_DAY;
}

/**
 * SimulationClock — source de vérité du temps pour tout le jeu.
 * Usage :
 *   const clock = new SimulationClock(new Date('2026-03-20T08:00'));
 *   clock.tick(realDeltaMs);        // à chaque frame
 *   clock.setSpeed('semaine');      // bouton de vitesse
 *   clock.scrubTo(150.5);           // slider de date (jour 0..365)
 */
export class SimulationClock {
  /**
   * @param {Date} [dateInitiale] date de départ (défaut : 1er avril, 10h)
   * @param {string} [climatInitial] identifiant de climat (défaut : 'tempre')
   */
  constructor(dateInitiale, climatInitial) {
    this.jours = dateInitiale ? dateVersJours(dateInitiale) : 90 + 10 / 24; // ~1er avril 10h
    this.speedIndex = 1; // x1 temps réel par défaut
    this.speedId = 'x1';
    this.climat = climatInitial || 'tempre';
    this.instances = []; // plantes dont la maturité suit le climat (croissance)
  }

  /** Change le climat : la météo, la vigueur et les floraisons s'adaptent. */
  setClimat(id) {
    this.climat = id;
  }

  get daysPerSecond() {
    return SPEEDS[this.speedIndex].daysPerSecond;
  }

  get paused() {
    return this.daysPerSecond === 0;
  }

  /** Choisit une vitesse par id parmi SPEEDS ('pause' | 'x1' | 'jour' | 'semaine' | 'mois'). */
  setSpeed(id) {
    const i = SPEEDS.findIndex((s) => s.id === id);
    if (i >= 0) {
      this.speedIndex = i;
      this.speedId = id;
    }
    return this.speedId;
  }

  /**
   * Avance l'horloge. @param {number} deltaMs millisecondes réelles écoulées.
   * Le temps de simulation boucle sur l'année (365 jours) sans à-coup :
   * 365.2 → 0.2, la végétation hivernale redevient printanière en continu.
   *
   * Les frames très lentes (machine chargée, onglet throttled, rendu
   * logiciel) sont découpées en sous-pas de 250 ms max (4 au plus, soit
   * 1 s de temps réel par frame) : la vitesse nominale est ainsi préservée
   * même à 2-3 fps, tout en plafonnant le rattrapage après un gel long.
   */
  tick(deltaMs) {
    if (this.paused || deltaMs <= 0) return;
    let reste = Math.min(deltaMs, MAX_STEP_MS * MAX_STEPS);
    while (reste > 0) {
      const pas = Math.min(reste, MAX_STEP_MS);
      reste -= pas;
      this._avancer(pas);
    }
  }

  /** Avance d'un sous-pas (≤ 250 ms) : horloge + croissance des plantes. */
  _avancer(deltaMs) {
    const avanceJours = (deltaMs / 1000) * this.daysPerSecond;
    this.jours = mod365(this.jours + avanceJours);
    // Croissance pluri-annuelle modulée par le climat : chaque plante gagne
    // (ou perd, sous climat inadapté) un peu de maturité.
    if (this.instances.length) {
      const facteur = facteurCroissance(this.climat, this.jours);
      const deltaMaturite = (avanceJours * MATURITE_PAR_JOUR) * facteur;
      for (const inst of this.instances) {
        inst.maturite = Math.min(1, Math.max(0, inst.maturite + deltaMaturite));
      }
    }
  }

  /**
   * Scrubbing : saute directement au jour demandé (0..365, décimales = heure).
   * Appelé par le slider ; le rendu interpelle ensuite les états interpolés,
   * donc même un saut de 6 mois est rendu comme un état cohérent (pas de
   * transition animée parasite — l'état cible est affiché immédiatement).
   */
  scrubTo(jours) {
    this.jours = mod365(jours);
  }

  /** Date JS courante de la simulation. */
  get date() {
    return jourVersDate(this.jours);
  }

  /** Fraction de l'année écoulée 0..1 (0 = 1er jan 00h). */
  get fractionAnnee() {
    return this.jours / DAYS_PER_YEAR;
  }

  /** Heure locale de simulation 0..24 (pour la position du soleil). */
  get heure() {
    return this.jours % 1 * 24;
  }

  /** {jour, mois, heure, minutes, saison, label} pour l'affichage HUD. */
  get etat() {
    const d = this.date;
    const jour = d.getUTCDate();
    const mois = d.getUTCMonth() + 1;
    const h = Math.floor(this.heure);
    const m = Math.floor((this.heure - h) * 60);
    const saison = saisonDuMois(mois);
    const hh = String(h).padStart(2, '0');
    const mm = String(m).padStart(2, '0');
    return {
      jour,
      mois,
      heure: h,
      minutes: m,
      saison,
      label: `${jour} ${MOIS_NOMS[mois - 1]} · ${hh}:${mm} · ${SAISON_LABEL[saison]}`,
    };
  }
}

function mod365(x) {
  return ((x % DAYS_PER_YEAR) + DAYS_PER_YEAR) % DAYS_PER_YEAR;
}
