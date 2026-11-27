#!/usr/bin/env python3
"""Assemble les pages statiques des maquettes Ocean 82 à partir de src/<page>/ (aucune dépendance).

    python3 build.py            # construit index.html + immersion/ + maison/ + lagon/
    python3 build.py --prune    # … et supprime de assets/img les déclinaisons qu'aucune page n'utilise

Macros disponibles dans page.html, style.css et app.js :
    [[pic: clé | sizes | alt fr | alt en | options]]   <picture> AVIF + WebP, dimensions et chargement différé
                                                        options : eager · class=… · w=… (largeur maxi)
    [[url: clé | largeur | ext]]                        URL d'une déclinaison (webp par défaut, la plus grande si largeur omise)
    [[inc: fichier]]                                    inclusion depuis src/partials/
    [[css]]  [[menu]]  [[digestifs]]  [[info.xxx]]      styles en ligne, carte, digestifs, coordonnées
    [[clé]]                                             valeur lue dans src/<page>/vars.json (chiffres mesurés, textes)
"""
import html, json, os, re, sys

from content import DIGESTIFS, INFO, MENU, SIDES, TAX

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
MANIFEST = json.load(open(os.path.join(ROOT, 'assets', 'img', 'manifest.json')))
PAGES = {'hub': ('index.html', ''), 'immersion': ('immersion/index.html', '../'),
         'maison': ('maison/index.html', '../'), 'lagon': ('lagon/index.html', '../')}
used = set()
esc = lambda s: html.escape(s, quote=True)


def sizes_of(key):
    if key in MANIFEST:
        return MANIFEST[key]['variants']['']['sizes']
    slug, _, var = key.rpartition('-')
    return MANIFEST[slug]['variants'][var]['sizes']


def img_url(key, w, ext, prefix):
    used.add('%s-%d.%s' % (key, w, ext))
    return '%sassets/img/%s-%d.%s' % (prefix, key, w, ext)


def pic(prefix, key, sizes='100vw', alt_fr='', alt_en='', options=''):
    opts = options.split()
    cap = next((int(o[2:]) for o in opts if o.startswith('w=')), 10 ** 6)
    sz = [s for s in sizes_of(key) if s[0] <= cap] or sizes_of(key)[:1]
    W, H = sz[-1]
    cls = next((o[6:] for o in opts if o.startswith('class=')), '')
    srcset = lambda ext: ', '.join('%s %dw' % (img_url(key, w, ext, prefix), w) for w, _ in sz)
    load = 'loading="eager" fetchpriority="high"' if 'eager' in opts else 'loading="lazy"'
    return ('<picture%s><source type="image/avif" srcset="%s" sizes="%s">'
            '<img src="%s" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s"%s %s decoding="async"></picture>') % (
        ' class="%s"' % cls if cls else '', srcset('avif'), esc(sizes), img_url(key, W, 'webp', prefix), srcset('webp'),
        esc(sizes), W, H, esc(alt_fr), ' data-en-alt="%s"' % esc(alt_en) if alt_en else '', load)


def price(p):
    return p if ('/' in p or '€' in p) else p + ' €'


def render_menu(wrap='section'):
    """Carte complète, balisage sémantique commun ; chaque maquette l'habille avec son propre CSS."""
    out = []
    for sec in MENU:
        rows = []
        for it in sec['items']:
            fr, en, pr = it[0], it[1], it[2]
            opts = ''
            if len(it) > 3:
                opts = '<ul class="dish-opts">%s</ul>' % ''.join(
                    '<li><span class="dish-name">%s <i lang="en">%s</i></span><span class="dots" aria-hidden="true"></span>'
                    '<span class="dish-price">%s</span></li>' % (esc(a), esc(b), price(c)) for a, b, c in it[3])
            rows.append('<li class="dish"><div class="dish-row"><span class="dish-name">%s</span>'
                        '<span class="dots" aria-hidden="true"></span><span class="dish-price">%s</span></div>'
                        '<p class="dish-en" lang="en">%s</p>%s</li>' % (esc(fr), price(pr), esc(en), opts))
        sides = '<p class="carte-sides">%s <span lang="en">%s</span></p>' % (esc(SIDES[0]), esc(SIDES[1])) if sec.get('sides') else ''
        head = '<span class="carte-fr">%s</span> <span class="carte-en" lang="en">%s</span>' % (esc(sec['fr']), esc(sec['en']))
        body = '<ul class="carte-list">%s</ul>%s' % (''.join(rows), sides)
        if wrap == 'details':
            out.append('<details class="carte-sec" id="carte-%s"%s><summary>%s</summary>%s</details>' % (
                sec['id'], ' open' if sec['id'] == 'poissons' else '', head, body))
        else:
            out.append('<section class="carte-sec" id="carte-%s" data-title="%s" data-title-en="%s"><h3>%s</h3>%s</section>' % (
                sec['id'], esc(sec['fr']), esc(sec['en']), head, body))
    return '\n'.join(out)


