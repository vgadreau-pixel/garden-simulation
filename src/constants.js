// Constantes partagées du jardin : dimensions, couleurs, densités.
// Le jardin est une pelouse libre (pas de grille de parcelles) : GRID_EXTENT
// définit simplement l'étendue du terrain jouable.
export const GROUND_HALF = 24; // demi-étendue de la pelouse (mètres)
export const GRID_EXTENT = GROUND_HALF * 2; // compat ascendante (terrain, fps)
export const GROUND_MARGIN = 0; // le sol couvre déjà toute l'étendue

// Couleurs
export const COLORS = {
  grassLight: 0x7dab54,
  grassDark: 0x5e8a3e,
  soil: 0x6b4a2f,
  soilDark: 0x57391f,
  border: 0x8a6a45, // bordure bois (pas japonais, bordures de massifs)
};
