"""Ocean 82 — maquette 3D stylisée du restaurant (Blender / Cycles, sans interface).

usage : python scene.py <ambiance> <vue> <sortie.png> [largeur hauteur échantillons]
  ambiance : bleue (heure bleue) | chocolat (crépuscule chaud) | ivoire (maquette claire, de jour)
  vue      : face | ext | tall (téléphone) | vivier | carte | maquette (sur socle, fond transparent — ambiance ivoire)

(Un mode « trait », dessin d'architecte au trait, est amorcé dans le code mais n'est pas abouti.)

Dépendance : Blender en module Python (pip install bpy). Les textures de tex/ sont la carte 2027 composée
(tex/carte.html → carte.png) et deux photos du restaurant, accrochées au-dessus du vivier.

Le modèle est volontairement épuré : pavillon sur pilotis au bord de l'eau, terrasse à poteaux et jambes de force,
salle ouverte sur la baie, cave vitrée et vivier à langoustes sur le mur du fond. Les proportions suivent les photos.
"""
import math, os, random, sys
import bpy
import bmesh
from mathutils import Vector

MOOD, VIEW, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
RW, RH, SAMPLES = (int(a) for a in (sys.argv[4:7] + ['1280', '800', '64'])[:3])
HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(82)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection
NIGHT = MOOD in ('bleue', 'chocolat')
CLAY, LINE, WARMSKY = MOOD == 'ivoire', MOOD == 'trait', MOOD == 'chocolat'
INSIDE = VIEW in ('vivier', 'carte')
MODEL = VIEW == 'maquette'          # maquette d'architecte posée sur un socle, fond transparent

# ------------------------------------------------------------------ matériaux
lin = lambda h: tuple(((int(h[i:i + 2], 16) / 255) ** 2.2) for i in (1, 3, 5))


