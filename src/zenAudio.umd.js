/**
 * zen-audio.js — Nappe ambiante méditative 100 % procédurale (Web Audio).
 *
 * Aucun fichier audio externe : tout est synthétisé (drones, nappes,
 * vent, carillons pentatoniques). Boucle infinie sans coupure.
 *
 * Démarrage : le contexte audio n'est créé qu'au premier appel de play()
 * déclenché par un geste utilisateur (clic) — conforme aux politiques
 * d'autoplay. Aucune erreur n'est levée si le navigateur bloque l'audio.
 *
 * API :
 *   const audio = createZenAudio(document.getElementById('audio-ui-host'));
 *   audio.play();                  // démarre (doit venir d'un clic)
 *   audio.pause();                 // fondu de sortie puis suspension
 *   audio.toggle();
 *   audio.setVolume(0..1);         // volume master
 *   audio.setSeason('spring'|'summer'|'autumn'|'winter');  // variation d'intensité
 *   audio.setWeather('clear'|'rain'|'snow'|'fog'|'heat');  // variation météo
 *   audio.setMood({brightness, wind, bellRate});  // réglage fin (0..1)
 *   audio.isPlaying();
 *
 * Toutes les transitions sont fondues (gain ramps) : aucune coupure brutale.
 */
(function (global) {
  'use strict';

  // —— Presets saison/météo : {brightness (cutoff filtre), wind, bellRate (bells/min), droneLevel}
  var SEASON_PRESETS = {
    spring: { brightness: 0.75, wind: 0.30, bellRate: 4.5, droneLevel: 0.85 },
    summer: { brightness: 0.90, wind: 0.20, bellRate: 3.0, droneLevel: 1.00 },
    autumn: { brightness: 0.55, wind: 0.45, bellRate: 2.5, droneLevel: 0.80 },
    winter: { brightness: 0.40, wind: 0.60, bellRate: 1.5, droneLevel: 0.65 }
  };
  var WEATHER_PRESETS = {
    clear: { brightness: 1.00, wind: 1.00, bellRate: 1.00, droneLevel: 1.00 },
    rain:  { brightness: 0.70, wind: 1.30, bellRate: 0.60, droneLevel: 1.10 },
    snow:  { brightness: 0.55, wind: 0.70, bellRate: 0.50, droneLevel: 0.90 },
    fog:   { brightness: 0.60, wind: 0.60, bellRate: 0.70, droneLevel: 0.95 },
    heat:  { brightness: 0.85, wind: 0.50, bellRate: 0.80, droneLevel: 0.95 }
  };

  // Gamme pentatonique (la mineur pentatonique, apaisante)
  var SCALE = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33];

  var FADE_SECONDS = 2.5; // crossfade entrée/sortie

  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }

  function createZenAudio(hostElement, options) {
    options = options || {};
    var ctx = null;              // créé paresseusement (politique autoplay)
    var nodes = null;            // graphe audio
    var bellTimer = null;
    var chordTimer = null;
    var playing = false;
    var volume = (typeof options.volume === 'number') ? clamp(options.volume, 0, 1) : 0.5;
    var mood = { brightness: 0.7, wind: 0.35, bellRate: 3.0, droneLevel: 0.85 };
    var season = 'spring';
    var weather = 'clear';
    var failed = false;

    // ————————————————— UI —————————————————
    var ui = null;
    if (hostElement) ui = buildUI(hostElement);

    function buildUI(host) {
      var root = document.createElement('div');
      root.className = 'zen-audio-ui';
      root.setAttribute('style', [
        'position:absolute', 'left:16px', 'bottom:16px', 'z-index:1000',
        'display:flex', 'align-items:center', 'gap:10px',
        'padding:10px 14px', 'border-radius:24px',
        'background:rgba(30,32,28,0.55)', 'backdrop-filter:blur(8px)',
        'font-family:system-ui,sans-serif', 'color:#e8e6df',
        'user-select:none', 'box-shadow:0 2px 12px rgba(0,0,0,0.25)'
      ].join(';'));

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Lire ou mettre en pause la musique');
      btn.setAttribute('style', [
        'width:38px', 'height:38px', 'border-radius:50%', 'border:none',
        'cursor:pointer', 'font-size:16px', 'line-height:1',
        'background:rgba(255,255,255,0.12)', 'color:#e8e6df',
        'transition:background .2s'
      ].join(';'));
      btn.textContent = '▶';

      var vol = document.createElement('input');
      vol.type = 'range';
      vol.min = '0'; vol.max = '100'; vol.value = String(Math.round(volume * 100));
      vol.setAttribute('aria-label', 'Volume de la musique');
      vol.setAttribute('style', 'width:110px;accent-color:#a8c69f;cursor:pointer;');

      root.appendChild(btn);
      root.appendChild(vol);
      host.appendChild(root);

      btn.addEventListener('click', function () { api.toggle(); });
      vol.addEventListener('input', function () {
        api.setVolume(parseInt(vol.value, 10) / 100);
      });
      return { root: root, btn: btn, vol: vol };
    }

    function updateUI() {
      if (!ui) return;
      ui.btn.textContent = playing ? '⏸' : '▶';
    }

    // ————————————————— Construction du graphe —————————————————
    function buildGraph() {
      var master = ctx.createGain();
      master.gain.value = 0;             // démarre muet, fondu au play()
      master.connect(ctx.destination);

      // Bus de réverbération léger (convolution générée procéduralement)
      var reverb = ctx.createConvolver();
      reverb.buffer = makeImpulseResponse(3.2, 2.5);
      var reverbGain = ctx.createGain();
      reverbGain.gain.value = 0.35;
      reverb.connect(reverbGain);
      reverbGain.connect(master);

      var bus = ctx.createGain();        // bus commun des sources
      bus.connect(master);
      bus.connect(reverb);

      nodes = {
        master: master,
        bus: bus,
        filters: {},
        layers: {}
      };

      buildDroneLayer();
      buildWindLayer();
      scheduleNextChord(0);
      scheduleNextBell();
      applyMood(0); // applique les réglages initiaux sans transition
    }

    function makeImpulseResponse(duration, decay) {
      var rate = ctx.sampleRate;
      var len = Math.floor(rate * duration);
      var buf = ctx.createBuffer(2, len, rate);
      for (var ch = 0; ch < 2; ch++) {
        var data = buf.getChannelData(ch);
        for (var i = 0; i < len; i++) {
          data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay);
        }
      }
      return buf;
    }

    // Nappe drone : 3 oscillateurs détunés + filtre passe-bas modulé par LFO lent
    function buildDroneLayer() {
      var filter = ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.value = 700;
      filter.Q.value = 0.7;

      var droneGain = ctx.createGain();
      droneGain.gain.value = 0.16;
      filter.connect(droneGain);
      droneGain.connect(nodes.bus);

      // LFO très lent sur la cutoff → respiration de la nappe
      var lfo = ctx.createOscillator();
      lfo.frequency.value = 0.05; // période 20 s
      var lfoGain = ctx.createGain();
      lfoGain.gain.value = 220;
      lfo.connect(lfoGain);
      lfoGain.connect(filter.frequency);
      lfo.start();

      var oscs = [];
      // Accord de base : la1 + mi2 + la2, léger détune pour richesse
      var freqs = [110.0, 164.81, 220.0];
      freqs.forEach(function (f, i) {
        var o = ctx.createOscillator();
        o.type = i === 1 ? 'triangle' : 'sine';
        o.frequency.value = f;
        o.detune.value = (i - 1) * 6;
        var g = ctx.createGain();
        g.gain.value = i === 0 ? 0.6 : 0.35;
        o.connect(g);
        g.connect(filter);
        o.start();
        oscs.push(o);
      });

      nodes.filters.drone = filter;
      nodes.layers.drone = { gain: droneGain, oscs: oscs, lfo: lfo };
    }

    // Vent : bruit filtré en bande passante modulée lentement
    function buildWindLayer() {
      var noise = makeNoiseSource();
      var filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.value = 400;
      filter.Q.value = 0.5;

      var windGain = ctx.createGain();
      windGain.gain.value = 0.05;
      noise.connect(filter);
      filter.connect(windGain);
      windGain.connect(nodes.bus);

      var lfo = ctx.createOscillator();
      lfo.frequency.value = 0.07;
      var lfoGain = ctx.createGain();
      lfoGain.gain.value = 180;
      lfo.connect(lfoGain);
      lfoGain.connect(filter.frequency);
      lfo.start();

      nodes.filters.wind = filter;
      nodes.layers.wind = { gain: windGain, source: noise, lfo: lfo };
    }

    function makeNoiseSource() {
      var len = ctx.sampleRate * 4; // buffer bouclé sans coupure audible
      var buf = ctx.createBuffer(1, len, ctx.sampleRate);
      var data = buf.getChannelData(0);
      var last = 0;
      for (var i = 0; i < len; i++) { // bruit rose approx. (léger lissage)
        var white = Math.random() * 2 - 1;
        last = 0.98 * last + 0.02 * white;
        data[i] = last * 3.5;
      }
      var src = ctx.createBufferSource();
      src.buffer = buf;
      src.loop = true;
      src.start();
      return src;
    }

    // Nappes harmoniques : accord pentatonique changeant toutes les ~25 s
    function scheduleNextChord(delay) {
      chordTimer = setTimeout(function () {
        if (!playing || !ctx) { scheduleNextChord(5000); return; }
        try { playChord(); } catch (e) { /* audio indisponible : on continue */ }
        scheduleNextChord(18000 + Math.random() * 14000);
      }, delay);
    }

    function playChord() {
      var root = SCALE[Math.floor(Math.random() * 4)];
      var idx = SCALE.indexOf(root);
      var voices = [root, SCALE[(idx + 2) % SCALE.length], SCALE[(idx + 4) % SCALE.length]];
      var now = ctx.currentTime;
      voices.forEach(function (f, i) {
        var o = ctx.createOscillator();
        o.type = 'sine';
        o.frequency.value = f * 0.5; // une octave sous les carillons
        o.detune.value = (Math.random() - 0.5) * 8;
        var g = ctx.createGain();
        var peak = 0.05 / (i + 1);
        g.gain.setValueAtTime(0.0001, now);
        g.gain.linearRampToValueAtTime(peak, now + 6 + i); // montée très lente
        g.gain.linearRampToValueAtTime(0.0001, now + 22 + i);
        o.connect(g);
        g.connect(nodes.bus);
        o.start(now);
        o.stop(now + 24 + i);
      });
    }

    // Carillons : notes pentatoniques éparses, longue traîne
    function scheduleNextBell() {
      var delayMs = (60 / mood.bellRate) * 1000 * (0.6 + Math.random() * 0.9);
      bellTimer = setTimeout(function () {
        if (playing && ctx) {
          try { playBell(); } catch (e) { /* ignore */ }
        }
        scheduleNextBell();
      }, Math.max(2000, delayMs));
    }

    function playBell() {
      var f = SCALE[Math.floor(Math.random() * SCALE.length)] * 2;
      var now = ctx.currentTime;
      var o = ctx.createOscillator();
      o.type = 'sine';
      o.frequency.value = f;
      var partial = ctx.createOscillator(); // harmonique légère, timbre cloche
      partial.type = 'sine';
      partial.frequency.value = f * 2.76;
      var pg = ctx.createGain();
      pg.gain.value = 0.12;

      var g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, now);
      g.gain.exponentialRampToValueAtTime(0.09, now + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, now + 6);

      o.connect(g); partial.connect(pg); pg.connect(g);
      g.connect(nodes.bus);
      o.start(now); partial.start(now);
      o.stop(now + 6.5); partial.stop(now + 6.5);
    }

    // ————————————————— Mood / saison / météo —————————————————
    function applyMood(fadeSeconds) {
      if (!ctx || !nodes) return;
      var t = ctx.currentTime;
      var fs = Math.max(0.1, fadeSeconds);
      // combine saison et météo multiplicativement
      var s = SEASON_PRESETS[season] || SEASON_PRESETS.spring;
      var w = WEATHER_PRESETS[weather] || WEATHER_PRESETS.clear;
      var brightness = clamp(s.brightness * w.brightness, 0.1, 1.5);
      var wind = clamp(s.wind * w.wind, 0.05, 1.5);
      var droneLevel = clamp(s.droneLevel * w.droneLevel, 0.2, 1.5);
      mood.bellRate = clamp(s.bellRate * w.bellRate, 0.3, 10);

      nodes.filters.drone.frequency.cancelScheduledValues(t);
      nodes.filters.drone.frequency.linearRampToValueAtTime(300 + brightness * 900, t + fs);
      nodes.layers.drone.gain.gain.cancelScheduledValues(t);
      nodes.layers.drone.gain.gain.linearRampToValueAtTime(0.16 * droneLevel, t + fs);

      nodes.layers.wind.gain.gain.cancelScheduledValues(t);
      nodes.layers.wind.gain.gain.linearRampToValueAtTime(0.05 * wind, t + fs);
    }

    // ————————————————— Transport —————————————————
    function ensureContext() {
      if (ctx || failed) return;
      var AC = global.AudioContext || global.webkitAudioContext;
      if (!AC) { failed = true; return; } // pas de support : bouton inerte, zéro erreur
      try {
        ctx = new AC();
        buildGraph();
      } catch (e) {
        failed = true;
        ctx = null;
      }
    }

    function fadeMasterTo(value, then) {
      if (!ctx) return;
      var t = ctx.currentTime;
      var g = nodes.master.gain;
      g.cancelScheduledValues(t);
      g.setValueAtTime(Math.max(0.0001, g.value), t);
      g.linearRampToValueAtTime(value, t + FADE_SECONDS);
      if (then) setTimeout(then, FADE_SECONDS * 1000 + 100);
    }

    function play() {
      ensureContext();
      if (!ctx || playing) return;
      var start = function () {
        playing = true;
        updateUI();
        fadeMasterTo(volume);
      };
      if (ctx.state === 'suspended') {
        Promise.resolve(ctx.resume()).then(start).catch(function () {
          // Bloqué par le navigateur : aucun crash, l'utilisateur peut recliquer
        });
      } else {
        start();
      }
    }

    function pause() {
      if (!ctx || !playing) return;
      playing = false;
      updateUI();
      fadeMasterTo(0.0001, function () {
        if (!playing && ctx && ctx.state === 'running') {
          ctx.suspend().catch(function () {});
        }
      });
    }

    // ————————————————— API publique —————————————————
    var api = {
      play: play,
      pause: pause,
      toggle: function () { if (playing) pause(); else play(); },
      isPlaying: function () { return playing; },

      setVolume: function (v) {
        volume = clamp(v, 0, 1);
        if (ui) ui.vol.value = String(Math.round(volume * 100));
        if (ctx && playing) {
          var t = ctx.currentTime;
          var g = nodes.master.gain;
          g.cancelScheduledValues(t);
          g.linearRampToValueAtTime(volume, t + 0.15);
        }
      },
      getVolume: function () { return volume; },

      setSeason: function (name) {
        if (SEASON_PRESETS[name]) { season = name; applyMood(4); }
      },
      setWeather: function (name) {
        if (WEATHER_PRESETS[name]) { weather = name; applyMood(6); }
      },
      setMood: function (m) {
        if (!m) return;
        if (typeof m.brightness === 'number') mood.brightness = clamp(m.brightness, 0.1, 1.5);
        if (typeof m.wind === 'number') mood.wind = clamp(m.wind, 0.05, 1.5);
        if (typeof m.bellRate === 'number') mood.bellRate = clamp(m.bellRate, 0.3, 10);
        if (ctx) applyMood(3);
      },

      // Diagnostic interne (tests / intégration) — ne modifie rien
      _debug: function () {
        return {
          hasContext: !!ctx,
          failed: failed,
          state: ctx ? ctx.state : null,
          playing: playing,
          volume: volume
        };
      },

      dispose: function () {
        clearTimeout(bellTimer);
        clearTimeout(chordTimer);
        if (ctx) { try { ctx.close(); } catch (e) {} ctx = null; }
        if (ui && ui.root.parentNode) ui.root.parentNode.removeChild(ui.root);
      }
    };

    return api;
  }

  global.createZenAudio = createZenAudio;
  if (typeof module !== 'undefined' && module.exports) module.exports = { createZenAudio: createZenAudio };
})(typeof window !== 'undefined' ? window : this);
