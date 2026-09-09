/**
 * jardin-saisons — Catalogue botanique de plantes réelles
 * --------------------------------------------------------
 * Source de vérité des données qui pilotent le rendu saisonnier.
 * Consumeurs : moteur temporel (t_44f07608), rendu 3D, palette UI.
 *
 * Formats :
 *  - Couleurs : hexadécimal "#RRGGBB" (compatible THREE.Color).
 *  - Mois : tableau d'entiers 1..12 (janvier=1, décembre=12), [] si aucun.
 *  - Échelle : facteur multiplicatif par rapport à la taille mature (0..1).
 *  - Saison : "printemps" (3,4,5), "été" (6,7,8), "automne" (9,10,11), "hiver" (12,1,2).
 *
 * Schéma d'une entrée : voir docs de PLANT_SCHEMA dans validate.js.
 */

export const CLIMATS = {
  oceanique: {
    label: 'Océanique',
    zonesUsda: [7, 8, 9],
    description: 'Hivers doux et humides, étés tempérés (ex. façade atlantique).',
  },
  continental: {
    label: 'Continental',
    zonesUsda: [4, 5, 6],
    description: 'Hivers froids, étés chauds, écarts saisonniers marqués.',
  },
  mediterraneen: {
    label: 'Méditerranéen',
    zonesUsda: [9, 10],
    description: 'Étés secs et chauds, hivers doux.',
  },
  montagne: {
    label: 'Montagne',
    zonesUsda: [3, 4, 5],
    description: 'Hivers longs et neigeux, étés courts.',
  },
};

export const TYPES = ['arbre', 'arbuste', 'fleur', 'legume', 'roche', 'eau'];

export const SAISONS = ['printemps', 'ete', 'automne', 'hiver'];

/** Saison (clé SAISONS) pour un numéro de mois 1..12. */
export function saisonDuMois(mois) {
  if (mois >= 3 && mois <= 5) return 'printemps';
  if (mois >= 6 && mois <= 8) return 'ete';
  if (mois >= 9 && mois <= 11) return 'automne';
  return 'hiver';
}

/** Stades de croissance — communs à toutes les espèces. */
export const STADES = ['graine', 'jeune_pousse', 'mature'];

/**
 * Rusticité : tolérance au froid.
 *  - zoneUsdaMin : zone USDA la plus froide supportée (3 = très rustique, 10 = gélif).
 *  - temperatureMinC : température minimale de survie en °C.
 *  - label : libellé affichable.
 */
export const RUSTICITE = {
  tres_rustique: { label: 'Très rustique', temperatureMinC: -30 },
  rustique: { label: 'Rustique', temperatureMinC: -15 },
  semi_rustique: { label: 'Semi-rustique', temperatureMinC: -7 },
  fragile: { label: 'Fragile (gélif)', temperatureMinC: 0 },
};