def mat(name, hexcol, rough=0.6, metal=0.0, emit=None, power=0.0, trans=0.0, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin(hexcol), 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if emit:
        b.inputs['Emission Color'].default_value = (*lin(emit), 1); b.inputs['Emission Strength'].default_value = power
    if trans:
        b.inputs['Transmission Weight'].default_value = trans
    return m


def photo(name, path, power=0.0):
    """Une photo du restaurant, tirée telle quelle (tirage encadré, carte sur son pupitre)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(path)
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55
    if power:
        nt.links.new(tex.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = power
    return m


WARM = '#ffc98a'
if CLAY or LINE:       # maquette d'architecte : une seule matière, quelques accents
    clay = mat('clay', '#efe6d8', 0.8)
    M = dict(struct=clay, roof=mat('roof', '#e6dccc', 0.75), floor=clay, deck=mat('deck', '#dccbb2', 0.75), wall=clay,
             cloth=mat('cloth', '#f7f1e7', 0.85), under=mat('under', '#5a3d30', 0.85), chair=mat('chair', '#8a6b56', 0.85),
             slate=mat('slate', '#cdbda6', 0.85), base=mat('base', '#d6c7b0', 0.85), sand=mat('sand', '#ece2d2', 0.95),
             bottle=mat('bottle', '#8a6d52', 0.35), label=clay, wood=mat('wood', '#cbb596', 0.75), dark=mat('dark', '#b09a80', 0.75),
             lobster=mat('lobster', '#b4543a', 0.5), rock=mat('rock', '#c2b29b', 0.9), hill=mat('hill', '#e9dfcf', 1.0),
             hill2=mat('hill2', '#eee6d8', 1.0), sign=mat('sign', '#483026', 0.5), brass=mat('brass', '#c9a468', 0.35, 0.9),
             frame=mat('frame', '#483026', 0.5), neighbor=mat('neighbor', '#eee5d7', 0.9), palm=mat('palm', '#d9cbb3', 0.9),
             trunk=mat('trunk', '#cdbca3', 0.9))
    P = dict(glow=1.6, lamp=3.0, aqua=1.5, cellar=0.9, sign=0)
else:
    hill, hill2 = (('#18233a', '#1c2a45'), ('#2b3a5a', '#34476e')) if not WARMSKY else (('#22161a', '#2a1a1c'), ('#3b2526', '#4a2e2c'))
    M = dict(struct=mat('struct', '#efe7da', 0.55), roof=mat('roof', '#aaa39a', 0.55), floor=mat('floor', '#9c8c79', 0.14),
             deck=mat('deck', '#5a3a26', 0.45), wall=mat('wall', '#efe6d8', 0.7), cloth=mat('cloth', '#f4eee3', 0.8),
             under=mat('under', '#4a2f24', 0.8), chair=mat('chair', '#33251e', 0.7), slate=mat('slate', '#3e3630', 0.6),
             base=mat('base', '#211a16', 0.85), sand=mat('sand', '#a8937a', 0.95), bottle=mat('bottle', '#1d140f', 0.15),
             label=mat('label', '#e9dcc5', 0.6), wood=mat('wood', '#6b4630', 0.45), dark=mat('dark', '#1c1512', 0.6),
             lobster=mat('lobster', '#7a2a1a', 0.5), rock=mat('rock', '#1e2a2c', 0.9),
             hill=mat('hill', hill[0], 1.0, emit=hill[1], power=0.55), hill2=mat('hill2', hill2[0], 1.0, emit=hill2[1], power=0.6),
             sign=mat('sign', '#f6e6c6', 0.4, emit='#ffe2ae', power=2.4), brass=mat('brass', '#c9a468', 0.3, 1.0),
             frame=mat('frame', '#1c120d', 0.4), neighbor=mat('neighbor', '#8c8377', 0.9), palm=mat('palm', '#0f1a17', 0.9),
             trunk=mat('trunk', '#17110e', 0.9))
    P = dict(glow=5.0, lamp=12.0, aqua=1.0, cellar=3.2, sign=1.6)
M['glow'] = mat('glow', '#fff1d6', 0.5, emit=WARM, power=P['glow'] * (0.35 if INSIDE and NIGHT else 1))            # gorges lumineuses
M['lamp'] = mat('lamp', '#fff1d6', 0.5, emit=WARM, power=P['lamp'])            # suspensions, bougies
M['cellar'] = mat('cellar', '#ffd9a0', 0.6, emit='#ffb866', power=P['cellar'])  # fond rétro-éclairé de la cave
M['glass'] = mat('glass', '#ffffff', 0.02, trans=1.0)
# paroi lumineuse du vivier : dégradé, clair en surface, profond au fond — les langoustes s'y découpent en silhouette
aq = bpy.data.materials.new('aqua'); aq.use_nodes = True; an = aq.node_tree
em = an.nodes.new('ShaderNodeEmission'); ramp = an.nodes.new('ShaderNodeValToRGB'); tcn = an.nodes.new('ShaderNodeTexCoord'); spn = an.nodes.new('ShaderNodeSeparateXYZ')
an.links.new(tcn.outputs['Generated'], spn.inputs['Vector']); an.links.new(spn.outputs['Z'], ramp.inputs['Fac'])
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, (*lin('#075068'), 1)
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 1.0, (*lin('#5fe0f2'), 1)
e = ramp.color_ramp.elements.new(0.55); e.color = (*lin('#1aa6c8'), 1)
an.links.new(ramp.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = ((1.5 if INSIDE else 4.2) if NIGHT else 1.6) * P['aqua']
an.links.new(em.outputs['Emission'], an.nodes['Material Output'].inputs['Surface'])
M['aqua'] = aq


# ------------------------------------------------------------------ primitives
def link(o):
    col.objects.link(o); return o


def box(name, size, loc, m, rot=(0, 0, 0), bevel=0.012):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    if bevel and min(size) > bevel * 3:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect='EDGES', profile=0.6)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = rot; me.materials.append(m)
    return link(o)


def cyl(name, r, h, loc, m, r2=None, seg=28, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = len(p.vertices) == 4
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = rot; me.materials.append(m)
    return link(o)


def ball(name, scale, loc, m, sub=2, noise=0.0, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1)
    for v in bm.verts:
        k = 1 + (random.random() - 0.5) * noise
        v.co = Vector((v.co.x * scale[0] * k, v.co.y * scale[1] * k, v.co.z * scale[2] * k))
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = noise == 0
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = rot; me.materials.append(m)
    return link(o)


def poly(name, verts, faces, m, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.materials.append(m)
    for p in me.polygons: p.use_smooth = smooth
    return link(bpy.data.objects.new(name, me))


def quad(name, w, h, loc, m, rot=(math.pi / 2, 0, 0)):
    """Rectangle texturé (image entière), face tournée vers -Y par défaut."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[i].uv = c
    me.materials.append(m)
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = rot
    return link(o)


def inst(src, loc, rot=(0, 0, 0)):
    o = bpy.data.objects.new(src.name, src.data); o.location = loc; o.rotation_euler = rot
    return link(o)


def group(name, parts):
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join(); parts[0].name = name
    return parts[0]


def text(body, size, loc, m, font, rot=(math.pi / 2, 0, 0), depth=0.02):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = body; cu.size = size; cu.extrude = depth
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.font = bpy.data.fonts.load(os.path.join(HERE, 'fonts', font + '.ttf'))
    cu.materials.append(m)
    o = bpy.data.objects.new('txt', cu); o.location = loc; o.rotation_euler = rot
    return link(o)


def light(kind, loc, energy, color=WARM, size=1.0, rot=None, toward=None, spot=None):
    d = bpy.data.lights.new('l', kind); d.energy = energy; d.color = lin(color)
    if kind == 'AREA': d.size = size
    elif kind == 'SUN': d.angle = math.radians(size)
    else: d.shadow_soft_size = size
    if spot: d.spot_size = math.radians(spot); d.spot_blend = 0.6
    o = bpy.data.objects.new('l', d); o.location = loc
    if toward is not None: o.rotation_euler = (Vector(toward) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    elif rot: o.rotation_euler = rot
    return link(o)


# ------------------------------------------------------------------ le site : mer, plage, collines, voisins, palmiers
F = 2.4                       # niveau du plancher au-dessus de l'eau
W2, TD, HD = 9.0, 5.0, 14.0   # demi-largeur, profondeur de la terrasse, profondeur totale

sea_col = {'bleue': '#061a2a', 'chocolat': '#1a0f0d', 'ivoire': '#cfe1df', 'trait': '#cfe1df'}[MOOD]
BX, BY0, BY1 = (18.5, -9.5, 17.5) if MODEL else (600.0, -600.0, 60.0)      # emprise du terrain
sea = poly('sea', [(-BX, BY0, 0), (BX, BY0, 0), (BX, BY1, 0), (-BX, BY1, 0)], [(0, 1, 2, 3)], mat('sea', '#9fd6d6' if MODEL else sea_col, 0.07 if NIGHT else (0.12 if MODEL else 0.2)))
nt = sea.data.materials[0].node_tree; b = nt.nodes['Principled BSDF']
noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 0.55; noise.inputs['Detail'].default_value = 3
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.22, 2.4, 1)
tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], noise.inputs['Vector'])
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.45 if NIGHT else 0.08
nt.links.new(noise.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])

