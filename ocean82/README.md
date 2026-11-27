# Ocean 82 — maquettes de refonte

Trois propositions de design pour le site d'Ocean 82 (restaurant français, Grand Case, Saint-Martin), construites à partir
des contenus de <https://ocean82.fr> : mêmes textes, même carte 2027, mêmes photos — recadrées et allégées.

| Dossier | Proposition |
| --- | --- |
| `index.html` | Page de présentation : les trois maquettes, comparatif avant/après, poids mesurés |
| `immersion/` | 1 · **Immersion** — sombre, cinématographique : on entre dans le restaurant en faisant défiler la page |
| `maison/` | 2 · **La Maison** — claire, éditoriale, aux couleurs de la marque |
| `lagon/` | 3 · **Lagon** — colorée, moderne : du lagon au coucher du soleil |

## Nouveau cap : pistes « luxe épuré » avec décor 3D (`pistes/`)

Les trois premières propositions n'ont pas été retenues. Le cap suivant — luxe épuré, restaurant modélisé en 3D stylisé,
la carte et le vivier au premier plan, dans l'esprit du site du Rainbow Café — est exploré dans `pistes/` :

| Fichier | Piste |
| --- | --- |
| `pistes/index.html` | Présentation des trois pistes (écran d'accueil + écran suivant + téléphone) |
| `pistes/a-heure-bleue.html` | A · **Heure bleue** — nocturne, plein écran, Bodoni Moda |
| `pistes/b-maquette.html` | B · **Maquette** — ivoire, maquette d'architecte annotée, Cormorant Garamond |
| `pistes/c-chocolat.html` | C · **Chocolat** — couleurs du logo, la carte dès l'accueil, capitales Jost |

Ce sont des écrans d'accueil, pas des sites complets. Les images 3D (`assets/3d/`) sortent d'un modèle Blender décrit par
un script, sans interface : `src/3d/scene.py` (voir l'en-tête du fichier pour les ambiances et les vues disponibles).

```bash
pip install bpy            # Blender en module Python (≈ 430 Mo)
python src/3d/scene.py bleue face sortie.png 2000 1250 64
```

## Voir les maquettes

Ce sont des pages statiques, sans serveur d'application ni dépendance :

```bash
cd ocean82 && python3 -m http.server 8000
```

puis ouvrir <http://localhost:8000/>. (Un simple double-clic sur les fichiers ne suffit pas : les modules JavaScript et la
visite 360° demandent un serveur web.)

### Sans serveur : une maquette = un fichier

```bash
python3 src/build.py --solo sortie/
```

écrit `ocean82-1-immersion.html`, `ocean82-2-maison.html` et `ocean82-3-lagon.html` : images, polices, scripts et panoramas
sont intégrés dans chaque fichier (2 à 3 Mo). Ils s'ouvrent d'un double-clic et se partagent en pièce jointe.

## Modifier

Les pages sont assemblées à partir de `src/` par un petit script Python sans dépendance :

```bash
python3 src/build.py            # reconstruit les quatre pages
python3 src/build.py lagon      # … ou une seule
```

- `src/content.py` — la carte (français / anglais), les digestifs, les coordonnées : une seule source pour les trois maquettes.
- `src/<page>/page.html`, `style.css`, `app.js` — gabarit, styles (intégrés dans la page à la construction) et script de chaque maquette.
- `src/partials/` — icônes et formulaire de réservation partagés.
- `assets/js/pano.js` — la visionneuse 360° (WebGL, aucune bibliothèque) ; `assets/js/site.js` — bascule FR/EN, réservation.
- `assets/img/`, `assets/pano/` — photos déclinées en AVIF/WebP ; `assets/img/manifest.json` indique pour chaque image
  la photo d'origine sur ocean82.fr et le cadrage appliqué.

## Photos

Toutes les images proviennent du site actuel. `src/images.py` les recadre autour d'un point d'intérêt, redresse des vues
« à plat » à partir des quatre panoramas 360°, et exporte chaque déclinaison en plusieurs largeurs. Les panoramas publiés sur
le site ne font que 1 920 px de large : ils ont été agrandis (Real-ESRGAN) avant redimensionnement. Avec les fichiers d'origine
du photographe, il suffit de relancer le script pour obtenir une visite plus fine.

## Limites d'une maquette

- Le formulaire de réservation n'envoie rien à un serveur : il prépare un message WhatsApp ou un courriel.
- Les pictogrammes d'allergènes de la carte papier ne sont pas reproduits.
- Les pages portent `noindex` pour ne pas concurrencer le site en ligne.
