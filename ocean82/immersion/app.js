/* Ocean 82 — proposition 1 « Immersion ».
   Le défilement de la page pilote la caméra : on se pose à Grand Case, on pousse la porte, on traverse la salle
   jusqu'à la terrasse. À tout moment on peut « attraper » la scène pour regarder autour de soi. */
import { Pano, ease } from '../assets/js/pano.js';
import { initLang, initReservation, getLang } from '../assets/js/site.js';

const R = '../';
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const html = document.documentElement;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x)), lerp = (a, b, t) => a + (b - a) * t;
const lerpA = (a, b, t) => a + ((((b - a) % 360) + 540) % 360 - 180) * t;
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const wide = matchMedia('(min-aspect-ratio: 21/20)');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

initLang();
initReservation($('#resa-form'));

// ------------------------------------------------------------------ la carte (panneau)
const dialog = $('#carte-dialog'), body = $('#carte-body'), nav = $('#carte-nav');
const secs = $$('.carte-sec', body);
const label = s => (getLang() === 'en' ? s.dataset.titleEn : s.dataset.title).replace(/^(Les|The) /, '');
const paintNav = () => { nav.innerHTML = secs.map(s => `<button type="button" data-go="${s.id}">${label(s)}</button>`).join(''); mark(); };
const mark = () => {
  const top = body.getBoundingClientRect().top + 80;
  const cur = [...secs].reverse().find(s => s.getBoundingClientRect().top <= top) || secs[0];
  for (const b of nav.children) {
    const on = b.dataset.go === cur.id; b.setAttribute('aria-current', on);
    if (on && dialog.open) b.scrollIntoView({ block: 'nearest', inline: 'center' });
  }
};
nav.addEventListener('click', e => { const b = e.target.closest('button'); if (b) $('#' + b.dataset.go).scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' }); });
body.addEventListener('scroll', mark, { passive: true });
document.addEventListener('langchange', paintNav);
paintNav();
for (const b of $$('[data-carte]')) b.addEventListener('click', () => {
  dialog.showModal(); $('#carte-' + b.dataset.carte).scrollIntoView(); mark();
});
dialog.addEventListener('click', e => { if (e.target === dialog || e.target.closest('[data-close]')) dialog.close(); });

// ------------------------------------------------------------------ apparition des panneaux (ligne médiane de l'écran)
const stops = $$('.stop');
const io = new IntersectionObserver(es => { for (const e of es) e.target.classList.toggle('is-in', e.isIntersecting); }, { rootMargin: '-45% 0px -45% 0px' });
stops.forEach(s => io.observe(s));

// ------------------------------------------------------------------ défilement doux vers une étape
let scrollAnim = 0;
function glideTo(y, min = 900, max = 3400) {
  cancelAnimationFrame(scrollAnim);
  const y0 = scrollY, d = y - y0;
  if (reduced || Math.abs(d) < 4) { scrollTo(0, y); return; }
  const dur = clamp(Math.abs(d) * 0.9, min, max), t0 = performance.now();
  const step = now => { const k = clamp((now - t0) / dur, 0, 1); scrollTo(0, y0 + d * ease(k)); if (k < 1) scrollAnim = requestAnimationFrame(step); };
  scrollAnim = requestAnimationFrame(step);
}
const stopY = el => {       // position où le panneau d'une étape est installé au centre
  const r = el.getBoundingClientRect(), top = r.top + scrollY;
  if (el.id === 'accueil') return 0;
  return el.classList.contains('stop') && !el.classList.contains('stop-resa') ? top + (r.height - innerHeight) * 0.3 : top - 70;
};
for (const a of $$('a[href^="#"]')) a.addEventListener('click', e => {
  const el = $(a.getAttribute('href')); if (!el) return;
  e.preventDefault(); if (html.classList.contains('roam-on')) roam(false);
  const slow = a.id === 'enter';        // « Entrer » : on prend le temps de la descente
  glideTo(stopY(el), slow ? 3000 : 900, slow ? 4400 : 3400); history.replaceState(null, '', a.getAttribute('href'));
});
for (const ev of ['wheel', 'touchstart', 'keydown']) addEventListener(ev, () => cancelAnimationFrame(scrollAnim), { passive: true });

// ------------------------------------------------------------------ la visite
const rail = $$('.rail a'), navLinks = $$('.nav a');
const heroCopy = $('#hero-copy'), heroHint = $('#hero-hint'), heroLand = $('#hero-land');
const hero = $('#accueil'), foot = $('#contact'), railBox = $('.rail');
const heroP = () => clamp(scrollY / Math.max(1, hero.offsetHeight - innerHeight), 0, 1);
function chrome(scene) {
  const p = heroP();
  heroCopy.style.opacity = 1 - smooth(0.03, 0.17, p); heroCopy.style.transform = `translateY(${-p * 90}px)`;
  heroCopy.style.visibility = p > 0.2 ? 'hidden' : '';
  heroHint.style.opacity = 1 - smooth(0, 0.05, p);
  heroLand.style.opacity = smooth(0.7, 0.84, p) * (1 - smooth(0.95, 1, p));
  for (const a of rail) a.classList.toggle('is-on', a.dataset.stop === scene);
  railBox.classList.toggle('is-off', scrollY + innerHeight > foot.offsetTop + innerHeight * 0.25);
  const mid = scrollY + innerHeight / 2;
  for (const a of navLinks) { const el = $(a.getAttribute('href')), t = el.offsetTop; a.classList.toggle('is-on', mid >= t && mid < t + el.offsetHeight); }
}

const usable = Pano.supported && !reduced;
if (usable) start(); else fallback();

function start() {
  const canvas = $('#scene');
  let pano;
  try {
    pano = new Pano(canvas, {
      scenes: { ciel: R + 'assets/pano/ciel', entree: R + 'assets/pano/entree', salle: R + 'assets/pano/salle', terrasse: R + 'assets/pano/terrasse' },
      grain: 0.035, vignette: 0.3, onRender: placePins,
    });
  } catch (e) { return fallback(); }
  pano.setDrag('x');

  // --- le parcours : [section, position dans la section (0 → 1 pendant qu'elle est épinglée), vue, côté du panneau]
  let KF = [], pts = [];
  function plan() {
    const w = wide.matches, asp = innerWidth / innerHeight, f = w ? 1 : 1.2, n = w ? 0 : 0.1;
    const side = s => (w ? { cx: s === 'L' ? 0.3 * asp : s === 'R' ? -0.3 * asp : 0, cy: 0 } : { cx: 0, cy: s === 'C' ? 0 : 0.26 });
    const v = (scene, yaw, pitch, fov, lens, s = 'C') => ({ scene, yaw, pitch, fov: Math.min(fov * f, 118), n: lens + n, ...side(s) });
    const planet = { scene: 'ciel', yaw: -15, pitch: -90, fov: w ? 252 : 276, n: 2, cx: w ? 0.4 * asp : 0, cy: w ? 0 : -0.36 };   // = l'affiche fixe (src/images.py)
    KF = [
      ['#accueil', 0, planet],
      ['#accueil', 0.2, { ...planet, yaw: -62, fov: planet.fov - 14 }],
      ['#accueil', 0.56, { scene: 'ciel', yaw: -30, pitch: -42, fov: 168, n: 1.75, cx: 0, cy: 0 }],
      ['#accueil', 0.84, v('ciel', -15, -10, 64, 1.1)],
      ['#accueil', 1, v('ciel', -15, -6.5, 46, 1.04)],
      ['#maison', 0, v('entree', -5, 2, 86, 1.15, 'L')],
      ['#maison', 1, v('entree', 12, 2, 82, 1.15, 'L')],
      ['#vivier', 0.25, v('entree', 38, 3, 66, 1.06, 'R')],
      ['#vivier', 1, v('entree', 30, 3, 70, 1.06, 'R')],
      ['#cave', 0.25, v('entree', -48, 7, 66, 1.06, 'L')],
      ['#cave', 0.8, v('entree', -56, 5, 70, 1.06, 'L')],
      ['#cave', 1.25, v('entree', -160, -2, 74, 1.1)],
      ['#carte', 0, v('salle', -112, 0, 84, 1.12, 'R')],
      ['#carte', 1, v('salle', -30, -4, 84, 1.12, 'R')],
      ['#bar', 0.2, v('salle', 138, -2, 74, 1.06, 'L')],
      ['#bar', 0.8, v('salle', 128, -2, 76, 1.06, 'L')],
      ['#bar', 1.3, v('salle', -22, -3, 66, 1.06)],
      ['#terrasse', 0, v('terrasse', 8, -6, 86, 1.12)],
      ['#terrasse', 1, v('terrasse', -66, -8, 84, 1.12)],
      ['#reserver', 0.5, v('terrasse', -80, -4, 72, 1.06, 'R')],
      ['#contact', 0.6, v('terrasse', -102, 4, 62, 1.02)],
    ];
    pts = KF.map(([sel, at]) => {
      const el = $(sel), top = el.getBoundingClientRect().top + scrollY, h = el.offsetHeight;
      return el.querySelector('.pinbox, .hero-pin') ? top + at * (h - innerHeight) : top + at * h - innerHeight * 0.5;
    });
    for (let i = 1; i < pts.length; i++) pts[i] = Math.max(pts[i], pts[i - 1] + 1);
  }
  const mixView = (a, b, t) => ({ scene: a.scene, yaw: lerpA(a.yaw, b.yaw, t), pitch: lerp(a.pitch, b.pitch, t), fov: lerp(a.fov, b.fov, t), n: lerp(a.n, b.n, t) });

  let roaming = false, sceneNow = 'ciel';
  function apply(s) {
    let i = 0;
    while (i < pts.length - 2 && s >= pts[i + 1]) i++;
    const A = KF[i][2], B = KF[i + 1][2], t = clamp((s - pts[i]) / (pts[i + 1] - pts[i]), 0, 1), k = ease(t);
    pano.center = [lerp(A.cx || 0, B.cx || 0, k), lerp(A.cy || 0, B.cy || 0, k)];
    if (A.scene === B.scene) { pano.frame(mixView(A, B, k)); sceneNow = A.scene; }
    else {                                  // on change de pièce : on avance, la suivante s'ouvre depuis le centre
      const m = clamp((k - 0.12) / 0.7, 0, 1);
      pano.frame({ ...A, fov: A.fov * (1 - 0.38 * k) }, { ...B, fov: B.fov * (1 + 0.3 * (1 - k)) }, m, 0.3 * Math.sin(Math.PI * k));
      sceneNow = m > 0.5 ? B.scene : A.scene;
    }
    pano.autoRotate = s < 4 ? 2.2 : 0;
    // précharge la pièce suivante un peu avant d'y arriver
    const nxt = KF[Math.min(i + 2, KF.length - 1)][2].scene; if (nxt !== A.scene && t > 0.3) pano.need(nxt);
    chrome(sceneNow);
  }

  // le défilement est lissé (les molettes avancent par à-coups) : la caméra rattrape la position réelle
  let cur = scrollY, raf = 0, last = 0;
  const loop = now => {
    const target = scrollY, dt = Math.min(now - last, 64); last = now;
    cur += (target - cur) * (1 - Math.exp(-dt / 105));
    if (Math.abs(target - cur) < 0.4) cur = target;
    if (!roaming) { apply(cur); pano.relax(0.05); }
    raf = cur !== target ? requestAnimationFrame(loop) : 0;
  };
  const kick = () => { if (!raf) { last = performance.now(); raf = requestAnimationFrame(loop); } };
  addEventListener('scroll', kick, { passive: true });
  let rz = 0;
  addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => { plan(); if (!roaming) apply(cur = scrollY); }, 120); });
  wide.addEventListener('change', () => { plan(); if (!roaming) apply(cur = scrollY); });
  plan(); apply(cur);

  // la toile remplace l'affiche dès que la vue nette du ciel est chargée
  pano.ready.then(() => pano.need(sceneNow)).catch(() => {}).then(() => requestAnimationFrame(() => html.classList.add('gl-on')));
  // images suivantes pendant les temps morts
  const idle = window.requestIdleCallback || (fn => setTimeout(fn, 1500));
  idle(() => { if (sceneNow === 'ciel') pano.need('entree'); });

  // --- repères
  const pins = $$('.pin').map(el => ({ el, scene: el.dataset.scene, yaw: +el.dataset.yaw, pitch: +el.dataset.pitch }));
  function placePins(p) {
    const main = p.b && p.mix > 0.5 ? p.b : p.a, settled = !p.b || p.mix < 0.1 || p.mix > 0.96;
    for (const pin of pins) {
      let on = settled && pin.scene === main.scene && main.n < 1.3 && !(pin.scene === 'ciel' && !roaming && heroP() > 0.985);
      if (on) { const s = p.project(pin.yaw, pin.pitch, main); on = s.visible; if (on) pin.el.style.transform = `translate(${s.x.toFixed(1)}px,${s.y.toFixed(1)}px)`; }
      pin.el.classList.toggle('is-on', on);
    }
  }

  // --- visite libre
  const HOME = {
    ciel: { scene: 'ciel', yaw: -15, pitch: -12, fov: 78, n: 1.12 }, entree: { scene: 'entree', yaw: -5, pitch: 2, fov: 88, n: 1.15 },
    salle: { scene: 'salle', yaw: -25, pitch: -4, fov: 88, n: 1.14 }, terrasse: { scene: 'terrasse', yaw: -66, pitch: -8, fov: 88, n: 1.14 },
  };
  const fit = v => (wide.matches ? v : { ...v, fov: Math.min(v.fov * 1.2, 112), n: v.n + 0.1 });
  const chips = $$('.roam-scenes button');
  const chip = scene => { for (const c of chips) c.setAttribute('aria-pressed', c.dataset.scene === scene); sceneNow = scene; };
  function roam(on) {
    roaming = on; html.classList.toggle('roam-on', on); $('#roam').hidden = !on;
    pano.stop(); pano.autoRotate = 0;
    if (on) {
      pano.setDrag('xy'); const c0 = [...pano.center];
      pano.look(fit(HOME[sceneNow]), 1100); chip(sceneNow); canvas.tabIndex = 0; canvas.focus({ preventScroll: true });
      pano.tween(700, k => { pano.center = [c0[0] * (1 - k), c0[1] * (1 - k)]; pano.dirty = true; });
    } else { pano.setDrag('x'); pano.uy = pano.up = pano.vy = pano.vp = 0; canvas.tabIndex = -1; apply(cur = scrollY); }
  }
  $('#roam-open').addEventListener('click', () => roam(true));
  $('#roam-close').addEventListener('click', () => roam(false));
  addEventListener('keydown', e => { if (e.key === 'Escape' && roaming && !dialog.open) roam(false); });
  for (const c of chips) c.addEventListener('click', () => { chip(c.dataset.scene); pano.walk(fit(HOME[c.dataset.scene])); });
  for (const pin of pins) if (pin.el.dataset.to) pin.el.addEventListener('click', () => {
    if (!roaming) return glideTo(stopY($('#maison')), 2600, 3600);
    const [yaw, pitch] = pin.el.dataset.in.split(',').map(Number), to = pin.el.dataset.to;
    chip(to); pano.walk(fit({ ...HOME[to], yaw, pitch }), { towards: { yaw: pin.yaw, pitch: pin.pitch * 0.5 } });
  });
  window.__o82 = { pano, roam, apply: y => apply(cur = y) };      // accès pour les tests et les captures
}

