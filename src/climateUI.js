// Sélecteur de climat — petit panneau UI en haut à droite.
// Liste les climats de CLIMATS, affiche température / pluie / soleil courants
// et permet de changer de climat à chaud (callback onChange).

import { CLIMATS, CLIMAT_IDS, meteoDuJour } from './climate.js';

const ICONES = {
  tempre: '🍂',
  mediterraneen: '☀️',
  tropical: '🌴',
  continental: '❄️',
  aride: '🏜️',
};

/**
 * @param {HTMLElement} conteneur (ex. document.body)
 * @param {SimulationClock} clock  pour lire les températures au jour courant
 * @param {(climatId: string) => void} onChange appelé quand l'utilisateur change
 * @param {string} climatInitial
 */
export function creerSelecteurClimat(conteneur, clock, onChange, climatInitial) {
  const panneau = document.createElement('div');
  panneau.id = 'climat-panel';

  const titre = document.createElement('div');
  titre.className = 'climat-titre';
  titre.textContent = 'Climat';
  panneau.appendChild(titre);

  const boutons = CLIMAT_IDS.map((id) => {
    const b = document.createElement('button');
    b.className = 'cbtn';
    b.dataset.climat = id;
    b.title = CLIMATS[id].description;
    b.innerHTML = `${ICONES[id] || '🌍'} <span>${CLIMATS[id].label}</span>`;
    b.addEventListener('click', () => {
      onChange(id);
      rafraichir();
    });
    panneau.appendChild(b);
    return b;
  });

  const infos = document.createElement('div');
  infos.id = 'climat-infos';
  panneau.appendChild(infos);

  conteneur.appendChild(panneau);

  function rafraichir() {
    // L'horloge est la source de vérité (le climat peut changer dehors) :
    // on resynchronise l'affichage à chaque rafraîchissement.
    courant = clock.climat;
    for (const b of boutons) b.classList.toggle('active', b.dataset.climat === courant);
    const m = meteoDuJour(courant, clock.jours);
    infos.textContent = `${Math.round(m.temperature)}°C · ☔ ${Math.round(m.precipitation)} mm/m · ☀️ ${m.ensoleillement.toFixed(1)} h/j`;
  }

  let courant = climatInitial;
  rafraichir();

  return {
    /** À appeler chaque frame (ou quelques fois par seconde) pour suivre l'horloge. */
    maj() {
      rafraichir();
    },
    get climat() {
      return courant;
    },
    set climat(id) {
      courant = id;
      rafraichir();
    },
    element: panneau,
  };
}
