#!/usr/bin/env python3
"""Photo pipeline for the Ocean 82 mockups.

Every image used by the three proposals comes from the photos already published on ocean82.fr.
This script turns the originals into correctly framed, lightweight derivatives:

  * PHOTOS  – art-directed crops (aspect ratio + focal point, so the subject is never cut),
              exported in AVIF + WebP at several widths.
  * STILLS  – flat, undistorted views rendered from the four 360° panoramas
              (the current site shows those panoramas flat, which bends the horizon).
  * PANOS   – the 360° panoramas themselves, resized for the WebGL tour.

usage:  python3 images.py --orig <dir with originals> [--sr <dir with upscaled x4 PNGs>] [--only slug,slug]
Originals are downloaded from https://ocean82.fr/wp-content/uploads/<year>/<month>/<file> (see SOURCES in the manifest).
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_IMG = os.path.join(HERE, '..', 'assets', 'img')
OUT_PANO = os.path.join(HERE, '..', 'assets', 'pano')

AVIF_Q, WEBP_Q = 56, 76
LADDER = [360, 480, 640, 800, 960, 1280, 1600, 1920, 2400]

# ---------------------------------------------------------------- photos
# slug: (source file, focal point (x, y) in 0..1, {variant: (aspect w, aspect h[, zoom])}, max output width)
O = 'OCEAN-82-GRAND-CASE-RESTAURANT-'
PHOTOS = {
    # --- le lieu
    'coucher-soleil':   ('2020-01_Tastevin-8.jpg',  (0.37, 0.52), {'3x2': (3, 2), '16x9': (16, 9), '4x5': (4, 5), '1x1': (1, 1)}, 2400),
    'terrasse-nuit':    ('2020-01_Tastevin-25.jpg', (0.55, 0.58), {'3x2': (3, 2), '16x9': (16, 9), '4x5': (4, 5), '1x1': (1, 1)}, 2400),
    'macarons':         ('2020-01_galerie4.png',    (0.44, 0.60), {'3x2': (3, 2), '4x5': (4, 5), '1x1': (1, 1)}, 1024),
    'diner-sunset':     ('2020-01_Screenshot_1.jpg', (0.45, 0.50), {'4x3': (4, 3)}, 598),
    # --- la cuisine
    'magret':           ('2020-01_o3.jpg',          (0.52, 0.48), {'2x1': (2, 1), '4x3': (4, 3), '1x1': (1, 1), '4x5': (4, 5)}, 1200),
    'huitres':          ('2020-01_%s12.jpg' % O,    (0.46, 0.47), {'1x1': (1, 1), '4x5': (4, 5)}, 1280),
    'thon-sesame':      ('2020-01_%s24.jpg' % O,    (0.50, 0.58), {'4x5': (4, 5), '1x1': (1, 1)}, 1280),
    'risotto':          ('2020-01_%s18.jpg' % O,    (0.52, 0.64), {'1x1': (1, 1), '4x5': (4, 5)}, 1280),
    'plat-sauce':       ('2020-01_%s19.jpg' % O,    (0.48, 0.45), {'1x1': (1, 1)}, 1280),
    'grenouilles':      ('2020-01_galerie2.png',    (0.60, 0.55), {'3x2': (3, 2), '1x1': (1, 1), '4x5': (4, 5)}, 1024),
    # --- les desserts
    'sphere-chocolat':  ('2020-01_galerie1.png',    (0.55, 0.55), {'3x2': (3, 2), '1x1': (1, 1), '4x5': (4, 5)}, 1024),
    'citron':           ('2020-01_%s21.jpg' % O,    (0.48, 0.58), {'4x5': (4, 5), '1x1': (1, 1), '3x4': (3, 4)}, 1280),
    'trio-desserts':    ('2020-01_%s16.jpg' % O,    (0.52, 0.47), {'4x5': (4, 5), '3x4': (3, 4)}, 1280),
    'entremets-rouge':  ('2020-01_79539131_1515673118581461_5720307993392709632_n.jpg', (0.48, 0.58), {'1x1': (1, 1), '4x5': (4, 5)}, 960),
    'entremets-exotique': ('2020-01_79681570_1515673055248134_6132528406023110656_n.jpg', (0.50, 0.58), {'1x1': (1, 1), '4x5': (4, 5)}, 960),
    'part-rouge':       ('2020-01_80060353_1515673178581455_6561330351648538624_n.jpg', (0.56, 0.60), {'1x1': (1, 1), '4x5': (4, 5)}, 960),
    # --- le vivier
    'langouste':        ('2020-01_%s15.jpg' % O,    (0.56, 0.52), {'4x3': (4, 3), '21x9': (21, 9), '16x9': (16, 9), '1x1': (1, 1), '4x5': (4, 5)}, 1920),
    'langoustes-vivier': ('2020-01_galerie3.png',   (0.50, 0.55), {'3x2': (3, 2), '16x9': (16, 9), '1x1': (1, 1)}, 1024),
    # --- la cave & le bar
    'cave-mur':         ('2020-01_%s17.jpg' % O,    (0.50, 0.48), {'1x1': (1, 1), '16x9': (16, 9), '4x5': (4, 5)}, 1600),
    'cave-allee':       ('2020-01_%s5.jpg' % O,     (0.55, 0.50), {'1x1': (1, 1), '4x5': (4, 5)}, 960),
    'cave-vitrine':     ('2020-01_80247262_1515673431914763_778308246527016960_n.jpg', (0.58, 0.44), {'1x1': (1, 1), '16x9': (16, 9), '3x2': (3, 2)}, 960),
    'barmaid':          ('2020-01_%s14.jpg' % O,    (0.50, 0.40), {'4x5': (4, 5), '1x1': (1, 1), '3x4': (3, 4)}, 1280),
    'cocktail':         ('2020-01_80373057_1515673238581449_8791977631789613056_n.jpg', (0.50, 0.52), {'4x5': (4, 5), '1x1': (1, 1)}, 768),
    # --- l'équipe & les instants
    'franck-romain':    ('2019-12_Screenshot_2.jpg', (0.36, 0.45), {'3x2': (3, 2), '4x3': (4, 3, 1.0)}, 595),
    'table-amis':       ('2020-01_%s11.jpg' % O,    (0.46, 0.56), {'4x3': (4, 3), '16x9': (16, 9)}, 1600),
    'plage':            ('2020-01_%s22.jpg' % O,    (0.55, 0.50), {'4x5': (4, 5), '3x4': (3, 4)}, 1280),
    'amis-mer':         ('2020-01_%s9.jpg' % O,     (0.50, 0.45), {'4x5': (4, 5)}, 768),
    'accueil':          ('2020-01_%s20.jpg' % O,    (0.50, 0.48), {'3x4': (3, 4), '4x5': (4, 5)}, 1280),
    'vivier-couple':    ('2020-01_%s23.jpg' % O,    (0.48, 0.42), {'4x3': (4, 3), '1x1': (1, 1)}, 1600),
    'amies-cave':       ('2020-01_%s8.jpg' % O,     (0.50, 0.45), {'4x3': (4, 3)}, 1024),
}
# photos for which an x4 upscaled source exists (name of the PNG in --sr): gives full-bleed heroes enough pixels
UPSCALED = {'coucher-soleil': 'Tastevin-8.x4.png', 'terrasse-nuit': 'Tastevin-25.x4.png'}

# ---------------------------------------------------------------- 360° panoramas
PANOS = {  # scene id: original file, upscaled file
    'ciel':     ('2020-01_Aerea-Restaurante-fb-Copier.jpg', 'Aerea-Restaurante-fb-Copier.x4.png'),
    'entree':   ('2020-01_lobster_fb-Copier.jpg',           'lobster_fb-Copier.x4.png'),
    'salle':    ('2020-01_barra_fb-Copier.jpg',             'barra_fb-Copier.x4.png'),
    'terrasse': ('2020-01_Balcon_fb-Copier.jpg',            'Balcon_fb-Copier.x4.png'),
}
# slug: (scene, yaw°, pitch°, vertical fov°, lens n (1 = rectilinear, 2 = stereographic), width, height)
STILLS = {
    'vue-ciel':          ('ciel', -15, -7, 54, 1.0, 1920, 1080),
    'vue-ciel-large':    ('ciel', -15, -10, 62, 1.1, 2400, 1030),
    'vue-ciel-tall':     ('ciel', -15, -6, 74, 1.1, 1200, 1500),
    'vue-ciel-carre':    ('ciel', -15, -8, 60, 1.0, 1400, 1400),
    'petite-planete':    ('ciel', -15, -90, 252, 2.0, 1600, 1600),      # affiche de la visite (écrans larges)
    'petite-planete-portrait': ('ciel', -15, -90, 276, 2.0, 1280, 1280),  # … et téléphones : mêmes réglages que immersion/app.js
    'baie':              ('ciel', -108, -2, 40, 1.0, 1920, 820),
    'vue-entree':        ('entree', -5, 2, 88, 1.15, 1920, 1080),
    'vue-vivier':        ('entree', 38, 2, 62, 1.0, 1920, 1080),
    'vue-vivier-tall':   ('entree', 36, 0, 78, 1.1, 1200, 1500),
    'vue-cave':          ('entree', -48, 6, 62, 1.0, 1920, 1080),
    'vue-cave-tall':     ('entree', -48, 3, 76, 1.1, 1200, 1500),
    'vue-salle':         ('salle', -25, -4, 80, 1.1, 1920, 1080),
    'vue-salle-tall':    ('salle', -22, -6, 92, 1.2, 1200, 1500),
    'vue-salle-tableaux': ('salle', -118, 0, 76, 1.0, 1920, 1080),
    'vue-bar':           ('salle', 135, -2, 72, 1.0, 1920, 1080),
    'vue-bar-tall':      ('salle', 128, -4, 84, 1.1, 1200, 1500),
    'vue-terrasse':      ('terrasse', -70, -8, 78, 1.0, 1920, 1080),
    'vue-terrasse-tall': ('terrasse', -62, -8, 92, 1.2, 1200, 1500),
    'vue-terrasse-large': ('terrasse', -72, -6, 66, 1.1, 2400, 1030),
    'vue-enfilade':      ('terrasse', 5, -6, 78, 1.0, 1920, 1080),
    'vue-enfilade-tall': ('terrasse', 8, -8, 92, 1.2, 1200, 1500),
}


def cover_box(w, h, aw, ah, fx, fy, zoom=1.0):
    """Largest aw:ah box inside w×h (shrunk by zoom), centred on the focal point and kept inside the frame."""
    a = aw / ah
    bw, bh = (w, w / a) if w / h <= a else (h * a, h)
    bw, bh = bw / zoom, bh / zoom
    x0 = min(max(fx * w - bw / 2, 0), w - bw)
    y0 = min(max(fy * h - bh / 2, 0), h - bh)
    return [int(round(x0)), int(round(y0)), int(round(x0 + bw)), int(round(y0 + bh))]


def widths_for(src_w, max_w):
    """Largest useful width plus two or three smaller steps (never upscales)."""
    top = min(src_w, max_w)
    ws = {top}
    for f in (0.66, 0.44, 0.28):
        cand = min(LADDER, key=lambda x: abs(x - top * f))
        if cand < top * 0.9: ws.add(cand)
    return sorted(ws)


def export(im, base, widths):
    """Write AVIF + WebP at each width. Returns [(w, h)]."""
    out = []
    for w in widths:
        h = int(round(im.height * w / im.width))
        r = im if w == im.width else im.resize((w, h), Image.LANCZOS)
        if w < im.width * 0.7:
            r = r.filter(ImageFilter.UnsharpMask(radius=0.6, percent=45, threshold=2))
        r.save('%s-%d.avif' % (base, w), 'AVIF', quality=AVIF_Q, speed=4)
        r.save('%s-%d.webp' % (base, w), 'WEBP', quality=WEBP_Q, method=6)
        out.append((w, h))
    return out


def render_still(a, yaw, pitch, vfov, W, H, n=1.0, ss=2):
    """Same camera model as assets/js/pano.js: theta = n * atan(r * tan(fov / 2n)), r = 1 at half the height."""
    sh, sw, _ = a.shape
    w, h = W * ss, H * ss
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    px = (xs + 0.5 - w / 2) / (h / 2); py = -(ys + 0.5 - h / 2) / (h / 2)
    r = np.sqrt(px * px + py * py) + 1e-9
    theta = n * np.arctan(r * np.tan(np.radians(vfov) / (2 * n)))
    st = np.sin(theta); dx, dy, dz = st * px / r, st * py / r, -np.cos(theta)
    p, yw = np.radians(pitch), np.radians(yaw)
    y1 = dy * np.cos(p) - dz * np.sin(p); z1 = dy * np.sin(p) + dz * np.cos(p)
    x2 = dx * np.cos(yw) - z1 * np.sin(yw); z2 = dx * np.sin(yw) + z1 * np.cos(yw)
    u = (np.arctan2(x2, -z2) / (2 * np.pi) + 0.5) * sw - 0.5
    v = (0.5 - np.arcsin(np.clip(y1, -1, 1)) / np.pi) * sh - 0.5
    u0 = np.floor(u).astype(np.int64); v0 = np.floor(v).astype(np.int64)
    fu = (u - u0)[..., None]; fv = (v - v0)[..., None]
    u1 = (u0 + 1) % sw; u0 %= sw
    v1 = np.clip(v0 + 1, 0, sh - 1); v0 = np.clip(v0, 0, sh - 1)
    o = a[v0, u0] * (1 - fu) * (1 - fv) + a[v0, u1] * fu * (1 - fv) + a[v1, u0] * (1 - fu) * fv + a[v1, u1] * fu * fv
    im = Image.fromarray(np.clip(o + 0.5, 0, 255).astype(np.uint8))
    return im.resize((W, H), Image.LANCZOS) if ss > 1 else im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--orig', required=True); ap.add_argument('--sr', default=None)
    ap.add_argument('--only', default=''); ap.add_argument('--skip-panos', action='store_true')
    ap.add_argument('--photos-only', action='store_true')
    args = ap.parse_args()
    only = set(filter(None, args.only.split(',')))
    os.makedirs(OUT_IMG, exist_ok=True); os.makedirs(OUT_PANO, exist_ok=True)
    mpath = os.path.join(OUT_IMG, 'manifest.json')
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}

    for slug, (src, focal, variants, max_w) in PHOTOS.items():
        if only and slug not in only: continue
        im = Image.open(os.path.join(args.orig, src)).convert('RGB')
        hi = None
        if args.sr and slug in UPSCALED and os.path.exists(os.path.join(args.sr, UPSCALED[slug])):
            hi = Image.open(os.path.join(args.sr, UPSCALED[slug])).convert('RGB')
        entry = {'source': src, 'focal': focal, 'variants': {}}
        for name, spec in variants.items():
            aw, ah = spec[0], spec[1]; zoom = spec[2] if len(spec) > 2 else 1.0
            box = cover_box(im.width, im.height, aw, ah, focal[0], focal[1], zoom)
            if hi is not None:
                k = hi.width / im.width
                crop = hi.crop(tuple(int(round(b * k)) for b in box))
                crop = crop.resize((min(crop.width, max_w), int(round(min(crop.width, max_w) * crop.height / crop.width))), Image.LANCZOS)
            else:
                crop = im.crop(tuple(box))
            sizes = export(crop, os.path.join(OUT_IMG, '%s-%s' % (slug, name)), widths_for(crop.width, max_w))
            entry['variants'][name] = {'crop': box, 'sizes': sizes}
        manifest[slug] = entry
        print('photo', slug, {k: [s[0] for s in v['sizes']] for k, v in entry['variants'].items()}, flush=True)

    cache = {}
    def pano_array(scene):
        if scene not in cache:
            orig, up = PANOS[scene]
            p = os.path.join(args.sr, up) if args.sr and os.path.exists(os.path.join(args.sr, up)) else os.path.join(args.orig, orig)
            cache.clear(); cache[scene] = (np.asarray(Image.open(p).convert('RGB')).astype(np.float32), p)
        return cache[scene]

    for scene in ([] if args.photos_only else PANOS):
        todo = [s for s, v in STILLS.items() if v[0] == scene and (not only or s in only)]
        do_pano = not args.skip_panos and (not only or ('pano-' + scene) in only)
        if not todo and not do_pano: continue
        arr, path = pano_array(scene)
        for slug in todo:
            _, yaw, pitch, fov, n, W, H = STILLS[slug]
            im = render_still(arr, yaw, pitch, fov, W, H, n)
            sizes = export(im, os.path.join(OUT_IMG, slug), widths_for(W, W))
            manifest[slug] = {'source': PANOS[scene][0], 'still': {'scene': scene, 'yaw': yaw, 'pitch': pitch, 'fov': fov, 'n': n},
                              'variants': {'': {'sizes': sizes}}}
            print('still', slug, [s[0] for s in sizes], flush=True)
        if do_pano:
            full = Image.fromarray(arr.astype(np.uint8))
            for w in (4096, 2048):
                r = full.resize((w, w // 2), Image.LANCZOS)
                r.save(os.path.join(OUT_PANO, '%s-%d.avif' % (scene, w)), 'AVIF', quality=58 if w > 2048 else 60, speed=4)
                r.save(os.path.join(OUT_PANO, '%s-%d.webp' % (scene, w)), 'WEBP', quality=78, method=6)
            full.resize((512, 256), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2)).save(
                os.path.join(OUT_PANO, '%s-512.webp' % scene), 'WEBP', quality=60, method=6)
            print('pano', scene, 'from', os.path.basename(path), flush=True)

    json.dump(manifest, open(mpath, 'w'), indent=1, sort_keys=True)
    print('manifest:', len(manifest), 'entries')


if __name__ == '__main__':
    main()