bx, by = (BX, BY1) if MODEL else (300.0, 40.0)
poly('beach', [(-bx, -5.5, -0.3), (bx, -5.5, -0.3), (bx, 0, 0.5), (-bx, 0, 0.5), (-bx, by, 1.4), (bx, by, 1.4)], [(0, 1, 2, 3), (3, 2, 5, 4)], M['sand'])
if MODEL:      # socle
    box('socle', (2 * BX, BY1 - BY0, 2.2), (0, (BY0 + BY1) / 2, -1.25), M['wall'], bevel=0.08)
    for sx in (-1, 1):       # chants du terrain, pour que la plage ait une épaisseur
        poly('chant', [(sx * BX, -5.5, -0.3), (sx * BX, 0, 0.5), (sx * BX, BY1, 1.4), (sx * BX, BY1, -0.3)], [(0, 1, 2, 3)], M['sand'])
    poly('chant_fond', [(-BX, BY1, -0.3), (BX, BY1, -0.3), (BX, BY1, 1.4), (-BX, BY1, 1.4)], [(0, 1, 2, 3)], M['sand'])
    catcher = poly('ombre', [(-200, -200, -2.36), (200, -200, -2.36), (200, 200, -2.36), (-200, 200, -2.36)], [(0, 1, 2, 3)], M['wall'])
    catcher.is_shadow_catcher = True
for i, (x, y, sx, sy, sz) in enumerate([] if MODEL else [(-260, 560, 260, 120, 62), (120, 620, 330, 130, 84), (430, 540, 220, 110, 50), (-520, 600, 240, 120, 44)]):
    ball('hill%d' % i, (sx, sy, sz), (x, y, -4), M['hill'], sub=4, noise=0.10)
for i, (x, y, sx, sy, sz) in enumerate([] if MODEL else [(-90, 820, 380, 140, 118), (360, 860, 320, 140, 96)]):
    ball('hillfar%d' % i, (sx, sy, sz), (x, y, -6), M['hill2'], sub=4, noise=0.08)
for i, (x, w, d, h) in enumerate([] if MODEL else [(-25, 9, 10, 4.0), (-37, 11, 9, 5.2), (25, 8, 10, 3.6), (35.5, 10, 11, 4.8), (48, 9, 9, 4.0), (-50, 10, 9, 3.8)]):
    y = 10 + i % 2
    box('nb%d' % i, (w, d, h), (x, y, 1.2 + h / 2), M['neighbor'], bevel=0.03)
    poly('nbroof%d' % i, [(x - w / 2 - .3, y - d / 2 - .3, 1.2 + h), (x + w / 2 + .3, y - d / 2 - .3, 1.2 + h), (x + w / 2 + .3, y + d / 2 + .3, 1.2 + h),
                           (x - w / 2 - .3, y + d / 2 + .3, 1.2 + h), (x, y, 1.2 + h + 1.4)], [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], M['roof'])
    if NIGHT and i in (0, 3):
        box('nbwin', (0.7, 0.05, 0.9), (x - w / 4, y - d / 2 - 0.03, 1.2 + h * 0.55), M['cellar'], bevel=0)


def palm(x, y, height, lean=0.0, n=9):
    """Palmier stylisé : tronc légèrement incliné, palmes en arc."""
    segs = 10
    for k in range(segs):
        t0, t1 = k / segs, (k + 1) / segs
        p0 = Vector((x + lean * t0 * t0 * height * 0.25, y, 0.6 + t0 * height)); p1 = Vector((x + lean * t1 * t1 * height * 0.25, y, 0.6 + t1 * height))
        c = cyl('tronc', 0.15 - 0.06 * t0, (p1 - p0).length * 1.05, (p0 + p1) / 2, M['trunk'], r2=0.15 - 0.06 * t1, seg=10)
        c.rotation_euler = (p1 - p0).to_track_quat('Z', 'Y').to_euler()
    top = Vector((x + lean * height * 0.25, y, 0.6 + height))
    for k in range(n):
        ang = k * 2 * math.pi / n + random.random() * 0.4; L = 3.1 + random.random() * 1.3; droop = 1.5 + random.random() * 1.4
        vs, fs, steps = [], [], 9
        dirx, diry = math.cos(ang), math.sin(ang)
        for j in range(steps + 1):
            t = j / steps; w = 0.26 * math.sin(math.pi * min(1.0, 0.12 + t * 0.95)) + 0.015
            c = top + Vector((dirx * L * t, diry * L * t, 0.75 * math.sin(math.pi * t * 0.55) - droop * t * t))
            side = Vector((-diry, dirx, 0)) * w
            vs += [tuple(c - side + Vector((0, 0, -0.10 * w * 4))), tuple(c + Vector((0, 0, 0.05))), tuple(c + side + Vector((0, 0, -0.10 * w * 4)))]
        for j in range(steps):
            a = j * 3; fs += [(a, a + 1, a + 4, a + 3), (a + 1, a + 2, a + 5, a + 4)]
        poly('palme', vs, fs, M['palm'], smooth=True)


if not INSIDE:
    if MODEL:
        palm(-14.0, 7.5, 8.6, lean=-0.4, n=13); palm(-16.8, 11.5, 6.8, lean=0.3, n=11); palm(14.6, 9.0, 8.0, lean=0.5, n=13)
    else:
        palm(-14.5, 6.5, 9.6, lean=-0.5, n=13); palm(-17.8, 9.5, 7.6, lean=0.35, n=11); palm(15.4, 7.5, 8.9, lean=0.6, n=13); palm(20.2, 11, 7.0, lean=-0.3, n=11)

