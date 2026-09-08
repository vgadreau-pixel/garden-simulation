// Vérification logique du module climat (node scripts/check-climat.mjs).
import { etatClimat, meteoDuJour, vigueur, decalageFloraison, facteurCroissance, CLIMATS } from '../src/climate.js';
import { PLANTES } from '../src/data/plants.js';

let fail = 0;
function check(label, cond, detail) {
  console.log(`${cond ? 'OK  ' : 'FAIL'} ${label} ${detail || ''}`);
  if (!cond) fail++;
}

// 1. Continuité : aucun saut brusque des intensités météo sur l'année.
for (const cid of Object.keys(CLIMATS)) {
  let prev = meteoDuJour(cid, 0);
  let maxJump = 0;
  for (let j = 0; j < 3650; j++) {
    const m = meteoDuJour(cid, j / 10);
    for (const k of ['pluie', 'neige', 'brume', 'eclat']) {
      const d = Math.abs(m[k] - prev[k]);
      if (d > maxJump) maxJump = d;
    }
    prev = m;
  }
  check(`continuité météo ${cid}`, maxJump < 0.01, `(max saut/0,1 j = ${maxJump.toFixed(4)})`);
}

// 2. Critères d'acceptation botaniques.
const olivier = PLANTES.find((p) => p.id === 'olivier');
const lavande = PLANTES.find((p) => p.id === 'lavande');
const vigOlivierCont = vigueur(olivier, 'continental', 195);
const vigLavandeMed = vigueur(lavande, 'mediterraneen', 195);
check('olivier dépérit en continental', vigOlivierCont < 0.45, `(vigueur = ${vigOlivierCont.toFixed(2)})`);
check('lavande s’épanouit en méditerranéen', vigLavandeMed === 1, `(vigueur = ${vigLavandeMed.toFixed(2)})`);
check('olivier prospère en méditerranéen', vigueur(olivier, 'mediterraneen', 195) === 1);

// 3. Décalage des floraisons : chaud → avancé, froid → retardé.
const decalMed = decalageFloraison('mediterraneen', 100);
const decalCont = decalageFloraison('continental', 100);
check('floraison avancée en méditerranéen', decalMed < 0, `(${decalMed.toFixed(1)} j)`);
check('floraison retardée en continental', decalCont > 0, `(${decalCont.toFixed(1)} j)`);

// 4. Vitesse de croissance modulée.
check('croissance accélérée en aride (été)', facteurCroissance('aride', 195) > 1.1,
  `(${facteurCroissance('aride', 195).toFixed(2)})`);
check('croissance ralentie en continental (hiver)', facteurCroissance('continental', 15) < 0.7,
  `(${facteurCroissance('continental', 15).toFixed(2)})`);

// 5. Cohérence météo par climat (moyennes annuelles plausibles).
function moyenneAnnuelle(cid, cle) {
  let s = 0;
  for (let j = 0; j < 365; j++) s += meteoDuJour(cid, j)[cle];
  return s / 365;
}
const neigeCont = moyenneAnnuelle('continental', 'neige');
const neigeMed = moyenneAnnuelle('mediterraneen', 'neige');
const eclatAride = moyenneAnnuelle('aride', 'eclat');
const pluieMedEte = meteoDuJour('mediterraneen', 195).pluie;
check('neige en continental > neige en méditerranéen', neigeCont > neigeMed + 0.1,
  `(${neigeCont.toFixed(2)} vs ${neigeMed.toFixed(2)})`);
check('éclat solaire aride élevé', eclatAride > 0.85, `(${eclatAride.toFixed(2)})`);
check('été méditerranéen sec (peu de pluie)', pluieMedEte < 0.15, `(${pluieMedEte.toFixed(2)})`);
const pluieMedHiver = meteoDuJour('mediterraneen', 15).pluie;
check('hiver méditerranéen pluvieux', pluieMedHiver > 0.3, `(${pluieMedHiver.toFixed(2)})`);

console.log(fail === 0 ? '\nTOUS LES TESTS PASSENT' : `\n${fail} ÉCHEC(S)`);
process.exit(fail === 0 ? 0 : 1);