// ------------------------------------------------------------------ sans WebGL (ou mouvement réduit) : vues fixes en fondu
function fallback() {
  html.classList.add('no-gl');
  const data = JSON.parse($('#stills-data').textContent), box = $('#stills'), made = {};
  const which = { maison: 'entree', vivier: 'vivier', cave: 'cave', carte: 'salle', bar: 'bar', terrasse: 'terrasse', reserver: 'mer', contact: 'mer' };
  const show = key => {
    if (key && !made[key]) { const i = made[key] = new Image(); i.alt = ''; i.decoding = 'async'; i.src = data[key]; box.append(i); }
    for (const k in made) made[k].classList.toggle('is-on', k === key);
  };
  const order = ['accueil', ...Object.keys(which)].map(id => $('#' + id));
  const pick = () => {
    const mid = scrollY + innerHeight * 0.5; let id = 'accueil';
    for (const el of order) if (el.getBoundingClientRect().top + scrollY <= mid) id = el.id;
    const key = id === 'accueil' ? (heroP() > 0.45 ? 'ciel' : null) : which[id];
    show(key); chrome({ ciel: 'ciel', entree: 'entree', vivier: 'entree', cave: 'entree', salle: 'salle', bar: 'salle', terrasse: 'terrasse', mer: 'terrasse' }[key] || 'ciel');
  };
  addEventListener('scroll', pick, { passive: true }); pick();
  $('#roam-open').hidden = true;
}
