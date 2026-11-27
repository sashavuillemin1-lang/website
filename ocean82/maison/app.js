/* Ocean 82 — proposition 2 « La Maison ».
   Page presque entièrement statique : la carte s'ouvre avec <details>, le défilement doux est en CSS.
   Le script ne sert qu'à la langue, aux apparitions, à la réservation et à la visite 360° (chargée à la demande). */
import { initLang, reveal, initReservation } from '../assets/js/site.js';

const R = '../';
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
window.o82 = true;

initLang();
reveal();
initReservation($('#resa-form'));

// un lien « La sélection des digestifs » ouvre la rubrique correspondante de la carte
for (const a of $$('a[data-open]')) a.addEventListener('click', () => { const d = $('#' + a.dataset.open); if (d) d.open = true; });

// rubrique en cours dans le sommaire
const links = $$('.nav a'), spy = new IntersectionObserver(es => {
  for (const e of es) if (e.isIntersecting) for (const a of links) a.classList.toggle('is-on', a.getAttribute('href') === '#' + e.target.id);
}, { rootMargin: '-45% 0px -50% 0px' });
links.forEach(a => { const el = $(a.getAttribute('href')); if (el) spy.observe(el); });

// ------------------------------------------------------------------ la visite 360°
const frame = $('.tour-frame'), canvas = $('#tour-canvas'), startBox = $('#tour-start'), enterBtn = $('#tour-enter');
const pinsBox = $('#tour-pins'), hint = $('#tour-hint'), full = $('#tour-full'), tabs = $$('#tour-tabs button');
const narrow = matchMedia('(max-width: 899px)');
// vues d'arrivée dans chaque lieu ; la terrasse reprend exactement le cadrage de l'affiche fixe (src/images.py)
const HOME = {
  ciel: { scene: 'ciel', yaw: -15, pitch: -10, fov: 70, n: 1.1 },
  entree: { scene: 'entree', yaw: -5, pitch: 2, fov: 88, n: 1.15 },
  salle: { scene: 'salle', yaw: -25, pitch: -4, fov: 86, n: 1.12 },
  terrasse: { scene: 'terrasse', yaw: -70, pitch: -8, fov: 78, n: 1 },
};
const POSTER_TALL = { scene: 'terrasse', yaw: -62, pitch: -8, fov: 92, n: 1.2 };
const fit = v => (narrow.matches ? { ...v, fov: Math.min(v.fov * 1.18, 112), n: Math.min(v.n + 0.1, 1.28) } : v);

let mod = null, pano = null, entering = null, grabbed = false, seen = false;
const load = () => mod || (mod = import(R + 'assets/js/pano.js'));
const press = scene => { for (const t of tabs) t.setAttribute('aria-pressed', String(t.dataset.scene === scene)); };

// le module n'est demandé qu'à l'approche de la section
new IntersectionObserver((es, io) => {
  if (!es.some(e => e.isIntersecting)) return;
  io.disconnect();
  load().then(m => { if (!m.Pano.supported) noGL(); }).catch(noGL);
}, { rootMargin: '900px 0px' }).observe(frame);

// sans WebGL : on garde les vues fixes, les onglets changent simplement l'image
let stills = false;
function noGL() {
  if (stills) return; stills = true;
  startBox.hidden = true; frame.classList.add('no-gl');
  const img = new Image(); img.className = 'tour-still'; img.alt = ''; img.decoding = 'async';
  $('#tour-poster').append(img);
  for (const t of tabs) t.addEventListener('click', () => {
    press(t.dataset.scene); img.classList.remove('is-on');
    img.onload = () => img.classList.add('is-on');
    img.src = narrow.matches ? t.dataset.stillTall : t.dataset.still;
  });
}

function enter() {
  return entering || (entering = (async () => {
    const { Pano } = await load();
    if (!Pano.supported) { noGL(); return false; }
    frame.classList.add('is-busy');
    try {
      pano = new Pano(canvas, {
        scenes: { ciel: R + 'assets/pano/ciel', entree: R + 'assets/pano/entree', salle: R + 'assets/pano/salle', terrasse: R + 'assets/pano/terrasse' },
        grain: 0.018, vignette: 0.16, onRender: place,
      });
    } catch (e) { noGL(); return false; }
    pano.setDrag('x');
    pano.frame({ ...(narrow.matches ? POSTER_TALL : HOME.terrasse) });
    await pano.ready; await pano.need('terrasse');
    frame.classList.remove('is-busy'); frame.classList.add('is-live');
    pinsBox.hidden = false; hint.hidden = false; canvas.tabIndex = 0;
    setTimeout(() => { startBox.hidden = true; }, 700);
    pano.onGrab = () => { grabbed = true; pano.autoRotate = 0; hint.hidden = true; };
    drift();
    if (document.fullscreenEnabled && frame.requestFullscreen) {
      full.hidden = false;
      full.addEventListener('click', () => (document.fullscreenElement ? document.exitFullscreen() : frame.requestFullscreen()));
      document.addEventListener('fullscreenchange', () => pano.setDrag(document.fullscreenElement === frame ? 'xy' : 'x'));
    }
    window.o82 = { pano };
    return true;
  })());
}
// la scène dérive très lentement tant qu'on ne l'a pas touchée — et seulement quand elle est à l'écran
const drift = () => { if (pano) pano.autoRotate = seen && !grabbed ? 1.1 : 0; };
new IntersectionObserver(es => { seen = es[0].isIntersecting; drift(); }, { threshold: 0.25 }).observe(frame);

function go(scene, view, towards) {
  press(scene);
  pano.walk(fit(view || HOME[scene]), towards ? { towards } : {});
}
enterBtn.addEventListener('click', enter);
for (const t of tabs) t.addEventListener('click', async () => {
  if (stills) return;
  const first = !pano;
  if (await enter() && !(first && t.dataset.scene === 'terrasse')) go(t.dataset.scene);
});

// repères accrochés dans la scène
const pins = $$('.pin', pinsBox).map(el => ({ el, scene: el.dataset.scene, yaw: +el.dataset.yaw, pitch: +el.dataset.pitch }));
function place(p) {
  const main = p.b && p.mix > 0.5 ? p.b : p.a, settled = !p.b || p.mix < 0.1 || p.mix > 0.96;
  for (const pin of pins) {
    let on = settled && pin.scene === main.scene;
    if (on) {
      const s = p.project(pin.yaw, pin.pitch, main);
      on = s.visible && s.x > 10 && s.x < p.W - 10 && s.y > 10 && s.y < p.H - 10;
      if (on) pin.el.style.transform = `translate(${s.x.toFixed(1)}px,${s.y.toFixed(1)}px)`;
    }
    pin.el.classList.toggle('is-on', on);
  }
}
for (const pin of pins) if (pin.el.dataset.to) pin.el.addEventListener('click', () => {
  const [yaw, pitch] = pin.el.dataset.in.split(',').map(Number), to = pin.el.dataset.to;
  go(to, { ...HOME[to], yaw, pitch }, { yaw: pin.yaw, pitch: pin.pitch * 0.5 });
});
