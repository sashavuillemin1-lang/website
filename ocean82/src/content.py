"""Contenu partagé par les trois maquettes — repris du site ocean82.fr (textes) et de la carte 2027 (PDF scanné).

Chaque plat : (nom français, traduction anglaise, prix en €, [options]).
Les fautes de frappe évidentes de la version anglaise ont été corrigées (« lentels », « proscuito », « Deserts »…).
Les pictogrammes d'allergènes de la carte ne sont volontairement pas reproduits : ils doivent venir d'une source vérifiée.
"""

INFO = {
    'name': 'Ocean 82',
    'address': '82 Boulevard de Grand Case, 97150 Saint-Martin FWI',
    'maps': 'https://www.google.com/maps/search/?api=1&query=Ocean+82+Grand+Case+Saint-Martin',
    'phone': '+590 590 52 98 12', 'phone_href': 'tel:+590590529812',
    'whatsapp': '+590 690 77 77 57', 'whatsapp_href': 'https://wa.me/590690777757',
    'email': 'ocean.82@hotmail.fr',
    'facebook': 'https://www.facebook.com/Ocean82-443496175739516/',
    'instagram': 'https://www.instagram.com/ocean82sxm',
    'tripadvisor': 'https://www.tripadvisor.com/Restaurant_Review-g147351-d3774253-Reviews-Ocean_82-Grand_Case_Saint_Martin_St_Martin_St_Maarten.html',
}

MENU = [
    {'id': 'froids', 'fr': 'Les hors-d’œuvre froids', 'en': 'Cold appetizers', 'items': [
        ('Trilogie de tartare de mahi-mahi, façon péruvienne, tahitienne et créole', 'Mahi-mahi tartare trilogy: Peruvian, Tahitian and Creole style', '22'),
        ('La salade fraîcheur façon Ocean 82', 'Crisp mixed salad with a light vinaigrette', '12'),
        ('La classique salade César', 'The classic Caesar salad', '12',
            [('au poulet', 'with chicken', '16'), ('aux crevettes', 'with shrimp', '20')]),
        ('Les rouleaux de printemps au thon rouge et aux pommes, sauce impériale', 'Tuna spring roll with fresh apples and imperial sauce', '19'),
        ('Le célèbre « foie gras » maison farci aux figues confites', 'The famous homemade duck liver pâté stuffed with fig preserve', '25'),
    ]},
    {'id': 'chauds', 'fr': 'Les hors-d’œuvre chauds', 'en': 'Hot appetizers', 'items': [
        ('Cuisses de grenouille à la persillade', 'Frog legs with garlic and parsley', '19'),
        ('Raviole de langouste et champignons maison, crème de basilic et poivre de Madagascar', 'Homemade lobster and mushroom raviole, basil and Madagascar peppercorn sauce', '22'),
        ('Traditionnels escargots gratinés au beurre d’ail', 'Traditional “escargots” gratinated with garlic butter', '18'),
        ('L’œuf parfait', 'Perfect poached egg', '19'),
        ('Foie gras poêlé au raisin blanc, déglacé de miel et vinaigre balsamique', 'Pan-seared foie gras with white grape, honey and balsamic sauce', '28'),
    ]},
    {'id': 'potages', 'fr': 'Les potages', 'en': 'Soups', 'items': [
        ('Traditionnelle gratinée à l’oignon', 'Traditional gratinated onion soup', '12'),
        ('Velouté de langouste', 'Creamy lobster bisque', '14'),
        ('La soupe de tomates glacée', 'Traditional Spanish gazpacho', '12'),
    ]},
    {'id': 'pates', 'fr': 'Les pâtes', 'en': 'Pastas', 'items': [
        ('Les « penne » aux trois fromages', 'Three-cheese penne', '25'),
        ('Tagliatelle à la langouste', 'Lobster fettuccine', '35'),
        ('Tagliatelle Alfredo', 'Fettuccine Alfredo', '26'),
        ('Linguine alle vongole', 'Linguine with clams', '34'),
        ('Penne arrabbiata', 'Penne arrabbiata', '25'),
    ]},
    {'id': 'poissons', 'fr': 'Les poissons', 'en': 'Fish & seafood', 'items': [
        ('Langouste du vivier, préparée selon votre choix : grillée, thermidor ou flambée (+5 €)', 'Lobster from the tank: grilled, thermidor or flambéed (+€5)', '41 / livre · 90 / kg'),
        ('Le vivaneau (pêche locale) rôti, chutney de mangue et son beurre blanc', 'Roasted local snapper with mango chutney and white wine butter sauce', '39'),
        ('La marmite des Caraïbes (Saint-Jacques, langouste, vivaneau, moules) dans son bouillon de crustacés à la crème', 'Caribbean fish pot: sea scallops, lobster, snapper and mussels in a creamy seafood broth', '39'),
        ('Tataki de thon local, salsa de mangue acidulée et caramel de soja', 'Local tuna tataki with citrus mango salsa and caramel soy sauce', '36'),
        ('Saint-Jacques rôties, carpaccio de magret fumé et crème de lentilles au foie gras', 'Roasted sea scallops, smoked duck breast carpaccio, creamy lentils and foie gras sauce', '38'),
        ('Gambas sautées à la provençale', 'Sautéed shrimp with garlic, parsley and zucchini', '37'),
    ], 'sides': True},
    {'id': 'viandes', 'fr': 'Les viandes et volailles', 'en': 'Meats & poultry', 'items': [
        ('Filet de bœuf à la plancha, sauce morilles', 'Beef tenderloin “à la plancha” with morel mushroom sauce', '45',
            [('avec sa tranche de foie gras', 'with pan-seared foie gras', '+10')]),
        ('Éventail de magret de canard poêlé, sauce à la canne à sucre et réduction de vinaigre balsamique', 'Thinly sliced roasted duck breast, sugar cane sauce and balsamic reduction', '38'),
        ('La souris d’agneau braisée « 24 heures » au vin blanc, miel et romarin', 'Lamb shank braised for 24 hours with white wine, honey and rosemary', '37'),
        ('Paleron de bœuf braisé au vin rouge et sa garniture bourguignonne (poitrine de porc et champignons)', 'Braised beef chuck with Burgundy garnish (bacon and mushroom)', '37'),
        ('Suprême de poulet fermier farci aux tomates confites, jambon cru et comté 24 mois, rôti aux épices cajun', 'Cajun-spiced free-range chicken breast stuffed with prosciutto, confit tomato and Comté cheese', '32'),
    ], 'sides': True},
    {'id': 'fromages', 'fr': 'Fromages', 'en': 'Cheeses', 'items': [
        ('L’assortiment de fromages, petite salade au balsamique, raisins frais et noix', 'Assorted cheeses with a balsamic-dressed salad, grapes and walnuts', '15'),
    ]},
    {'id': 'desserts', 'fr': 'Les desserts', 'en': 'Desserts', 'items': [
        ('Glaces et sorbets (la boule)', 'Ice cream and sorbet (per scoop)', '4'),
        ('La crème brûlée maison à la vanille', 'Homemade vanilla crème brûlée', '12'),
        ('La très belle profiterole', 'The amazing profiterole', '16'),
        ('Mi-cuit au chocolat maison et sa glace vanille', 'Homemade molten chocolate cake with vanilla ice cream', '14'),
        ('Le fruit du moment en trompe-l’œil Ocean 82', 'Fruit of the day in trompe-l’œil, Ocean 82 style', '16'),
        ('Soufflé au Grand Marnier, crème anglaise et sauce chocolat', 'Grand Marnier soufflé with custard and chocolate sauce', '16'),
    ]},
]