# ------------------------------------------------------------------ le pavillon
box('rock_base', (2 * W2 - 1.5, HD - 4.2, F - 0.5), (0, 4.4 + (HD - 4.2) / 2, (F - 0.5) / 2 + 0.3), M['base'], bevel=0.06)
for i in range(7):
    x = -W2 + 0.2 + i * (2 * W2 - 0.4) / 6
    box('pilotis', (0.2, 0.2, F - 0.2), (x, 0.3, (F - 0.2) / 2 + 0.2), M['dark'])
    L = math.hypot(3.6, F - 0.7)
    box('strut', (0.14, L, 0.14), (x, 0.3 + 1.8, 0.45 + (F - 0.7) / 2), M['dark'], rot=(math.atan2(F - 0.7, -3.6) + math.pi, 0, 0))
for k in range(9):
    ball('rock', (0.9 + random.random(), 0.8 + random.random() * .6, 0.5 + random.random() * .4),
         (-W2 + 1 + k * 2.1 + random.random(), 2.6 + random.random() * 1.2, 0.5), M['base'], sub=2, noise=0.35)

box('deck', (2 * W2 + 0.4, TD + 0.3, 0.22), (0, TD / 2 - 0.05, F - 0.11), M['deck'], bevel=0.02)
box('floor', (2 * W2 + 0.4, HD - TD, 0.22), (0, TD + (HD - TD) / 2, F - 0.11), M['floor'], bevel=0.02)
for i in range(int((2 * W2) / 0.24)):
    box('lame', (0.012, TD + 0.3, 0.004), (-W2 + 0.12 + i * 0.24, TD / 2 - 0.05, F + 0.002), M['dark'], bevel=0)

PH = 2.75
for i in range(7):
    x = -W2 + 0.15 + i * (2 * W2 - 0.3) / 6
    box('post', (0.15, 0.15, PH), (x, 0.12, F + PH / 2), M['struct'])
    for s in (-1, 1):
        if (i == 0 and s < 0) or (i == 6 and s > 0): continue
        box('brace', (0.09, 0.09, 1.15), (x + s * 0.4, 0.12, F + PH - 0.4), M['struct'], rot=(0, -s * math.radians(45), 0))
    if i in (0, 6):
        for y in (TD / 2, TD - 0.1):
            box('post', (0.15, 0.15, PH), (x, y, F + PH / 2), M['struct'])
box('fascia', (2 * W2 + 0.5, 0.2, 0.42), (0, 0.12, F + PH + 0.21), M['struct'], bevel=0.02)
box('enseigne', (6.6, 0.08, 0.8), (0, 0.0, F + PH + 0.39), M['frame'] if NIGHT else M['struct'], bevel=0.02)     # de nuit : plaque sombre, lettres lumineuses
for s in (-1, 1):
    box('fascia_side', (0.2, TD, 0.42), (s * (W2 + 0.02), TD / 2, F + PH + 0.21), M['struct'], bevel=0.02)
for i in range(31):
    x = -W2 + 0.3 + i * (2 * W2 - 0.6) / 30
    L = math.hypot(TD + 0.5, 0.95)
    box('chevron', (0.06, L, 0.11), (x, TD / 2 - 0.1, F + PH + 0.68), M['struct'], rot=(math.atan2(0.95, TD + 0.5), 0, 0), bevel=0)
for i in range(6):
    x0 = -W2 + 0.15 + i * (2 * W2 - 0.3) / 6; x1 = x0 + (2 * W2 - 0.3) / 6
    box('verre', (x1 - x0 - 0.2, 0.02, 1.0), ((x0 + x1) / 2, 0.12, F + 0.55), M['glass'], bevel=0)
box('lisse', (2 * W2, 0.05, 0.05), (0, 0.12, F + 1.08), M['struct'], bevel=0)

HC = 3.3
for s in (-1, 1):
    box('pignon', (0.22, HD - TD, HC + 0.4), (s * W2, TD + (HD - TD) / 2, F + (HC + 0.4) / 2), M['wall'], bevel=0.02)
box('fond_haut', (2 * W2, 0.22, 0.75), (0, HD, F + HC - 0.1), M['wall'], bevel=0)
box('plafond', (2 * W2, HD - TD + 0.2, 0.16), (0, TD + (HD - TD) / 2, F + HC + 0.25), M['wall'], bevel=0)
for x in (-3.0, 3.0):
    box('colonne', (0.3, 0.3, HC + 0.2), (x, TD + 0.1, F + (HC + 0.2) / 2), M['struct'])
box('linteau', (2 * W2, 0.3, 0.5), (0, TD + 0.1, F + HC + 0.0), M['struct'], bevel=0.02)
for (sx, sy, x, y) in [(2 * W2 - 1.2, 0.07, 0, TD + 0.9), (2 * W2 - 1.2, 0.07, 0, HD - 0.9), (0.07, HD - TD - 1.8, -W2 + 0.6, TD + (HD - TD) / 2), (0.07, HD - TD - 1.8, W2 - 0.6, TD + (HD - TD) / 2)]:
    box('gorge', (sx, sy, 0.04), (x, y, F + HC + 0.14), M['glow'], bevel=0)

ZR0, ZR1, ov = F + PH + 0.42, F + HC + 0.8, 0.75
poly('toit_bas', [(-W2 - ov, -ov, ZR0), (W2 + ov, -ov, ZR0), (W2 + ov, HD + ov, ZR0), (-W2 - ov, HD + ov, ZR0),
                  (-W2 + 2.2, TD - 0.6, ZR1), (W2 - 2.2, TD - 0.6, ZR1), (W2 - 2.2, HD - 2.4, ZR1), (-W2 + 2.2, HD - 2.4, ZR1)],
     [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (0, 3, 2, 1)], M['roof'])
