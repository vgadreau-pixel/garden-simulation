// Catalogue d'espèces — panneau gauche de sélection avant plantation.
// Liste les 19 espèces du catalogue botanique avec icône de type, nom,
// compatibilité climat ( badge visible quand l'espèce n'aime pas le climat
// courant) et une recherche par nom. La sélection pilote l'outil de plantation.

import { PLANTES, TYPES } from './data/plants.js';
import { CLIMATS } from './climate.js';

const ICONES_TYPE = {
  arbre: '🌳',
  arbuste: '🌿',
  fleur: '🌸',
  legume: '🥕',
};

// Adaptation : l'identifiant de climat du moteur (climate.js) peut différer de
// celui du catalogue (plants.js) — table de correspondance.
const EQUIV_CLIMAT = {
  tempre: 'oceanique',
  mediterraneen: 'mediterraneen',
  tropical: null, // aucune espèce du catalogue n'est tropicale
  continental: 'continental',
  aride: 'mediterraneen', // le plus proche
};

/**
 * @param {HTMLElement} conteneur
 * @param {object} plantation  module plantation.js (especeSelectionnee)
 * @param {object} climateUI   module climateUI.js (climat courant)
 */
export function creerCatalogue(conteneur, plantation, climateUI) {
  const panneau = document.createElement('div');
  panneau.id = 'catalogue-panel';

  const titre = document.createElement('div');
  titre.className = 'catalogue-titre';
  titre.textContent = 'Catalogue';
  panneau.appendChild(titre);

  const recherche = document.createElement('input');
  recherche.type = 'search';
  recherche.id = 'catalogue-recherche';
  recherche.placeholder = 'Rechercher…';
  recherche.addEventListener('input', () => rafraichirFiltre());
  panneau.appendChild(recherche);

  const liste = document.createElement('div');
  liste.id = 'catalogue-liste';
  panneau.appendChild(liste);

  const lignes = PLANTES.map((plante) => {
    const b = document.createElement('button');
    b.className = 'cat-item';
    b.dataset.id = plante.id;
    b.dataset.recherche = plante.nom.toLowerCase();
    b.title = `${plante.nom} — ${ICONES_TYPE[plante.type] || '🌱'} ${plante.type}\n` +
      `Climats : ${plante.climats.map((c) => CLIMATS[c]?.label || c).join(', ')}`;
    b.innerHTML =
      `<span class="cat-icone">${ICONES_TYPE[plante.type] || '🌱'}</span>` +
      `<span class="cat-nom">${plante.nom.replace(/\s*\(.*\)$/, '')}</span>` +
      `<span class="cat-alerte" title="Peu adapté au climat courant">⚠️</span>`;
    b.addEventListener('click', () => selectionner(plante.id));
    liste.appendChild(b);
    return b;
  });

  // Pied du panneau : compteur + bouton « tout arracher »
  const pied = document.createElement('div');
  pied.id = 'catalogue-pied';
  const compteur = document.createElement('span');
  compteur.id = 'catalogue-compteur';
  const btnVider = document.createElement('button');
  btnVider.id = 'catalogue-vider';
  btnVider.textContent = '🗑 Tout arracher';
  btnVider.title = 'Retirer toutes les plantes du jardin';
  btnVider.addEventListener('click', () => {
    plantation.toutRetirer();
    majCompteur();
  });
  pied.appendChild(compteur);
  pied.appendChild(btnVider);
  panneau.appendChild(pied);

  conteneur.appendChild(panneau);

  function selectionner(id) {
    plantation.especeSelectionnee = id;
    rafraichirSelection();
  }

  function rafraichirSelection() {
    for (const b of lignes) {
      b.classList.toggle('selected', b.dataset.id === plantation.especeSelectionnee);
    }
  }

  function rafraichirFiltre() {
    const q = recherche.value.trim().toLowerCase();
    for (const b of lignes) {
      b.style.display = !q || b.dataset.recherche.includes(q) ? '' : 'none';
    }
  }

  /** Alerte « climat inadapté » : recalculée quand le climat change. */
  function rafraichirAlertes() {
    const climatMoteur = climateUI.climat;
    const climatCatalogue = EQUIV_CLIMAT[climatMoteur] ?? climatMoteur;
    for (const b of lignes) {
      const plante = PLANTES.find((p) => p.id === b.dataset.id);
      b.classList.toggle('inadapte', !plante.climats.includes(climatCatalogue));
    }
  }

  function majCompteur(n) {
    const { total } = plantation.compter();
    compteur.textContent = `${n ?? total} végétal${(n ?? total) > 1 ? 'aux' : ''} planté${(n ?? total) > 1 ? 's' : ''}`;
  }

  rafraichirSelection();
  rafraichirAlertes();
  majCompteur();

  return {
    element: panneau,
    rafraichirAlertes,
    majCompteur,
    // TYPES est réexporté pour d'éventuels tests.
    types: TYPES,
  };
}
