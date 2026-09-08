import { SimulationClock, jourVersDate } from '../src/simulationClock.js';
import { PLANTES } from '../src/data/plants.js';
import { masseFoliaire, intensiteFloraison, intensiteFruits, couleurFeuillage, nomStade } from '../src/seasons.js';
import { etatSoleil } from '../src/sun.js';

let erreurs = 0;
const ko = (msg) => { console.error('FAIL:', msg); erreurs++; };

// 1. Continuité : pas de saut > epsilon entre pas de 1 jour sur toute l'année
for (const plante of PLANTES) {
  let prevC = couleurFeuillage(plante, 0, null);
  let prevM = masseFoliaire(plante, 0);
  for (let j = 0.25; j <= 365; j += 0.25) {
    const c = couleurFeuillage(plante, j, null);
    const m = masseFoliaire(plante, j);
    const dc = Math.max(Math.abs(c.r - prevC.r), Math.abs(c.g - prevC.g), Math.abs(c.b - prevC.b));
    const dm = Math.abs(m - prevM);
    if (dc > 0.06) ko(`${plante.id} saut couleur ${dc.toFixed(3)} à j=${j.toFixed(2)}`);
    if (dm > 0.02) ko(`${plante.id} saut masse ${dm.toFixed(3)} à j=${j.toFixed(2)}`);
    prevC = c; prevM = m;
  }
  // Fleurs/fruits dans [0,1]
  for (let j = 0; j < 365; j += 5) {
    const f = intensiteFloraison(plante, j), fr = intensiteFruits(plante, j);
    if (!(f >= 0 && f <= 1) || !(fr >= 0 && fr <= 1)) ko(`${plante.id} intensité hors bornes j=${j}`);
  }
}

// 2. Horloge : vitesses + wrap d'année
const clock = new SimulationClock(new Date(Date.UTC(2026, 11, 30, 0, 0)));
clock.setSpeed('jour');
clock.tick(1000); // cap multi-pas : 1 s max par frame → +1 jour (364)
clock.tick(1000); // +1 jour → wrap d'année 365 → 0
if (!(clock.jours < 3)) ko(`wrap année: jours=${clock.jours}`);
if (clock.paused) ko('pause état');
clock.setSpeed('pause');
clock.tick(1000);
const j0 = clock.jours;
clock.tick(1000);
if (clock.jours !== j0) ko('pause ne gèle pas');
clock.scrubTo(200.75);
if (Math.abs(clock.jours - 200.75) > 1e-9) ko('scrub imprécis');
const et = clock.etat;
if (!/juillet/.test(et.label)) ko(`label inattendu: ${et.label}`);

// 3. Soleil : durée du jour plus longue en juin qu'en décembre, intensité > 0 le jour
const ete = etatSoleil(172, 12); // 21 juin midi
const hiver = etatSoleil(355, 12); // 21 déc midi
if (!(ete.dureeJourH > hiver.dureeJourH + 4)) ko(`durée jour: été=${ete.dureeJourH.toFixed(1)} hiver=${hiver.dureeJourH.toFixed(1)}`);
if (!(ete.intensite > 1)) ko(`intensité été midi=${ete.intensite}`);
if (!hiver.nuit === false && hiver.intensite < 0.1) ko('hiver midi sombre');
const nuit = etatSoleil(172, 2);
if (!nuit.nuit) ko('2h du matin devrait être nuit');

// 4. Stades sur l'année (cerisier attendu : floraison ~mars-avril)
const cerisier = PLANTES.find((p) => p.id === 'cerisier');
const stFlor = nomStade(cerisier, 100); // ~10 avril
if (!/floraison/.test(stFlor)) ko(`cerisier j100 attendu floraison, got ${stFlor}`);

console.log(erreurs === 0 ? 'TOUS LES TESTS PASSENT' : `${erreurs} échec(s)`);
process.exit(erreurs === 0 ? 0 : 1);