ZT = ZR1 + 2.3
poly('toit_haut', [(-W2 + 1.6, TD - 1.2, ZR1 + 0.25), (W2 - 1.6, TD - 1.2, ZR1 + 0.25), (W2 - 1.6, HD - 1.8, ZR1 + 0.25), (-W2 + 1.6, HD - 1.8, ZR1 + 0.25),
                   (-W2 + 5.4, (TD + HD) / 2 - 1.5, ZT), (W2 - 5.4, (TD + HD) / 2 - 1.5, ZT)],
     [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4), (0, 3, 2, 1)], M['roof'])
box('acrotere', (2 * W2 - 3.2, HD - TD - 0.6, 0.3), (0, (TD + HD) / 2 - 1.5, ZR1 + 0.12), M['struct'], bevel=0.02)
text('O C E A N   8 2', 0.5, (0, -0.045, F + PH + 0.39), M['sign'] if NIGHT else M['frame'], 'jost', depth=0.012)

# ------------------------------------------------------------------ mobilier
def make_table(round_=False):
    parts = []
    if round_:
        parts.append(cyl('t', 0.62, 0.74, (0, 0, 0.37), M['under'], seg=40))
        parts.append(cyl('t', 0.5, 0.03, (0, 0, 0.755), M['cloth'], seg=40))
    else:
        parts.append(box('t', (0.88, 0.88, 0.74), (0, 0, 0.37), M['under'], bevel=0.02))
        parts.append(box('t', (0.9, 0.9, 0.03), (0, 0, 0.755), M['cloth'], rot=(0, 0, math.radians(45)), bevel=0.004))
    parts.append(cyl('t', 0.035, 0.09, (0, 0, 0.815), M['glass'], seg=14))
    parts.append(cyl('t', 0.02, 0.05, (0, 0, 0.80), M['lamp'], seg=10))
    for a in range(4):
        ang = a * math.pi / 2 + math.pi / 4
        parts.append(cyl('t', 0.10, 0.006, (0.26 * math.cos(ang), 0.26 * math.sin(ang), 0.774), M['cloth'], seg=20))
        parts.append(cyl('t', 0.028, 0.14, (0.2 * math.cos(ang + .5), 0.2 * math.sin(ang + .5), 0.84), M['glass'], r2=0.04, seg=12))
    return group('table_r' if round_ else 'table', parts)


def make_chair():
    parts = [box('c', (0.46, 0.46, 0.05), (0, 0, 0.45), M['chair'], bevel=0.012),
             box('c', (0.46, 0.05, 0.42), (0, 0.22, 0.7), M['chair'], rot=(math.radians(-7), 0, 0), bevel=0.012)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box('c', (0.04, 0.04, 0.45), (sx * 0.2, sy * 0.2, 0.225), M['chair'], bevel=0))
        parts.append(box('c', (0.04, 0.44, 0.03), (sx * 0.23, 0.0, 0.62), M['chair'], bevel=0))
    return group('chair', parts)


def make_stool():
    parts = [cyl('s', 0.17, 0.05, (0, 0, 0.76), M['wood'], seg=24)]
    for a in range(4):
        ang = a * math.pi / 2 + math.pi / 4
        parts.append(box('s', (0.025, 0.025, 0.76), (0.13 * math.cos(ang), 0.13 * math.sin(ang), 0.38), M['dark'], bevel=0))
    parts.append(cyl('s', 0.16, 0.015, (0, 0, 0.28), M['dark'], seg=24))
    return group('stool', parts)


T, TR, CH, ST = make_table(), make_table(True), make_chair(), make_stool()
for o in (T, TR, CH, ST): o.location = (0, 0, -80)


def place(x, y, round_=False, seats=4, rot=0.0):
    inst(TR if round_ else T, (x, y, F), (0, 0, rot))
    r = 0.78 if round_ else 0.74
    for k in range(seats):
        a = rot + k * (2 * math.pi / seats)
        inst(CH, (x + r * math.sin(a), y - r * math.cos(a), F), (0, 0, a + math.pi))


for i in range(6):
    place(-7.3 + i * 2.92, 1.25, seats=2 if i % 2 else 4)
    place(-7.3 + i * 2.92 + 0.5, 3.55, seats=4)
for i in range(4):
    if not (VIEW == 'vivier' and i >= 2):          # vue intérieure : on dégage le premier plan devant le vivier
        place(-4.6 + i * 3.1, 7.3, round_=(i % 2 == 0), seats=4)
    if not (INSIDE and i >= 2):
        place(-4.6 + i * 3.1 + 0.4, 9.9, round_=(i % 2 == 1), seats=4)

box('bar', (0.7, 4.6, 1.08), (-W2 + 1.5, 8.6, F + 0.54), M['wall'], bevel=0.02)
box('bar_top', (0.86, 4.8, 0.06), (-W2 + 1.5, 8.6, F + 1.11), M['wood'], bevel=0.01)
for k in range(5):
    inst(ST, (-W2 + 2.25, 6.9 + k * 0.85, F))
box('bar_fond', (0.3, 4.6, 1.5), (-W2 + 0.3, 8.6, F + 1.75), M['cellar'], bevel=0)
for k in range(3):
    box('etag', (0.34, 4.6, 0.04), (-W2 + 0.32, 8.6, F + 1.2 + k * 0.5), M['wood'], bevel=0)
    cyl('suspension', 0.13, 0.26, (-W2 + 1.5, 7.1 + k * 1.5, F + 2.25), M['lamp'], r2=0.09, seg=20)
    cyl('fil', 0.005, 0.9, (-W2 + 1.5, 7.1 + k * 1.5, F + 2.83), M['dark'], seg=6)
cyl('vertigo', 1.25, 0.02, (0.4, 8.7, F + 2.55), M['struct'], r2=1.1, seg=48)
cyl('vertigo_c', 0.16, 0.2, (0.4, 8.7, F + 2.45), M['lamp'], r2=0.1, seg=24)
cyl('vertigo_f', 0.006, 0.7, (0.4, 8.7, F + 2.92), M['dark'], seg=6)

