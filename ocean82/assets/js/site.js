/*! site.js — petits utilitaires partagés par les trois maquettes Ocean 82 (langue, apparitions, réservation). */

const WHATSAPP = '590690777757', EMAIL = 'ocean.82@hotmail.fr';
const SEASON_START = '-12-01';            // à partir du 1er décembre : service dès 11h30 (sinon 15h00), jusqu'à 22h30

// ---------------------------------------------------------------- langue FR / EN
// Le français est dans le HTML ; la version anglaise est portée par data-en (contenu) ou data-en-<attribut>.
export function getLang() { return document.documentElement.lang === 'en' ? 'en' : 'fr'; }

export function setLang(lang) {
  const en = lang === 'en';
  for (const el of document.querySelectorAll('[data-en]')) {
    if (el.dataset.fr === undefined) el.dataset.fr = el.innerHTML;
    el.innerHTML = en ? el.dataset.en : el.dataset.fr;
  }
  for (const attr of ['alt', 'placeholder', 'aria-label', 'title', 'content']) {
    for (const el of document.querySelectorAll(`[data-en-${attr}]`)) {
      const key = 'fr' + attr.replace(/-(\w)/g, (m, c) => c.toUpperCase()).replace(/^\w/, c => c.toUpperCase());
      if (el.dataset[key] === undefined) el.dataset[key] = el.getAttribute(attr) || '';
      el.setAttribute(attr, en ? el.getAttribute(`data-en-${attr}`) : el.dataset[key]);
    }
  }
  document.documentElement.lang = en ? 'en' : 'fr';
  for (const b of document.querySelectorAll('[data-lang]')) b.setAttribute('aria-pressed', String(b.dataset.lang === lang));
  try { localStorage.setItem('o82-lang', lang); } catch (e) { /* navigation privée */ }
  document.dispatchEvent(new CustomEvent('langchange', { detail: lang }));
}

export function initLang() {
  let lang = new URLSearchParams(location.search).get('lang');
  if (!lang) { try { lang = localStorage.getItem('o82-lang'); } catch (e) { /* idem */ } }
  for (const b of document.querySelectorAll('[data-lang]')) b.addEventListener('click', () => setLang(b.dataset.lang));
  if (lang === 'en') setLang('en');
}

// ---------------------------------------------------------------- apparitions au défilement
export function reveal(selector = '[data-reveal]', options = { rootMargin: '0px 0px -8% 0px', threshold: 0.12 }) {
  const els = document.querySelectorAll(selector);
  if (!('IntersectionObserver' in window)) { els.forEach(e => e.classList.add('is-in')); return; }
  const io = new IntersectionObserver(entries => {
    for (const e of entries) if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
  }, options);
  els.forEach(e => io.observe(e));
}

// ---------------------------------------------------------------- réservation
// Maquette sans serveur : la demande est récapitulée puis confiée à WhatsApp ou au courriel du restaurant.
const pad = n => String(n).padStart(2, '0');

function slots(dateStr) {
  const y = (dateStr || '').slice(0, 4), lunch = !dateStr || dateStr >= y + SEASON_START;
  const out = [];
  for (let m = lunch ? 11 * 60 + 30 : 15 * 60; m <= 22 * 60 + 30; m += 30) out.push(pad(Math.floor(m / 60)) + ':' + pad(m % 60));
  return out;
}

export function initReservation(form) {
  if (!form) return;
  const date = form.elements.date, time = form.elements.time, done = form.parentElement.querySelector('.resa-done');
  const today = new Date(); today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
  date.min = today.toISOString().slice(0, 10);
  const fill = () => {
    const keep = time.value;
    time.innerHTML = slots(date.value).map(s => `<option${s === (keep || '19:30') ? ' selected' : ''}>${s}</option>`).join('');
  };
  date.addEventListener('change', fill); fill();

  form.addEventListener('submit', e => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const en = getLang() === 'en', v = n => form.elements[n].value.trim();
    const d = new Date(v('date') + 'T12:00:00');
    const when = d.toLocaleDateString(en ? 'en-US' : 'fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
    const n = +v('guests');
    const lines = en
      ? [`Hello, I would like to book a table at Ocean 82:`, `${when} at ${v('time')}, ${n} ${n > 1 ? 'guests' : 'guest'}.`, `Name: ${v('name')}`, `Phone: ${v('phone')}`]
      : [`Bonjour, je souhaite réserver une table chez Ocean 82 :`, `${when} à ${v('time').replace(':', 'h')}, ${n} ${n > 1 ? 'personnes' : 'personne'}.`, `Nom : ${v('name')}`, `Téléphone : ${v('phone')}`];
    if (v('email')) lines.push((en ? 'Email: ' : 'E-mail : ') + v('email'));
    if (v('message')) lines.push((en ? 'Special requests: ' : 'Demandes spéciales : ') + v('message'));
    const msg = lines.join('\n');
    done.querySelector('[data-resa-summary]').textContent = lines.slice(1, 2).join(' ') + ' — ' + v('name');
    done.querySelector('[data-resa-wa]').href = `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(msg)}`;
    done.querySelector('[data-resa-mail]').href = `mailto:${EMAIL}?subject=${encodeURIComponent(en ? 'Table reservation' : 'Réservation de table')}&body=${encodeURIComponent(msg)}`;
    form.hidden = true; done.hidden = false; done.focus();
  });
  done.querySelector('[data-resa-back]').addEventListener('click', () => { done.hidden = true; form.hidden = false; });
}
