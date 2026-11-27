/*! pano.js — visionneuse 360° WebGL sans dépendance (≈ 4 Ko gzip) pour les maquettes Ocean 82.
 *
 * Affiche une photo équirectangulaire sur un simple quad plein écran : la direction de chaque pixel
 * est calculée dans le fragment shader. Modèle de caméra à un paramètre :
 *     theta = n · atan(r · tan(fov / 2n))        n = 1 rectiligne … n = 2 stéréographique (« petite planète »)
 * ce qui permet de passer en continu d'une petite planète vue du ciel à une vue normale à hauteur d'yeux.
 * Deux scènes peuvent être fondues (uMix) avec un flou radial (uBlur) : c'est la transition « on avance ».
 */

const RAD = Math.PI / 180;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const lerpAngle = (a, b, t) => a + ((((b - a) % 360) + 540) % 360 - 180) * t;
export const ease = t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

const BODY = `
uniform sampler2D tA, tB;
uniform mat3 rA, rB;
uniform vec3 lA, lB;          // c = tan(fov/2n), n, hauteur de la texture
uniform vec2 uAspect, uCenter;
uniform float uMix, uBlur, uGrain, uVig, uPx, uSeed, uDim;

vec3 look(sampler2D t, mat3 R, vec3 l, vec2 q) {
  float r = length(q) + 1e-6;
  float th = l.y * atan(r * l.x);
  float s = sin(th);
  vec3 d = R * vec3(s * q.x / r, s * q.y / r, -cos(th));
  vec2 uv = vec2(atan(d.x, -d.z) * 0.15915494 + 0.5, acos(clamp(d.y, -1., 1.)) * 0.31830989);
  // niveau de mip calculé analytiquement (pas de dérivées : ni couture à ±180°, ni tache aux pôles)
  float lod = log2(max(l.y * l.x / (1. + r * r * l.x * l.x) * uPx * l.z * 0.31830989, 1e-6));
  return TEX(t, uv, max(lod - 0.4, 0.)).rgb;
}
vec3 scene(sampler2D t, mat3 R, vec3 l) {
  if (uBlur < 0.002) return look(t, R, l, v);
  float j = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233)) + uSeed) * 43758.5453);   // tramage : pas de stries
  vec3 c = vec3(0.);
  for (int i = 0; i < 8; i++) c += look(t, R, l, v * (1. + uBlur * ((float(i) + j) / 8. - 0.5)));
  return c / 8.;
}
void main() {
  vec3 c = scene(tA, rA, lA);
  if (uMix > 0.001) {
    // la nouvelle scène apparaît d'abord au centre, comme lorsqu'on franchit une porte
    float m = smoothstep(0., 1., uMix * 1.6 - 0.6 * length(v) / length(uAspect));
    c = mix(c, scene(tB, rB, lB), m);
  }
  c *= mix(1., 1. - smoothstep(0.3, 1.5, length((v + uCenter) * vec2(0.8, 1.))), uVig) * uDim;
  c += (fract(sin(dot(gl_FragCoord.xy + uSeed, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) * uGrain;
  OUT = vec4(c, 1.);
}`;
const VS2 = `#version 300 es
in vec2 p; out vec2 v; uniform vec2 uAspect, uCenter;
void main(){ v = p * uAspect - uCenter; gl_Position = vec4(p, 0., 1.); }`;
const FS2 = `#version 300 es
precision highp float;
#define TEX(t, uv, lod) textureLod(t, uv, lod)
#define OUT o
in vec2 v; out vec4 o;` + BODY;
const VS1 = `attribute vec2 p; varying vec2 v; uniform vec2 uAspect, uCenter;
void main(){ v = p * uAspect - uCenter; gl_Position = vec4(p, 0., 1.); }`;
const FS1 = `precision highp float;
#define TEX(t, uv, lod) texture2D(t, uv)
#define OUT gl_FragColor
varying vec2 v;` + BODY;

