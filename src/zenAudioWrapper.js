// Wrapper ESM autour de zen-audio.js (fourni en UMD par la tâche audio).
// Permet `import { createZenAudio } from './zenAudio.js'` dans main.js.
import './zenAudio.umd.js';

const { createZenAudio } = typeof window !== 'undefined' && window.createZenAudio
  ? window
  : { createZenAudio: null };

export { createZenAudio };