SIDES = ('Accompagnements au choix : assortiment de légumes, gratin de pommes de terre, purée de pommes de terre, '
         'purée de patates douces, riz, pâtes et salade.',
         'Side of your choice: vegetables, potato gratin, mashed potato, mashed sweet potato, rice, pasta or salad.')
TAX = ('Nos prix s’entendent hors TGCA (4 %).', 'Local tax (TGCA 4%) not included.')

DIGESTIFS = [
    ('Cognacs', 'Cognacs', [('Camus VS Élégance', '9'), ('Camus VSOP Élégance', '16'), ('Camus XO Élégance', '25'),
                            ('Dégustation de 3 cognacs Camus « Île de Ré » (6 cl) — Fine Island, Maturated et Cliff Cellar', '20')]),
    ('Armagnacs', 'Armagnacs', [('Janneau VSOP', '9'), ('Janneau 15 ans', '14'), ('Janneau 1980', '18')]),
    ('Calvados', 'Calvados', [('Berneroy VSOP', '9'), ('Berneroy XO', '14')]),
    ('Rhums vieux', 'Aged rums', [('Pyrat XO Reserve, HSE rhum vieux VO', '9'), ('Saint-Étienne XO', '15')]),
    ('Eaux-de-vie', 'Eaux-de-vie', [('Grappa di Barolo, poire William, framboise', '9')]),
    ('Whisky', 'Whisky', [('J. Walker Black Label', '9'), ('Chivas Regal 12 ans, Glenlivet 12 ans', '10'), ('J. Walker Blue Label', '27')]),
    ('Liqueurs', 'Liqueurs', [('Limoncello di Capri, Get 27, Get 31, Sambuca Molinari, Amaretto, Frangelico, Manzana', '8'),
                              ('Grand Marnier, Chartreuse, Baileys', '9')]),
    ('Tequila', 'Tequila', [('Patrón Añejo, Silver, Reposado ou XO Café', '10'), ('El Jimador Gold', '7')]),
    ('Porto', 'Port', [('Sandeman blanc', '8'), ('Sandeman Ruby', '8')]),
]
