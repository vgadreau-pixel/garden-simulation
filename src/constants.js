// Constantes partagées du jardin : dimensions, couleurs, densités.
export const PLOT_COUNT = 8; // grille 8x8 de parcelles
export const PLOT_SIZE = 4; // mètres
export const PLOT_PATH = 0.6; // largeur des allées entre parcelles
export const PITCH = PLOT_SIZE + PLOT_PATH; // pas de la grille
export const GRID_EXTENT = PLOT_COUNT * PITCH; // côté du terrain englobant
export const GROUND_MARGIN = 4; // marge d'herbe autour de la grille

// Couleurs
export const COLORS = {
  grassLight: 0x7dab54,
  grassDark: 0x5e8a3e,
  soil: 0x6b4a2f,
  soilDark: 0x57391f,
  border: 0x8a6a45, // bordure bois des parcelles
};
