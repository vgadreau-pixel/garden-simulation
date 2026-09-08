import { PLANTES, saisonDuMois } from '../src/data/plants.js';
console.log('plantes:', PLANTES.length);
const p = PLANTES[0];
console.log(JSON.stringify(p.feuillage), p.moisFloraison, p.stades.map((s) => s.echelle));
console.log('saison mois 7:', saisonDuMois(7));