# ------------------------------------------------------------------ mur du fond : la cave vitrée, l'entrée, le vivier
YB = HD - 0.12
CX0, CX1, CZ0, CZ1 = -8.3, -1.9, 0.75, 2.75
box('cave_fond', (CX1 - CX0, 0.05, CZ1 - CZ0), ((CX0 + CX1) / 2, YB + 0.42, F + (CZ0 + CZ1) / 2), M['cellar'], bevel=0)
box('cave_allege', (CX1 - CX0 + 0.3, 0.6, CZ0), ((CX0 + CX1) / 2, YB + 0.18, F + CZ0 / 2), M['wall'], bevel=0.02)
for z in (CZ0, CZ1):
    box('cave_cadre', (CX1 - CX0 + 0.3, 0.62, 0.1), ((CX0 + CX1) / 2, YB + 0.18, F + z), M['struct'], bevel=0.01)
for x in (CX0 - 0.1, CX1 + 0.1):
    box('cave_cadre', (0.1, 0.62, CZ1 - CZ0 + 0.1), (x, YB + 0.18, F + (CZ0 + CZ1) / 2), M['struct'], bevel=0.01)
bottle = group('bottle', [cyl('b', 0.037, 0.21, (0, 0, 0.105), M['bottle'], seg=14), cyl('b', 0.014, 0.1, (0, 0, 0.255), M['bottle'], r2=0.012, seg=10),
                          cyl('b', 0.0385, 0.07, (0, 0, 0.1), M['label'], seg=14)])
bottle.location = (0, 0, -80)
rows = 5
for r in range(rows):
    z = F + CZ0 + 0.06 + r * (CZ1 - CZ0 - 0.1) / rows
    box('tablette', (CX1 - CX0, 0.3, 0.03), ((CX0 + CX1) / 2, YB + 0.24, z), M['wood'], bevel=0)
    x = CX0 + 0.12
    while x < CX1 - 0.1:
        if random.random() > 0.07:
            inst(bottle, (x, YB + 0.22 + random.random() * 0.03, z + 0.015))
        x += 0.098
for k in range(1, 8):
    box('montant', (0.03, 0.3, CZ1 - CZ0), (CX0 + k * (CX1 - CX0) / 8, YB + 0.24, F + (CZ0 + CZ1) / 2), M['wood'], bevel=0)
box('cave_vitre', (CX1 - CX0, 0.012, CZ1 - CZ0), ((CX0 + CX1) / 2, YB - 0.1, F + (CZ0 + CZ1) / 2), M['glass'], bevel=0)
box('comptoir', (CX1 - CX0 - 1.2, 0.5, 1.04), ((CX0 + CX1) / 2, YB - 1.0, F + 0.52), M['wall'], bevel=0.02)
box('comptoir_top', (CX1 - CX0 - 1.0, 0.62, 0.05), ((CX0 + CX1) / 2, YB - 1.0, F + 1.065), M['wood'], bevel=0.01)
for k in range(6):
    inst(ST, (CX0 + 1.2 + k * 0.82, YB - 1.55, F))

# l'entrée, et la carte sur son pupitre de laiton
box('porte', (2.0, 0.1, 2.5), (0, YB + 0.3, F + 1.25), M['dark'], bevel=0)
box('porte_cadre', (2.3, 0.4, 0.12), (0, YB + 0.1, F + 2.56), M['struct'], bevel=0.01)
for s in (-1, 1):
    box('porte_cadre', (0.12, 0.4, 2.6), (s * 1.1, YB + 0.1, F + 1.3), M['struct'], bevel=0.01)
PX, PY = 2.05, YB - 1.75
cyl('pupitre_pied', 0.022, 1.12, (PX, PY, F + 0.56), M['brass'], seg=16)
cyl('pupitre_base', 0.2, 0.025, (PX, PY, F + 0.012), M['brass'], seg=40)
tilt = math.radians(72)
box('pupitre_plateau', (0.5, 0.66, 0.018), (PX, PY - 0.02, F + 1.22), M['brass'], rot=(tilt, 0, 0), bevel=0.004)
quad('carte', 0.44, 0.593, (PX, PY - 0.031, F + 1.223), photo('carte', os.path.join(HERE, 'tex', 'carte.png'), 0.18 if NIGHT else 0), rot=(tilt, 0, 0))

# le vivier, devant un mur d'ardoise
VX0, VX1 = 2.3, 8.2
box('ardoise', (VX1 - VX0 + 0.5, 0.08, HC - 0.2), ((VX0 + VX1) / 2, YB + 0.02, F + (HC - 0.2) / 2), M['slate'], bevel=0)
for k in range(1, 6):
    box('joint', (0.012, 0.01, HC - 0.2), (VX0 - 0.25 + k * (VX1 - VX0 + 0.5) / 6, YB - 0.03, F + (HC - 0.2) / 2), M['dark'], bevel=0)
for k in range(1, 4):
    box('joint', (VX1 - VX0 + 0.5, 0.01, 0.012), ((VX0 + VX1) / 2, YB - 0.03, F + k * (HC - 0.2) / 4), M['dark'], bevel=0)
VL, VD, VB, VH = VX1 - VX0 - 0.7, 0.95, 0.95, 0.82
vx, vy = (VX0 + VX1) / 2, YB - 0.1 - VD / 2
box('vivier_socle', (VL + 0.12, VD + 0.1, VB), (vx, vy, F + VB / 2), M['wall'], bevel=0.02)
for k in range(4):
    box('panneau', (VL / 4 - 0.22, 0.02, VB - 0.3), (vx - VL / 2 + (k + 0.5) * VL / 4, vy - VD / 2 - 0.05, F + VB / 2), M['struct'], bevel=0.01)