// AVIF 1×1 (pour savoir quel format demander sans téléchargement inutile)
const AVIF_PROBE = 'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADrbWV0YQAAAAAAAAAhaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAAAAAAAOcGl0bQAAAAAAAQAAAB5pbG9jAAAAAEQAAAEAAQAAAAEAAAETAAAAIwAAAChpaW5mAAAAAAABAAAAGmluZmUCAAAAAAEAAGF2MDFDb2xvcgAAAABqaXBycAAAAEtpcGNvAAAAFGlzcGUAAAAAAAAAAQAAAAEAAAAQcGl4aQAAAAADCAgIAAAADGF2MUOBAAwAAAAAE2NvbHJuY2x4AAEADQAGgAAAABdpcG1hAAAAAAAAAAEAAQQBAoMEAAAAK21kYXQSAAoIGAAGiAhoNCAyFRxHh4Xd0000wsAAAJA1jjx6zAQcgA==';
let avifOK;
const supportsAvif = () => avifOK || (avifOK = new Promise(res => {
  const i = new Image();
  i.onload = () => res(i.width === 1); i.onerror = () => res(false); i.src = AVIF_PROBE;
}));

export class Pano {
  static get supported() {
    try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); }
    catch (e) { return false; }
  }

  /** scenes: { id: 'chemin/vers/id' } → fichiers id-512.webp, id-2048.{avif,webp}, id-4096.{avif,webp} */
  constructor(canvas, { scenes, dprMax = 2, maxPixels = 3.6e6, grain = 0.035, vignette = 0.45, onRender = null, level = null } = {}) {
    this.canvas = canvas; this.scenes = scenes; this.dprMax = dprMax; this.maxPixels = maxPixels; this.onRender = onRender;
    this.grain = grain; this.vignette = vignette; this.dim = 1;
    this.center = [0, 0];              // décalage du centre optique, en demi-hauteurs d'écran (x vers la droite, y vers le haut)
    this.reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const opts = { alpha: false, antialias: false, depth: false, stencil: false, powerPreference: 'high-performance' };
    const gl = this.gl = canvas.getContext('webgl2', opts) || canvas.getContext('webgl', opts);
    if (!gl) throw new Error('WebGL indisponible');
    this.v2 = typeof WebGL2RenderingContext !== 'undefined' && gl instanceof WebGL2RenderingContext;
    this.tex = new Map(); this.loads = new Map();     // id → { tex, h, level, used }
    this.a = { scene: Object.keys(scenes)[0], yaw: 0, pitch: 0, fov: 80, n: 1.1 };
    this.b = null; this.mix = 0; this.blur = 0;
    this.uy = 0; this.up = 0; this.vy = 0; this.vp = 0;      // regard libre de l'utilisateur (offsets + inertie)
    this.autoRotate = 0; this.dragging = false; this.tweens = new Set(); this.dirty = true; this.alive = true;
    const conn = navigator.connection || {};
    const small = Math.min(screen.width, screen.height) < 500 && (navigator.deviceMemory || 4) < 4;
    this.level = level || (conn.saveData || small || gl.getParameter(gl.MAX_TEXTURE_SIZE) < 4096 ? 2048 : 4096);
    this._init();
    this._resize = this._resize.bind(this); this._tick = this._tick.bind(this);
    this.ro = new ResizeObserver(this._resize); this.ro.observe(canvas); this._resize();
    this.onscreen = true;              // hors écran : on ne dessine plus (visionneuses intégrées dans une page)
    this.io = new IntersectionObserver(es => { this.onscreen = es[es.length - 1].isIntersecting; if (this.onscreen) this.dirty = true; });
    this.io.observe(canvas);
    canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); this.lost = true; });
    canvas.addEventListener('webglcontextrestored', () => { this.lost = false; this.tex.clear(); this._init(); this.preload(Object.keys(scenes)); this.need(this.a.scene); });
    this._controls();
    this.ready = this.preload(Object.keys(scenes));
    requestAnimationFrame(this._tick);
  }

  _init() {
    const gl = this.gl, mk = (type, src) => {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    };
    const pr = this.prog = gl.createProgram();
    gl.attachShader(pr, mk(gl.VERTEX_SHADER, this.v2 ? VS2 : VS1));
    gl.attachShader(pr, mk(gl.FRAGMENT_SHADER, this.v2 ? FS2 : FS1));
    gl.bindAttribLocation(pr, 0, 'p'); gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(pr));
    gl.useProgram(pr);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);   // un seul triangle couvrant
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    this.u = {};
    for (const n of ['tA', 'tB', 'rA', 'rB', 'lA', 'lB', 'uAspect', 'uCenter', 'uMix', 'uBlur', 'uGrain', 'uVig', 'uPx', 'uSeed', 'uDim'])
      this.u[n] = gl.getUniformLocation(pr, n);
    gl.uniform1i(this.u.tA, 0); gl.uniform1i(this.u.tB, 1);
    this.aniso = gl.getExtension('EXT_texture_filter_anisotropic');
    // texture neutre en attendant les images
    this.blank = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, this.blank);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, 1, 1, 0, gl.RGB, gl.UNSIGNED_BYTE, new Uint8Array([18, 14, 12]));
  }

  async _image(url) {
    const inline = globalThis.O82_INLINE && globalThis.O82_INLINE[url.split('/').pop()];   // version « un seul fichier » : images intégrées à la page
    if (inline) url = inline;
    if (typeof createImageBitmap === 'function') {
      try { return await createImageBitmap(await (await fetch(url)).blob()); } catch (e) { /* repli ci-dessous */ }
    }
    const img = new Image(); img.decoding = 'async'; img.src = url; await img.decode(); return img;
  }

  _upload(id, img, level) {
    if (!this.alive || this.lost) return;
    const gl = this.gl, old = this.tex.get(id);
    if (old && old.level >= level) { if (img.close) img.close(); return; }     // un aperçu tardif n'écrase pas la version nette
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, img);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    if (this.v2) {
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      if (this.aniso) gl.texParameterf(gl.TEXTURE_2D, this.aniso.TEXTURE_MAX_ANISOTROPY_EXT, 4);
    } else gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    if (old && old.tex !== this.blank) gl.deleteTexture(old.tex);
    this.tex.set(id, { tex: t, h: img.height, level, used: performance.now() });
    if (img.close) img.close();
    this.dirty = true;
  }

  /** Charge les aperçus (≈ 6 Ko chacun) : il y a toujours quelque chose à afficher. */
  preload(ids) {
    return Promise.all(ids.map(async id => {
      if (this.tex.has(id)) return;
      this.tex.set(id, { tex: this.blank, h: 1, level: 0, used: 0 });
      try { this._upload(id, await this._image(this.scenes[id] + '-512.webp'), 512); } catch (e) { /* hors-ligne */ }
    }));
  }

  /** Demande la version nette d'une scène (au plus deux en mémoire à la fois). */
  need(id) {
    const e = this.tex.get(id);
    if (e) e.used = performance.now();
    if (e && e.level >= this.level) return Promise.resolve();
    if (!this.loads.has(id)) this.loads.set(id, this._load(id).finally(() => this.loads.delete(id)));
    return this.loads.get(id);
  }
  async _load(id) {
    if (!this.tex.has(id)) await this.preload([id]);
    const ext = (await supportsAvif()) ? 'avif' : 'webp';
    try {
      this._upload(id, await this._image(`${this.scenes[id]}-${this.level}.${ext}`), this.level);
      const hi = [...this.tex].filter(([k, t]) => t.level > 512 && k !== this.a.scene && !(this.b && k === this.b.scene))
        .sort((x, y) => x[1].used - y[1].used);
      while (hi.length > 1) this._drop(hi.shift()[0]);
    } catch (err) { /* on reste sur l'aperçu */ }
  }
  async _drop(id) {
    const t = this.tex.get(id); if (!t) return;
    if (t.tex !== this.blank) this.gl.deleteTexture(t.tex);
    this.tex.delete(id); await this.preload([id]);
  }

  _resize() {
    const c = this.canvas;      // la densité est plafonnée : au-delà de ~3,6 Mpx le gain est invisible et le coût bien réel
    const dpr = Math.max(0.75, Math.min(window.devicePixelRatio || 1, this.dprMax, Math.sqrt(this.maxPixels / Math.max(1, c.clientWidth * c.clientHeight))));
    const w = Math.max(1, Math.round(c.clientWidth * dpr)), h = Math.max(1, Math.round(c.clientHeight * dpr));
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    this.W = c.clientWidth || 1; this.H = c.clientHeight || 1; this.dirty = true;
  }

  // ---------------------------------------------------------------- caméra
  _basis(yaw, pitch) {
    const y = yaw * RAD, p = pitch * RAD, cy = Math.cos(y), sy = Math.sin(y), cp = Math.cos(p), sp = Math.sin(p);
    return [cy, 0, sy, -sp * sy, cp, sp * cy, -cp * sy, -sp, cp * cy];   // colonnes : droite, haut, arrière
  }
  _eye(v) { return { yaw: v.yaw + this.uy, pitch: clamp(v.pitch + this.up, -90, 90), fov: v.fov, n: v.n }; }

  /** Position écran (px CSS) d'une direction du monde — pour épingler des libellés HTML dans la scène. */
  project(yaw, pitch, view = this.a) {
    const e = this._eye(view), R = this._basis(e.yaw, e.pitch);
    const y = yaw * RAD, p = pitch * RAD, d = [Math.cos(p) * Math.sin(y), Math.sin(p), -Math.cos(p) * Math.cos(y)];
    const x = d[0] * R[0] + d[1] * R[1] + d[2] * R[2], yy = d[0] * R[3] + d[1] * R[4] + d[2] * R[5], z = d[0] * R[6] + d[1] * R[7] + d[2] * R[8];
    const th = Math.acos(clamp(-z, -1, 1));
    if (th / e.n > Math.PI / 2 - 0.02) return { x: 0, y: 0, visible: false };
    const r = Math.tan(th / e.n) / Math.tan(e.fov * RAD / (2 * e.n)), s = Math.hypot(x, yy) || 1e-9;
    const X = ((r * x / s + this.center[0]) / (this.W / this.H) * 0.5 + 0.5) * this.W, Y = (0.5 - (r * yy / s + this.center[1]) * 0.5) * this.H;
    return { x: X, y: Y, visible: X > -60 && X < this.W + 60 && Y > -60 && Y < this.H + 60 };
  }

  /** Fixe la ou les vues affichées. b + mix servent aux transitions pilotées (défilement). */
  frame(a, b = null, mix = 0, blur = 0) {
    this.a = a; this.b = b; this.mix = mix; this.blur = blur; this.dirty = true;
    this.need(a.scene); if (b) this.need(b.scene);
  }

  tween(duration, fn, easing = ease) {
    return new Promise(res => {
      const t = { t0: performance.now(), d: this.reduced ? Math.min(duration, 1) : duration, fn, easing, res };
      this.tweens.add(t);
    });
  }
  stop() { for (const t of this.tweens) t.res(false); this.tweens.clear(); }

  /** Tourne la tête vers une autre vue de la même scène. */
  look(to, duration = 1400) {
    this.stop();
    const from = { ...this._eye(this.a), scene: this.a.scene }; this.uy = this.up = this.vy = this.vp = 0;
    return this.tween(duration, k => this.frame({
      scene: from.scene, yaw: lerpAngle(from.yaw, to.yaw, k), pitch: lerp(from.pitch, to.pitch, k),
      fov: lerp(from.fov, to.fov ?? from.fov, k), n: lerp(from.n, to.n ?? from.n, k) }));
  }

  /** « On avance » : la scène courante se resserre, la suivante s'ouvre depuis le centre. */
  async walk(to, { duration = 1900, towards = null } = {}) {
    this.stop();
    const from = { ...this._eye(this.a), scene: this.a.scene }; this.uy = this.up = this.vy = this.vp = 0;
    if (to.scene === from.scene) return this.look(to, duration * 0.75);
    this.need(to.scene);
    if (towards && !this.reduced) await this.look({ ...from, ...towards }, 700);
    const A = { ...this._eye(this.a), scene: from.scene };
    const done = await this.tween(duration, k => {
      const a = { ...A, fov: A.fov * (1 - 0.38 * k) };
      const b = { ...to, fov: to.fov * (1 + 0.3 * (1 - k)) };
      this.frame(a, b, clamp((k - 0.12) / 0.7, 0, 1), this.reduced ? 0 : 0.3 * Math.sin(Math.PI * k));
    });
    if (done !== false) this.frame({ ...to });
    return done;
  }

  /** En mode « défilement », le regard libre revient doucement vers la vue prévue. */
  relax(k = 0.12) { if (!this.dragging) { this.uy *= 1 - k; this.up *= 1 - k; this.dirty = true; } }

  setDrag(mode) {     // 'x' : le glissement vertical laisse défiler la page · 'xy' : regard totalement libre · false
    this.drag = mode;
    this.canvas.style.touchAction = mode === 'xy' ? 'none' : mode === 'x' ? 'pan-y' : 'auto';
    this.canvas.style.cursor = mode ? 'grab' : '';
  }

  _controls() {
    const c = this.canvas; let last = null;
    c.addEventListener('pointerdown', e => {
      if (!this.drag || (e.pointerType === 'mouse' && e.button !== 0)) return;
      last = { x: e.clientX, y: e.clientY, t: e.timeStamp }; this.dragging = true; this.vy = this.vp = 0;
      try { c.setPointerCapture(e.pointerId); } catch (err) {}
      c.style.cursor = 'grabbing'; this.onGrab && this.onGrab();
    });
    c.addEventListener('pointermove', e => {
      if (!last) return;
      const k = this._eye(this.a).fov / this.H * (this.a.n > 1.5 ? 0.45 : 1);
      const dx = (e.clientX - last.x) * k, dy = (e.clientY - last.y) * k;
      this.uy -= dx; this.up = clamp(this.up + dy, -90 - this.a.pitch, 90 - this.a.pitch);
      this.vy = -dx; this.vp = dy; last = { x: e.clientX, y: e.clientY, t: e.timeStamp }; this.dirty = true;
    });
    const end = () => { if (last) { last = null; this.dragging = false; c.style.cursor = this.drag ? 'grab' : ''; } };
    c.addEventListener('pointerup', end); c.addEventListener('pointercancel', end); c.addEventListener('lostpointercapture', end);
    c.addEventListener('keydown', e => {
      const m = { ArrowLeft: [-8, 0], ArrowRight: [8, 0], ArrowUp: [0, 6], ArrowDown: [0, -6] }[e.key];
      if (!m || !this.drag) return;
      e.preventDefault(); this.uy += m[0]; this.up = clamp(this.up + m[1], -90 - this.a.pitch, 90 - this.a.pitch); this.dirty = true;
    });
  }

  _tick(now) {
    if (!this.alive) return;
    requestAnimationFrame(this._tick);
    for (const t of [...this.tweens]) {
      const k = clamp((now - t.t0) / t.d, 0, 1); t.fn(t.easing(k), k);
      if (k >= 1) { this.tweens.delete(t); t.res(true); }
    }
    if (!this.dragging && !this.reduced && this.onscreen) {
      if (Math.abs(this.vy) + Math.abs(this.vp) > 0.01) {
        this.uy += this.vy; this.up = clamp(this.up + this.vp, -90 - this.a.pitch, 90 - this.a.pitch);
        this.vy *= 0.93; this.vp *= 0.93; this.dirty = true;
      } else if (this.autoRotate && !this.tweens.size && !document.hidden) {
        this.uy += this.autoRotate * Math.min(now - (this._last || now), 50) / 1000; this.dirty = true;
      }
    }
    this._last = now;
    if (this.dirty && !this.lost && this.onscreen) { this.dirty = false; this._draw(); if (this.onRender) this.onRender(this); }
  }

  _draw() {
    const gl = this.gl, u = this.u, c = this.canvas;
    gl.viewport(0, 0, c.width, c.height);
    const bind = (unit, view, R, L) => {
      const e = this._eye(view), t = this.tex.get(view.scene) || { tex: this.blank, h: 1 };
      t.used = performance.now();
      gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t.tex);
      gl.uniformMatrix3fv(R, false, this._basis(e.yaw, e.pitch));
      gl.uniform3f(L, Math.tan(e.fov * RAD / (2 * e.n)), e.n, t.h);
    };
    bind(0, this.a, u.rA, u.lA); bind(1, this.b || this.a, u.rB, u.lB);
    gl.uniform2f(u.uAspect, c.width / c.height, 1); gl.uniform2f(u.uCenter, this.center[0], this.center[1]);
    gl.uniform1f(u.uMix, this.b ? this.mix : 0); gl.uniform1f(u.uBlur, this.blur);
    gl.uniform1f(u.uGrain, this.grain); gl.uniform1f(u.uVig, this.vignette); gl.uniform1f(u.uDim, this.dim);
    gl.uniform1f(u.uPx, 2 / c.height); gl.uniform1f(u.uSeed, (this.dragging || this.tweens.size) ? Math.random() * 97 : 7);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  destroy() {
    this.alive = false; this.ro.disconnect(); this.io.disconnect(); this.stop();
    const ext = this.gl.getExtension('WEBGL_lose_context'); if (ext) ext.loseContext();
  }
}

export const blendViews = (a, b, t) => ({
  scene: a.scene, yaw: lerpAngle(a.yaw, b.yaw, t), pitch: lerp(a.pitch, b.pitch, t), fov: lerp(a.fov, b.fov, t), n: lerp(a.n, b.n, t) });
