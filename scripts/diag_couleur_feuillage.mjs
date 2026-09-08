// Reproduction de couleurFeuillage (src/seasons.js) pour diagnostiquer le bug
// de teinte : automne (289 j) doit donner #d98032, pas #3f7d2c.
const DAYS_PER_YEAR = 365;

const moisVersJours = (m) => ((m - 0.5) * DAYS_PER_YEAR) / 12;

function deltaCycle(a, b) {
  let d = a - b;
  if (d > DAYS_PER_YEAR / 2) d -= DAYS_PER_YEAR;
  if (d < -DAYS_PER_YEAR / 2) d += DAYS_PER_YEAR;
  return d;
}

function smoothstep(t) {
  const x = Math.min(1, Math.max(0, t));
  return x * x * (3 - 2 * x);
}

const pts = [
  { j: moisVersJours(4), c: '#8fc94b', nom: 'printemps' },
  { j: moisVersJours(7), c: '#3f7d2c', nom: 'été' },
  { j: moisVersJours(10), c: '#d98032', nom: 'automne' },
  { j: moisVersJours(1), c: null, nom: 'hiver (caduc)' },
];
pts.forEach(p => console.log(`point ${p.nom}: j=${p.j.toFixed(1)} c=${p.c}`));

// Recherche de segment pour jours = 289 (16 octobre)
for (const jours of [106.5, 197.7, 289, 15.2]) {
  let i0 = pts.length - 1;
  for (let i = 0; i < pts.length; i++) {
    const c1 = deltaCycle(jours, pts[i].j) >= 0;
    const c2 = deltaCycle(pts[(i + 1) % 4].j, jours) > 0;
    if (c1 && c2) { i0 = i; break; }
  }
  console.log(`jours=${jours} -> segment [${pts[i0].nom} -> ${pts[(i0 + 1) % 4].nom}]`);
}