/** 16 espèces réelles. Ordonnées par type puis nom. */
export const PLANTES = [
  // ── Arbres ──────────────────────────────────────────────────────────────
  {
    id: 'cerisier',
    nom: 'Cerisier (Prunus avium)',
    type: 'arbre',
    climats: ['oceanique', 'continental'],
    tailleMatureM: 8,
    stades: [
      { nom: 'graine', couleur: '#6b4423', echelle: 0.0, description: 'Noyau enfoui' },
      { nom: 'jeune_pousse', couleur: '#8fbf5f', echelle: 0.18, description: 'Plant fin, écorce lisse verte' },
      { nom: 'mature', couleur: '#7a5230', echelle: 1.0, description: 'Tronc brun-rouge, houppier large' },
    ],
    moisFloraison: [3, 4],
    couleurFloraison: '#f7c5d8',
    feuillage: {
      printemps: '#8fc94b',
      ete: '#3f7d2c',
      automne: '#d98032',
      hiver: null, // caduc : pas de feuilles
    },
    moisFructification: [6, 7],
    couleurFruit: '#b1122e',
    caduc: true,
    rusticite: 'rustique',
    zoneUsdaMin: 5,
  },
  {
    id: 'erable_japonais',
    nom: 'Érable du Japon (Acer palmatum)',
    type: 'arbre',
    climats: ['oceanique', 'montagne'],
    tailleMatureM: 5,
    stades: [
      { nom: 'graine', couleur: '#8c3b2e', echelle: 0.0, description: 'Samarre ailée rougeâtre' },
      { nom: 'jeune_pousse', couleur: '#b04a3a', echelle: 0.15, description: 'Jeunes rameaux rouges' },
      { nom: 'mature', couleur: '#6e4a35', echelle: 1.0, description: 'Écorce grise, port étalé' },
    ],
    moisFloraison: [5],
    couleurFloraison: '#c9304a',
    feuillage: {
      printemps: '#c0392b',
      ete: '#4a7c3f',
      automne: '#e25822',
      hiver: null,
    },
    moisFructification: [9, 10],
    couleurFruit: '#a33b2e',
    caduc: true,
    rusticite: 'rustique',
    zoneUsdaMin: 5,
  },
  {
    id: 'sapin',
    nom: 'Sapin blanc (Abies alba)',
    type: 'arbre',
    climats: ['montagne', 'continental'],
    tailleMatureM: 20,
    stades: [
      { nom: 'graine', couleur: '#5b4632', echelle: 0.0, description: 'Graine ailée' },
      { nom: 'jeune_pousse', couleur: '#3e6b2f', echelle: 0.1, description: 'Plant conique sombre' },
      { nom: 'mature', couleur: '#4d5a4a', echelle: 1.0, description: 'Conifère élancé gris-vert' },
    ],
    moisFloraison: [5],
    couleurFloraison: '#c94f4f',
    feuillage: {
      printemps: '#4e8c3a',
      ete: '#2e5c26',
      automne: '#2e5c26',
      hiver: '#27513f',
    },
    moisFructification: [9, 10],
    couleurFruit: '#6b4a2f',
    caduc: false,
    rusticite: 'tres_rustique',
    zoneUsdaMin: 3,
  },
  {
    id: 'olivier',
    nom: 'Olivier (Olea europaea)',
    type: 'arbre',
    climats: ['mediterraneen'],
    tailleMatureM: 6,
    stades: [
      { nom: 'graine', couleur: '#4a3a24', echelle: 0.0, description: 'Noyau charnu' },
      { nom: 'jeune_pousse', couleur: '#9aa88a', echelle: 0.15, description: 'Tronc gris lisse' },
      { nom: 'mature', couleur: '#7d7466', echelle: 1.0, description: 'Tronc tortueux, feuillage argenté' },
    ],
    moisFloraison: [5, 6],
    couleurFloraison: '#f5f0dc',
    feuillage: {
      printemps: '#8fa877',
      ete: '#6f8a5a',
      automne: '#6f8a5a',
      hiver: '#5f7a4d',
    },
    moisFructification: [10, 11],
    couleurFruit: '#3d2b1f',
    caduc: false,
    rusticite: 'semi_rustique',
    zoneUsdaMin: 8,
  },
  {
    id: 'bouleau',
    nom: 'Bouleau (Betula pendula)',
    type: 'arbre',
    climats: ['continental', 'montagne', 'oceanique'],
    tailleMatureM: 15,
    stades: [
      { nom: 'graine', couleur: '#8a7448', echelle: 0.0, description: 'Graine ailée minuscule' },
      { nom: 'jeune_pousse', couleur: '#a9c46c', echelle: 0.15, description: 'Tige fine brun clair' },
      { nom: 'mature', couleur: '#e8e4da', echelle: 1.0, description: 'Écorce blanche caractéristique' },
    ],
    moisFloraison: [4],
    couleurFloraison: '#d9c76a',
    feuillage: {
      printemps: '#a9cf6e',
      ete: '#5b8c3e',
      automne: '#e8c33a',
      hiver: null,
    },
    moisFructification: [8, 9],
    couleurFruit: '#9c8a55',
    caduc: true,
    rusticite: 'tres_rustique',
    zoneUsdaMin: 2,
  },
  {
    id: 'pommier',
    nom: 'Pommier (Malus domestica)',
    type: 'arbre',
    climats: ['oceanique', 'continental'],
    tailleMatureM: 6,
    stades: [
      { nom: 'graine', couleur: '#5a3d26', echelle: 0.0, description: 'Pépin brun' },
      { nom: 'jeune_pousse', couleur: '#93b56a', echelle: 0.2, description: 'Port dressé, écorce grise' },
      { nom: 'mature', couleur: '#6f625a', echelle: 1.0, description: 'Cime arrondie, écorce écaillée' },
    ],
    moisFloraison: [4, 5],
    couleurFloraison: '#fbdde4',
    feuillage: {
      printemps: '#8fbc50',
      ete: '#3f7d2c',
      automne: '#c98a2e',
      hiver: null,
    },
    moisFructification: [9, 10],
    couleurFruit: '#c62e2e',
    caduc: true,
    rusticite: 'tres_rustique',
    zoneUsdaMin: 3,
  },

  // ── Arbustes ────────────────────────────────────────────────────────────
  {
    id: 'lavande',
    nom: 'Lavande (Lavandula angustifolia)',
    type: 'arbuste',
    climats: ['mediterraneen', 'oceanique'],
    tailleMatureM: 0.8,
    stades: [
      { nom: 'graine', couleur: '#4a3d2a', echelle: 0.0, description: 'Graine brune minuscule' },
      { nom: 'jeune_pousse', couleur: '#9fb37c', echelle: 0.2, description: 'Touffe grise basse' },
      { nom: 'mature', couleur: '#8a8f6a', echelle: 1.0, description: 'Coussin ligneux argenté' },
    ],
    moisFloraison: [6, 7, 8],
    couleurFloraison: '#8a6fc9',
    feuillage: {
      printemps: '#9db383',
      ete: '#8a9a70',
      automne: '#7c8a63',
      hiver: '#6e7a58',
    },
    moisFructification: [9],
    couleurFruit: '#5c4a3a',
    caduc: false,
    rusticite: 'rustique',
    zoneUsdaMin: 5,
  },
  {
    id: 'rosier',
    nom: 'Rosier (Rosa gallica)',
    type: 'arbuste',
    climats: ['oceanique', 'continental'],
    tailleMatureM: 1.2,
    stades: [
      { nom: 'graine', couleur: '#7a5a3a', echelle: 0.0, description: 'Akène (roseau)' },
      { nom: 'jeune_pousse', couleur: '#a45a4a', echelle: 0.25, description: 'Tiges épineuses rougeâtres' },
      { nom: 'mature', couleur: '#5f6b45', echelle: 1.0, description: 'Buisson dense à tiges lignifiées' },
    ],
    moisFloraison: [5, 6, 7, 8, 9],
    couleurFloraison: '#d94070',
    feuillage: {
      printemps: '#8cb85a',
      ete: '#4a7c30',
      automne: '#b5742a',
      hiver: null,
    },
    moisFructification: [9, 10],
    couleurFruit: '#c94f2e',
    caduc: true,
    rusticite: 'rustique',
    zoneUsdaMin: 4,
  },
  {
    id: 'hortensia',
    nom: 'Hortensia (Hydrangea macrophylla)',
    type: 'arbuste',
    climats: ['oceanique'],
    tailleMatureM: 1.5,
    stades: [
      { nom: 'graine', couleur: '#5f4a34', echelle: 0.0, description: 'Graine poussière' },
      { nom: 'jeune_pousse', couleur: '#8faf6a', echelle: 0.25, description: 'Pousses tendres vert clair' },
      { nom: 'mature', couleur: '#716a50', echelle: 1.0, description: 'Touffe ronde, tiges brunes' },
    ],
    moisFloraison: [6, 7, 8, 9],
    couleurFloraison: '#5a7fc9',
    feuillage: {
      printemps: '#93c45f',
      ete: '#477d33',
      automne: '#c9a04a',
      hiver: null,
    },
    moisFructification: [10],
    couleurFruit: '#8a6f4a',
    caduc: true,
    rusticite: 'rustique',
    zoneUsdaMin: 6,
  },
  {
    id: 'buis',
    nom: 'Buis (Buxus sempervirens)',
    type: 'arbuste',
    climats: ['oceanique', 'continental', 'mediterraneen'],
    tailleMatureM: 2,
    stades: [
      { nom: 'graine', couleur: '#6b5a3a', echelle: 0.0, description: 'Capsule brune' },
      { nom: 'jeune_pousse', couleur: '#7fa860', echelle: 0.2, description: 'Plant dressé vert tendre' },
      { nom: 'mature', couleur: '#5a6b45', echelle: 1.0, description: 'Boule dense vert foncé' },
    ],
    moisFloraison: [4],
    couleurFloraison: '#e8e0b8',
    feuillage: {
      printemps: '#87a85c',
      ete: '#5a7d42',
      automne: '#55753e',
      hiver: '#4d6b3a',
    },
    moisFructification: [9],
    couleurFruit: '#7a6a3f',
    caduc: false,
    rusticite: 'tres_rustique',
    zoneUsdaMin: 5,
  },
  {
    id: 'romarin',
    nom: 'Romarin (Salvia rosmarinus)',
    type: 'arbuste',
    climats: ['mediterraneen', 'oceanique'],
    tailleMatureM: 1,
    stades: [
      { nom: 'graine', couleur: '#5a4a30', echelle: 0.0, description: 'Graine ovale brune' },
      { nom: 'jeune_pousse', couleur: '#93ad70', echelle: 0.25, description: 'Rameaux souples clairs' },
      { nom: 'mature', couleur: '#6b7a52', echelle: 1.0, description: 'Arbuste ligneux à aiguilles' },
    ],
    moisFloraison: [2, 3, 4],
    couleurFloraison: '#8fa8d9',
    feuillage: {
      printemps: '#7f9a60',
      ete: '#6a854f',
      automne: '#63794c',
      hiver: '#5c704a',
    },
    moisFructification: [5],
    couleurFruit: '#6b5a3a',
    caduc: false,
    rusticite: 'semi_rustique',
    zoneUsdaMin: 7,
  },
  {
    id: 'forsythia',
    nom: 'Forsythia (Forsythia x intermedia)',
    type: 'arbuste',
    climats: ['oceanique', 'continental'],
    tailleMatureM: 2.5,
    stades: [
      { nom: 'graine', couleur: '#6a563a', echelle: 0.0, description: 'Capsule ailée' },
      { nom: 'jeune_pousse', couleur: '#96ad66', echelle: 0.22, description: 'Baguettes vertes souples' },
      { nom: 'mature', couleur: '#6f6a4a', echelle: 1.0, description: 'Arqué, rameaux bruns' },
    ],
    moisFloraison: [3, 4],
    couleurFloraison: '#f2c518',
    feuillage: {
      printemps: '#94bc50',
      ete: '#4f7d33',
      automne: '#b5742a',
      hiver: null,
    },
    moisFructification: [],
    couleurFruit: null,
    caduc: true,
    rusticite: 'tres_rustique',
    zoneUsdaMin: 4,
  },

  // ── Fleurs ──────────────────────────────────────────────────────────────
  {
    id: 'tulipe',
    nom: 'Tulipe (Tulipa gesneriana)',
    type: 'fleur',
    climats: ['oceanique', 'continental'],
    tailleMatureM: 0.4,
    stades: [
      { nom: 'graine', couleur: '#7a5a3a', echelle: 0.0, description: 'Bulbe tuniqué' },
      { nom: 'jeune_pousse', couleur: '#96b56a', echelle: 0.3, description: 'Feuille en tire-bouchon' },
      { nom: 'mature', couleur: '#6a8a4a', echelle: 1.0, description: 'Hamme florale dressée' },
    ],
    moisFloraison: [4, 5],
    couleurFloraison: '#e0392e',
    feuillage: {
      printemps: '#8fb55f',
      ete: '#8a9a60',
      automne: null,
      hiver: null,
    },
    moisFructification: [6],
    couleurFruit: '#9c8a4a',
    caduc: true,
    rusticite: 'rustique',
    zoneUsdaMin: 4,
  },
  {
    id: 'coquelicot',
    nom: 'Coquelicot (Papaver rhoeas)',
    type: 'fleur',
    climats: ['oceanique', 'continental', 'mediterraneen'],
    tailleMatureM: 0.5,
    stades: [
      { nom: 'graine', couleur: '#8a6a3a', echelle: 0.0, description: 'Graine minuscule' },
      { nom: 'jeune_pousse', couleur: '#a4bd70', echelle: 0.3, description: 'Rosette duveteuse' },
      { nom: 'mature', couleur: '#7a9a55', echelle: 1.0, description: 'Tige dressée velue' },
    ],
    moisFloraison: [4, 5, 6, 7],
    couleurFloraison: '#d93a2e',
    feuillage: {
      printemps: '#93b560',
      ete: '#7f9a52',
      automne: null,
      hiver: null,
    },
    moisFructification: [6, 7, 8],
    couleurFruit: '#8a7a45',
    caduc: true,
    rusticite: 'tres_rustique',
    zoneUsdaMin: 3,
  },
  {
    id: 'marguerite',
    nom: 'Marguerite (Leucanthemum vulgare)',
    type: 'fleur',
    climats: ['oceanique', 'continental', 'montagne'],
    tailleMatureM: 0.5,
    stades: [
      { nom: 'graine', couleur: '#6b5a34', echelle: 0.0, description: 'Akène allongé' },
      { nom: 'jeune_pousse', couleur: '#9ab56a', echelle: 0.3, description: 'Rosette de feuilles' },
      { nom: 'mature', couleur: '#6f8a50', echelle: 1.0, description: 'Tige nue, feuilles rares' },
    ],
    moisFloraison: [5, 6, 7, 8],
    couleurFloraison: '#f7f5ea',
    feuillage: {
      printemps: '#8ab05a',
      ete: '#6f8f47',
      automne: '#8a8a55',
      hiver: null,
    },
    moisFructification: [7, 8],
    couleurFruit: '#8a7a45',
    caduc: true,
    rusticite: 'tres_rustique',
    zoneUsdaMin: 3,
  },
  {
    id: 'iris',
    nom: 'Iris (Iris germanica)',
    type: 'fleur',
    climats: ['oceanique', 'mediterraneen'],
    tailleMatureM: 0.8,
    stades: [
      { nom: 'graine', couleur: '#7a6a3a', echelle: 0.0, description: 'Rhizome sectionné' },
      { nom: 'jeune_pousse', couleur: '#96ad70', echelle: 0.3, description: 'Éventail de feuilles courtes' },
      { nom: 'mature', couleur: '#7f8a5f', echelle: 1.0, description: 'Éventail dressé de feuilles en sabre' },
    ],
    moisFloraison: [5, 6],
    couleurFloraison: '#6a5acd',
    feuillage: {
      printemps: '#8fa860',
      ete: '#7a9052',
      automne: '#8a8a55',
      hiver: null,
    },
    moisFructification: [8],
    couleurFruit: '#6b5a34',
    caduc: true,
    rusticite: 'rustique',
    zoneUsdaMin: 4,
  },

  // ── Légumes ─────────────────────────────────────────────────────────────
  {
    id: 'tomate',
    nom: 'Tomate (Solanum lycopersicum)',
    type: 'legume',
    climats: ['oceanique', 'continental', 'mediterraneen'],
    tailleMatureM: 1.5,
    stades: [
      { nom: 'graine', couleur: '#8a7a4a', echelle: 0.0, description: 'Graine plate duveteuse' },
      { nom: 'jeune_pousse', couleur: '#9cc45f', echelle: 0.25, description: 'Plant tendre à tige velue' },
      { nom: 'mature', couleur: '#5f8a45', echelle: 1.0, description: 'Tuteur garni, feuillage dense' },
    ],
    moisFloraison: [6, 7],
    couleurFloraison: '#f2d938',
    feuillage: {
      printemps: '#a2c45f',
      ete: '#4f8a38',
      automne: '#8a8a4a',
      hiver: null,
    },
    moisFructification: [7, 8, 9],
    couleurFruit: '#d93a22',
    caduc: true,
    rusticite: 'fragile',
    zoneUsdaMin: 10,
  },
  {
    id: 'carotte',
    nom: 'Carotte (Daucus carota)',
    type: 'legume',
    climats: ['oceanique', 'continental'],
    tailleMatureM: 0.4,
    stades: [
      { nom: 'graine', couleur: '#6a5a34', echelle: 0.0, description: 'Graine petite et ronde' },
      { nom: 'jeune_pousse', couleur: '#93bd60', echelle: 0.3, description: 'Fines feuilles plumeuses' },
      { nom: 'mature', couleur: '#5f8a45', echelle: 1.0, description: 'Touffe aérée, racine charnue' },
    ],
    moisFloraison: [6, 7],
    couleurFloraison: '#f0ead9',
    feuillage: {
      printemps: '#8ab050',
      ete: '#5f8a40',
      automne: '#7f8a50',
      hiver: null,
    },
    moisFructification: [7, 8, 9],
    couleurFruit: '#d97a2e',
    caduc: true,
    rusticite: 'rustique',
    zoneUsdaMin: 3,
  },
  {
    id: 'courgette',
    nom: 'Courgette (Cucurbita pepo)',
    type: 'legume',
    climats: ['oceanique', 'mediterraneen'],
    tailleMatureM: 0.9,
    stades: [
      { nom: 'graine', couleur: '#8a7a4a', echelle: 0.0, description: 'Graine plate ovale' },
      { nom: 'jeune_pousse', couleur: '#9cc45f', echelle: 0.25, description: 'Cotylédons larges' },
      { nom: 'mature', couleur: '#4f7d35', echelle: 1.0, description: 'Touffe large de grandes feuilles' },
    ],
    moisFloraison: [6, 7, 8],
    couleurFloraison: '#f2b52e',
    feuillage: {
      printemps: '#a2c45f',
      ete: '#477d30',
      automne: '#8a8a4a',
      hiver: null,
    },
    moisFructification: [7, 8, 9],
    couleurFruit: '#2e6b2e',
    caduc: true,
    rusticite: 'fragile',
    zoneUsdaMin: 10,
  },
  // ── Éléments de décor naturel (pas des plantes : rendu dédié) ──────────
  {
    id: 'roche',
    nom: 'Roche décorative',
    type: 'roche',
    climats: ['oceanique', 'continental', 'mediterraneen', 'montagne'],
    tailleMatureM: 1,
    stades: [{ nom: 'mature', couleur: '#8b8d90', echelle: 1.0, description: 'Bloc de granit' }],
    feuillage: { printemps: null, ete: null, automne: null, hiver: null },
    caduc: false,
    rustique: true,
    decor: true,
  },
  {
    id: 'eau',
    nom: "Point d'eau (bassin)",
    type: 'eau',
    climats: ['oceanique', 'continental', 'mediterraneen', 'montagne'],
    tailleMatureM: 2,
    stades: [{ nom: 'mature', couleur: '#5fb8a8', echelle: 1.0, description: "Pièce d'eau naturelle" }],
    feuillage: { printemps: null, ete: null, automne: null, hiver: null },
    caduc: false,
    rustique: true,
    decor: true,
  },
];

/** Récupère une plante par son id (null si inconnue). */
export function planteParId(id) {
  return PLANTES.find((p) => p.id === id) || null;
}

/** Plantes compatibles avec un climat donné. */
export function plantesParClimat(climat) {
  return PLANTES.filter((p) => p.climats.includes(climat));
}