def render_digestifs():
    out = []
    for fr, en, items in DIGESTIFS:
        rows = ''.join('<li><span class="dish-name">%s</span><span class="dots" aria-hidden="true"></span>'
                       '<span class="dish-price">%s</span></li>' % (esc(n), price(p)) for n, p in items)
        out.append('<div class="dig"><h4 data-en="%s">%s</h4><ul>%s</ul></div>' % (esc(en), esc(fr), rows))
    return '\n'.join(out)


def minify_css(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s*([{};,>])\s*', r'\1', s)
    return s.replace(';}', '}').strip()


def expand(text, page, prefix):
    src = os.path.join(HERE, page)
    vpath = os.path.join(src, 'vars.json')        # textes et chiffres propres à une page : [[clé]]
    page_vars = json.load(open(vpath, encoding='utf-8')) if os.path.exists(vpath) else {}

    def macro(m):
        body = m.group(1).strip()
        name, _, rest = body.partition(':')
        name = name.strip(); args = [a.strip() for a in rest.split('|')] if rest else []
        if name == 'pic':
            return pic(prefix, *args)
        if name == 'url':
            key = args[0]; sz = sizes_of(key)
            w = int(args[1]) if len(args) > 1 and args[1] else sz[-1][0]
            return img_url(key, w, args[2] if len(args) > 2 else 'webp', prefix)
        if name == 'inc':
            return expand(open(os.path.join(HERE, 'partials', args[0]), encoding='utf-8').read(), page, prefix)
        if name == 'css':
            return '<style>%s</style>' % minify_css(expand(open(os.path.join(src, 'style.css'), encoding='utf-8').read(), page, prefix))
        if name == 'menu':
            return render_menu(args[0] if args else 'section')
        if name == 'digestifs':
            return render_digestifs()
        if name.startswith('info.'):
            return esc(INFO[name[5:]])
        if name == 'tax':
            return '%s <span lang="en">%s</span>' % (esc(TAX[0]), esc(TAX[1]))
        if name == 'root':
            return prefix
        if name in page_vars:
            return page_vars[name]
        raise SystemExit('macro inconnue dans %s : [[%s]]' % (page, body))

    return re.sub(r'\[\[(.+?)\]\]', macro, text, flags=re.S)


def build(page):
    out, prefix = PAGES[page]
    src = os.path.join(HERE, page)
    if not os.path.exists(os.path.join(src, 'page.html')):
        return False
    dest = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    page_html = expand(open(os.path.join(src, 'page.html'), encoding='utf-8').read(), page, prefix)
    open(dest, 'w', encoding='utf-8').write(page_html)
    total = len(page_html.encode())
    for f in sorted(os.listdir(src)):
        if f.endswith('.js'):
            js = expand(open(os.path.join(src, f), encoding='utf-8').read(), page, prefix)
            open(os.path.join(os.path.dirname(dest), f), 'w', encoding='utf-8').write(js)
            total += len(js.encode())
    print('%-10s → %-22s %6.1f Ko (HTML + CSS en ligne + JS)' % (page, out, total / 1024))
    return True


if __name__ == '__main__':
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    built = [p for p in PAGES if (not only or p in only) and build(p)]
    if '--prune' in sys.argv:
        if set(built) != set(PAGES):
            raise SystemExit('--prune exige que toutes les pages soient construites')
        d = os.path.join(ROOT, 'assets', 'img'); n = 0
        for f in os.listdir(d):
            if f.endswith(('.avif', '.webp')) and f not in used and not f.startswith('hub-'):
                os.remove(os.path.join(d, f)); n += 1
        print('%d déclinaisons inutilisées supprimées, %d conservées' % (n, len(used)))