box('vivier_fond', (VL - 0.04, 0.02, VH - 0.06), (vx, vy + VD / 2 - 0.04, F + VB + VH / 2), M['aqua'], bevel=0)       # paroi lumineuse
box('vivier_sable', (VL - 0.04, VD - 0.06, 0.04), (vx, vy, F + VB + 0.03), mat('vsable', '#bfe9ee' if NIGHT else '#dfeeee', 0.9), bevel=0)
box('vivier_verre', (VL, 0.012, VH), (vx, vy - VD / 2, F + VB + VH / 2), M['glass'], bevel=0)
box('vivier_capot', (VL + 0.1, VD + 0.08, 0.1), (vx, vy, F + VB + VH + 0.05), M['wall'], bevel=0.02)
for k in range(3):
    ball('v_roche', (0.3 + random.random() * .15, 0.16, 0.16 + random.random() * .1), (vx - VL / 2 + 0.9 + k * 1.75, vy + 0.16, F + VB + 0.14), M['rock'], sub=2, noise=0.45)


def lobster(x, y, z, a=0.0, s=1.0):
    """Langouste stylisée : pas de pinces, de longues antennes — reconnaissable en silhouette."""
    parts = [ball('l', (0.19 * s, 0.062 * s, 0.07 * s), (0, 0, 0), M['lobster'], sub=2)]
    for j in range(4):
        parts.append(ball('l', ((0.085 - j * 0.007) * s, (0.058 - j * 0.007) * s, (0.056 - j * 0.007) * s), ((-0.17 - j * 0.062) * s, 0, (-0.006 - j * 0.012) * s), M['lobster'], sub=2))
    parts.append(ball('l', (0.075 * s, 0.1 * s, 0.012 * s), (-0.46 * s, 0, -0.058 * s), M['lobster'], sub=2))
    for sd in (-1, 1):
        parts.append(cyl('l', 0.011 * s, 0.86 * s, (0.48 * s, sd * 0.07 * s, 0.2 * s), M['lobster'], r2=0.002 * s, seg=6, rot=(sd * math.radians(-9), math.radians(64), 0)))
        for j in range(4):
            parts.append(cyl('l', 0.009 * s, 0.2 * s, ((0.1 - j * 0.07) * s, sd * 0.09 * s, -0.08 * s), M['lobster'], seg=6, rot=(sd * math.radians(38), math.radians(14 * (j - 1.5)), 0)))
    g = group('langouste', parts); g.location = (x, y, z); g.rotation_euler = (0, 0, a)
    return g


for k, (dx, dz, a, s) in enumerate([(0.75, 0.13, 0.15, 1.15), (1.95, 0.13, math.pi - 0.2, 1.0), (2.85, 0.3, 0.3, 1.1), (4.15, 0.13, -0.1, 1.2)]):
    lobster(vx - VL / 2 + dx, vy - 0.12 + (k % 2) * 0.12, F + VB + 0.06 + dz, a, s)

# deux tirages encadrés sur l'ardoise (les vraies photos du restaurant)
if INSIDE:
    for (x, w, h, img) in [(vx - 1.3, 1.0, 0.75, os.path.join(HERE, 'tex', 'langouste.jpg')), (vx + 1.2, 0.72, 0.72, os.path.join(HERE, 'tex', 'sphere.jpg'))]:
        box('cadre', (w + 0.07, 0.03, h + 0.07), (x, YB - 0.05, F + 2.45), M['frame'], bevel=0.004)
        quad('tirage', w, h, (x, YB - 0.068, F + 2.45), photo('tirage', img, 0.05 if NIGHT else 0))
        if NIGHT: light('SPOT', (x, YB - 0.9, F + 3.2), 26, '#ffe3b8', 0.05, toward=(x, YB, F + 2.4), spot=50)

# ------------------------------------------------------------------ ciel
world = bpy.data.worlds.new('ciel'); scene.world = world; world.use_nodes = True
wn = world.node_tree; bg = wn.nodes['Background']
tcw = wn.nodes.new('ShaderNodeTexCoord'); sep = wn.nodes.new('ShaderNodeSeparateXYZ'); wr = wn.nodes.new('ShaderNodeValToRGB')
mr = wn.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.12; mr.inputs['From Max'].default_value = 0.75
wn.links.new(tcw.outputs['Generated'], sep.inputs['Vector']); wn.links.new(sep.outputs['Z'], mr.inputs['Value'])
wn.links.new(mr.outputs['Result'], wr.inputs['Fac']); wn.links.new(wr.outputs['Color'], bg.inputs['Color'])
SKY = {
    'bleue':    ([(0.0, '#0a1220'), (0.135, '#3a3550'), (0.165, '#c58a6e'), (0.21, '#6d5c78'), (0.34, '#263759'), (0.6, '#13203a'), (1.0, '#0a1222')], 1.15),
    'chocolat': ([(0.0, '#120a08'), (0.135, '#3a2019'), (0.165, '#d08a4e'), (0.2, '#8a4a34'), (0.32, '#3d2420'), (0.6, '#1f1412'), (1.0, '#130c0b')], 1.0),
    'ivoire':   ([(0.0, '#efe6d8'), (0.15, '#fbf6ee'), (0.4, '#fbf7f0'), (1.0, '#f4ecdf')], 0.5),
    'trait':    ([(0.0, '#241812'), (1.0, '#241812')], 1.0),
}[MOOD]
cr = wr.color_ramp
cr.elements[0].position, cr.elements[0].color = SKY[0][0][0], (*lin(SKY[0][0][1]), 1)
cr.elements[1].position, cr.elements[1].color = SKY[0][1][0], (*lin(SKY[0][1][1]), 1)
for pos, hx in SKY[0][2:]:
    e = cr.elements.new(pos); e.color = (*lin(hx), 1)
