// Test de la logique multi-pas de l'horloge (simulation du tick en sous-pas)
// Simule une frame très lente (600 ms) et vérifie le rattrapage.
const MAX_STEP_MS = 250;
const MAX_STEPS = 4;

function repartir(deltaMs) {
  // Même logique que simulationClock.tick (copie pour test hors three)
  const pas = [];
  let restant = Math.min(deltaMs, MAX_STEP_MS * MAX_STEPS);
  while (restant > 0) {
    const s = Math.min(restant, MAX_STEP_MS);
    pas.push(s);
    restant -= s;
  }
  return pas;
}

// Cas 1 : frame normale 16 ms → 1 pas
console.log('16 ms  →', repartir(16));
// Cas 2 : onglet throttled 400 ms → 2 pas de 250/150
console.log('400 ms →', repartir(400));
// Cas 3 : frame très lente headless 600 ms → 3 pas
console.log('600 ms →', repartir(600));
// Cas 4 : freeze énorme 3 s → plafonné à 4 pas (1 s), le surplus est perdu volontairement
console.log('3000 ms →', repartir(3000), '(plafonné à 1000 ms)');

// Total temps simulé par frame selon fps (à 30 j/s) :
for (const fps of [60, 30, 10, 4, 3]) {
  const delta = 1000 / fps;
  const total = Math.min(delta, 1000);
  console.log(`fps ${fps} → ${total} ms simulés/frame → ${(total / 1000 * 30).toFixed(1)} j/frame → ${(total / 1000 * 30 * fps).toFixed(0)} j/s`);
}
console.log('année complète en 12,6 s requiert :', (365 / 12.6).toFixed(1), 'j/s');
