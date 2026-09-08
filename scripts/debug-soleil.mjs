import { etatSoleil } from '../src/sun.js';
for (const h of [0, 2, 5, 6, 8, 12, 18, 21, 23]) {
  const et = etatSoleil(172, h); // 21 juin
  console.log(`h=${h} nuit=${et.nuit} duree=${et.dureeJourH.toFixed(1)} intensite=${et.intensite.toFixed(2)}`);
}