bg.inputs['Strength'].default_value = SKY[1]

# ------------------------------------------------------------------ lumière
if NIGHT:
    cool = '#9db7ff' if not WARMSKY else '#ffb38a'
    light('SUN', (0, 0, 60), 0.16 if not WARMSKY else 0.2, cool, 14, toward=(22, 36, 0))                 # ciel : modelé doux des volumes
    light('AREA', (0, TD / 2, F + PH + 0.3), 300, WARM, 9)                                                 # terrasse
    light('AREA', (0, 9.5, F + HC), 430 if not INSIDE else 34, WARM, 10)                                   # salle
    light('AREA', (vx, vy - 1.3, F + 2.9), 90 if not INSIDE else 22, '#8fe9f6', 4, toward=(vx, vy - 2.2, F))   # halo du vivier au sol
    light('AREA', ((CX0 + CX1) / 2, YB - 1.4, F + 2.6), 130, '#ffbf7a', 4, toward=((CX0 + CX1) / 2, YB - 2.4, F))
    light('AREA', (vx, YB - 0.5, F + HC), 140 if not INSIDE else 26, '#ffe0b3', 5.5, toward=(vx, YB, F + 1.6))  # lèche-mur sur l'ardoise
    if INSIDE: light('SPOT', (PX - 0.3, PY - 1.3, F + 3.1), 230, '#ffe3b8', 0.05, toward=(PX, PY, F + 1.2), spot=30)   # la carte
else:
    light('SUN', (0, 0, 60), 4.6, '#fff1de', 4, toward=((30, 34, -38) if MODEL else (46, 22, -30)))        # soleil latéral, ombres longues et douces
    light('AREA', (0, 9.5, F + HC), 420, '#fff3e0', 10)
    light('AREA', (0, TD / 2, F + PH + 0.3), 220, '#fff3e0', 9)

# ------------------------------------------------------------------ caméra
VIEWS = {
    'face':   dict(pos=(0, -31, 3.4), look=(0, 5, 6.9), lens=35),
    'ext':    dict(pos=(-15.5, -25, 4.6), look=(0.6, 5.5, 4.5), lens=36),
    'tall':   dict(pos=(0, -43, 3.3), look=(0, 5, 7.6), lens=24),
    'maquette': dict(pos=(-25, -44, 16.5), look=(0.4, 3.6, 1.9), lens=39),
    'vivier': dict(pos=(3.7, 8.0, F + 1.22), look=(4.5, YB - 0.4, F + 1.42), lens=25),
    'carte':  dict(pos=(1.0, 10.3, F + 1.36), look=(2.2, 12.3, F + 1.24), lens=44),
}
v = VIEWS[VIEW]
cam = bpy.data.cameras.new('cam'); cam.lens = v['lens']; cam.sensor_width = 36
co = link(bpy.data.objects.new('cam', cam)); co.location = v['pos']
co.rotation_euler = (Vector(v['look']) - Vector(v['pos'])).to_track_quat('-Z', 'Y').to_euler()
if VIEW == 'tall': cam.sensor_fit = 'VERTICAL'
if INSIDE:
    cam.dof.use_dof = True; cam.dof.focus_distance = (Vector((PX, PY, F + 1.22)) - Vector(v['pos'])).length if VIEW == 'carte' else (Vector(v['look']) - Vector(v['pos'])).length * 0.92; cam.dof.aperture_fstop = 2.4 if VIEW == 'carte' else 8
scene.camera = co

# ------------------------------------------------------------------ rendu
scene.render.engine = 'CYCLES'
cy = scene.cycles
cy.device = 'CPU'; cy.samples = SAMPLES; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.glossy_bounces = 4; cy.transmission_bounces = 6; cy.caustics_reflective = False; cy.caustics_refractive = False
cy.sample_clamp_indirect = 6
scene.render.threads_mode = 'FIXED'; scene.render.threads = 4
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = RW, RH, 100
scene.view_settings.view_transform = 'AgX'
try: scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
scene.view_settings.exposure = {'bleue': 0.75, 'chocolat': 0.75, 'ivoire': 0.1, 'trait': 0}[MOOD] + (0.35 if INSIDE and NIGHT else 0)
scene.render.image_settings.file_format = 'PNG'; scene.render.filepath = OUT
if MODEL:
    scene.render.film_transparent = True; scene.render.image_settings.color_mode = 'RGBA'
if LINE:      # dessin d'architecte : aplat sombre, seuls les traits ressortent
    flat = bpy.data.materials.new('aplat'); flat.use_nodes = True; fn = flat.node_tree
    fe = fn.nodes.new('ShaderNodeEmission'); fe.inputs['Color'].default_value = (*lin('#241812'), 1)
    fn.links.new(fe.outputs['Emission'], fn.nodes['Material Output'].inputs['Surface'])
    for o in col.objects:
        if o.type in ('MESH', 'FONT'):
            for i in range(len(o.data.materials)): o.data.materials[i] = flat
    scene.render.use_freestyle = True; scene.render.line_thickness = 1.15
    vl = bpy.context.view_layer; vl.use_freestyle = True
    ls = vl.freestyle_settings.linesets.new('traits')
    ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True; ls.select_external_contour = True
    ls.linestyle.color = lin('#eecd9b'); ls.linestyle.thickness = 1.15
    vl.freestyle_settings.crease_angle = math.radians(140)
    scene.view_settings.view_transform = 'Standard'; cy.samples = 8
bpy.ops.render.render(write_still=True)
print('rendu :', OUT)
