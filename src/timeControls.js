// Barre de contrôle du temps : boutons de vitesse + slider de date (scrubber).
// Zéro dépendance DOM. Expose update() pour rafraîchir le HUD date.
import { SPEEDS, DAYS_PER_YEAR, jourVersDate } from './simulationClock.js';

const MOIS_COURTS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'];
const SAISON_CLASSE = {
  printemps: 's-printemps',
  ete: 's-ete',
  automne: 's-automne',
  hiver: 's-hiver',
};

/**
 * @param {HTMLElement} conteneur
 * @param {SimulationClock} clock
 * @param {() => void} [onScrubStart] appelé quand on commence un scrub (pause auto)
 */
export function creerControlesTemps(conteneur, clock, onScrubStart) {
  const barre = document.createElement('div');
  barre.id = 'timebar';

  // ── Boutons de vitesse ──
  const boutons = SPEEDS.map((spd) => {
    const b = document.createElement('button');
    b.className = 'tbtn';
    b.dataset.speed = spd.id;
    b.textContent = spd.label;
    b.title = spd.id === 'pause' ? 'Geler le temps' : `Vitesse : ${spd.label}`;
    b.addEventListener('click', () => {
      clock.setSpeed(spd.id);
      rafraichirBoutons();
    });
    barre.appendChild(b);
    return b;
  });

  // ── Séparateur ──
  const sep = document.createElement('div');
  sep.className = 'tsep';
  barre.appendChild(sep);

  // ── Slider (scrubber) : 365 crans = 1 an ──
  const slider = document.createElement('input');
  slider.type = 'range';
  slider.id = 'dateslider';
  slider.min = '0';
  slider.max = String(DAYS_PER_YEAR);
  slider.step = '0.05';
  slider.value = String(clock.jours);
  slider.title = 'Sauter à n’importe quel jour de l’année';
  slider.addEventListener('input', () => {
    if (onScrubStart) onScrubStart();
    clock.scrubTo(parseFloat(slider.value));
    maj();
  });
  barre.appendChild(slider);

  // ── Date affichée ──
  const dateEl = document.createElement('div');
  dateEl.id = 'datelabel';
  barre.appendChild(dateEl);

  conteneur.appendChild(barre);

  function rafraichirBoutons() {
    for (const b of boutons) b.classList.toggle('active', b.dataset.speed === clock.speedId);
  }

  /** Suit l'horloge : position du slider + libellé de date. Appelé chaque frame. */
  function maj(suivreSlider = !scrubEnCours) {
    dateEl.textContent = clock.etat.label;
    dateEl.className = SAISON_CLASSE[clock.etat.saison] || '';
    if (suivreSlider) slider.value = String(clock.jours);
  }

  let scrubEnCours = false;
  slider.addEventListener('pointerdown', () => { scrubEnCours = true; });
  window.addEventListener('pointerup', () => { scrubEnCours = false; });

  rafraichirBoutons();
  maj();

  return { maj, element: barre };
}

/** Test d'affichage (utilisé par les vérifications CDP). */
export function libelleDate(jours) {
  const d = jourVersDate(jours);
  return `${d.getUTCDate()} ${MOIS_COURTS[d.getUTCMonth()]}`;
}
