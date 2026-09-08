// Centres des saisons en jours (même formule que src/seasons.js)
const m = (mois) => ((mois - 0.5) * 365) / 12;
console.log('centre avril (printemps):', m(4).toFixed(1));
console.log('centre juillet (été):', m(7).toFixed(1));
console.log('centre octobre (automne):', m(10).toFixed(1));
console.log('centre janvier (hiver):', m(1).toFixed(1));
