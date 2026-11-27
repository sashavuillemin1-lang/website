/* Ocean 82 — proposition 3 « Lagon ».
   Très peu de script : langue, apparitions, onglets de la carte, carrousel — et la visite 360°,
   chargée seulement quand on s'en approche. */
import { initLang, initReservation, reveal, getLang } from '../assets/js/site.js';

const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

initLang();
initReservation($('#resa-form'));
reveal();

// ------------------------------------------------------------------ la carte : une rubrique à la fois
const panels = $$('#carte-panels .carte-sec'), chips = $('#carte-chips');
let current = 'carte-froids';
const label = s => (getLang() === 'en' ? s.dataset.titleEn : s.dataset.title).replace(/^(Les|The) /, '').replace(/^./, c => c.toUpperCase());
function paint() {
  chips.innerHTML = panels.map(s => `<button type="button" data-go="${s.id}" aria-pressed="${s.id === current}">${label(s)}</button>`).join('');
  for (const s of panels) s.hidden = s.id !== current;
}
chips.addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  current = b.dataset.go; paint();
  const on = chips.querySelector('[aria-pressed="true"]'); if (on) on.focus({ preventScroll: true });
});
document.addEventListener('langchange', paint);
paint();
for (const b of $$('[data-carte]')) b.addEventListener('click', () => {
  current = 'carte-' + b.dataset.carte; paint();
  $('#carte-full').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
});

// ------------------------------------------------------------------ carrousel des assiettes (flèches pour la souris)
const plats = $('#plats');
for (const b of $$('[data-plats]')) b.addEventListener('click', () =>
  plats.scrollBy({ left: Number(b.dataset.plats) * plats.clientWidth * 0.7, behavior: reduced ? 'auto' : 'smooth' }));

// ------------------------------------------------------------------ visite 360° dans le hublot
const tour = $('#tour');
const near = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { near.disconnect(); initTour(); } }, { rootMargin: '700px 0px' });
near.observe(tour);

async function initTour() {
  const canvas = $('#tour-canvas'), enter = $('#tour-enter'), places = $$('#tour-chips button');
  const pins = $$('.tpin', tour).map(el => ({ el, scene: el.dataset.scene, yaw: Number(el.dataset.yaw), pitch: Number(el.dataset.pitch) }));
  const press = scene => places.forEach(c => c.setAttribute('aria-pressed', String(c.dataset.scene === scene)));

  let Pano = null;
  try { ({ Pano } = await import('../assets/js/pano.js')); } catch (e) { /* module indisponible */ }
  let pano = null;
  if (Pano && Pano.supported) {
    try {
      const base = '../assets/pano/';
      pano = new Pano(canvas, { scenes: { ciel: base + 'ciel', entree: base + 'entree', salle: base + 'salle', terrasse: base + 'terrasse' }, grain: 0.02, vignette: 0.22, onRender: place });
    } catch (e) { pano = null; }
  }
  if (!pano) return stills();

  pano.setDrag('x');
  const tall = () => canvas.clientHeight > canvas.clientWidth * 0.95;
  // la petite planète affichée par la toile coïncide avec l'affiche fixe, une image carrée cadrée en « cover » :
  // rendue à 276° pour le hublot large, à 252° pour l'arche des petits écrans (voir src/images.py)
  const planet = () => {
    const W = canvas.clientWidth, H = canvas.clientHeight;
    const fov = W > H ? 4 * Math.atan(Math.tan(69 * Math.PI / 180) * H / W) * 180 / Math.PI : 252;
    return { scene: 'ciel', yaw: -15, pitch: -90, fov, n: 2 };
  };
  const HOME = {
    ciel: { scene: 'ciel', yaw: -15, pitch: -12, fov: 74, n: 1.12 }, entree: { scene: 'entree', yaw: -5, pitch: 2, fov: 84, n: 1.15 },
    salle: { scene: 'salle', yaw: -25, pitch: -4, fov: 84, n: 1.14 }, terrasse: { scene: 'terrasse', yaw: -66, pitch: -8, fov: 84, n: 1.14 },
  };
  const fit = v => (tall() ? { ...v, fov: Math.min(v.fov * 1.24, 112), n: v.n + 0.1 } : v);
  let inside = false;

  pano.frame(planet());
  pano.ready.then(() => pano.need('ciel')).catch(() => {}).then(() => requestAnimationFrame(() => tour.classList.add('is-live')));
  const seen = new IntersectionObserver(es => { pano.autoRotate = es[0].isIntersecting && !inside ? 5 : 0; }, { threshold: 0.25 });
  seen.observe(tour);
  addEventListener('resize', () => { if (!inside) pano.frame(planet()); });

  function go(scene, view, towards) {
    inside = true; tour.classList.add('is-inside'); pano.autoRotate = 0; press(scene);
    return pano.walk(fit(view || HOME[scene]), towards ? { towards } : {});
  }
  enter.addEventListener('click', () => { go('entree'); canvas.focus({ preventScroll: true }); });
  for (const c of places) c.addEventListener('click', () => go(c.dataset.scene));
  for (const p of pins) if (p.el.dataset.to) p.el.addEventListener('click', () => {
    const to = p.el.dataset.to, v = p.el.dataset.in.split(',').map(Number);
    go(to, { ...HOME[to], yaw: v[0], pitch: v[1] }, { yaw: p.yaw, pitch: p.pitch * 0.5 });
  });

  function place(p) {
    const main = p.b && p.mix > 0.5 ? p.b : p.a, settled = !p.b || p.mix < 0.1 || p.mix > 0.96;
    for (const pin of pins) {
      let on = inside && settled && pin.scene === main.scene && main.n < 1.36;
      if (on) {
        const s = p.project(pin.yaw, pin.pitch, main);
        on = s.visible && s.x > 24 && s.x < p.W - 24 && s.y > 24 && s.y < p.H - 24;
        if (on) pin.el.style.transform = `translate(${s.x.toFixed(1)}px,${s.y.toFixed(1)}px)`;
      }
      pin.el.classList.toggle('is-on', on);
    }
  }

  // sans WebGL : les pastilles affichent simplement des vues fixes
  function stills() {
    const data = JSON.parse($('#tour-stills').textContent);
    tour.classList.add('is-still'); enter.hidden = true;
    for (const c of places) c.addEventListener('click', () => {
      press(c.dataset.scene);
      for (const s of $$('picture source', tour)) s.remove();
      for (const img of $$('picture img', tour)) { img.removeAttribute('srcset'); img.src = data[c.dataset.scene]; }
    });
  }
}
