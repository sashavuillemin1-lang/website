"""Veille Sint Maarten (côté hollandais) : rendement et score des condos à vendre.

Usage : python3 calcul.py AAAA-MM-JJ -> met à jour annonces.csv à partir de la liste BIENS du passage
(dédoublonnage par numéro d'annonce ou nom, détection des baisses de prix, retrait après 2 passages absents).
Toutes les hypothèses sont regroupées dans HYP pour être ajustées par les associés.
"""
import csv
import os
import sys

DATE = sys.argv[1] if len(sys.argv) > 1 else "2026-11-11"
HYP = {
    "frais_achat": 0.055,        # taxe de mutation 4 % + notaire 1 à 2 %
    "charges_defaut": 661,       # charges de copropriété médianes ($/mois) quand non publiées
    "frais_location": 0.20,      # ménage, plateformes, entretien, électricité (gestion par les associés)
    "net_cible": 0.05,           # rendement net visé pour le « loyer nécessaire »
    "budget_max": 550000,
}
SECTEURS_FORTS = {"Simpson Bay", "Cupecoy", "Maho"}

# loyer = loyer mensuel moyen connu (historique ou annonce), None si inconnu
# str_ok / pleine_propriete : True, False ou None (inconnu)
BIENS = [
    # Vérifiés le 2026-11-11 sur realestatesxm.com et thehillsresidence.com
    dict(id="RESXM-601", nom="Princess Heights (2 suites)", secteur="Dawn Beach", prix=455000, chambres=2, sdb=2, charges=775,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://realestatesxm.com/property/for-sale/caribbean-property-for-sale-sxm-ocean-view-condo",
         notes="Condo-hôtel au-dessus de Dawn Beach, meublé, vue mer. Conçu comme deux suites reliées avec terrasses séparées : une suite peut se louer à part."),
    dict(id="RESXM-613", nom="Tamarind Apartments (2 × 1 chambre)", secteur="Point Blanche", prix=345000, chambres=2, sdb=2, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://realestatesxm.com/property/for-sale/st-maarten-homes-for-sale-tamarind-apartments-2-condos",
         notes="Deux 1 chambre mitoyens avec mezzanine, meublés, vendus ensemble : deux logements à louer. Piscine. Charges non publiées."),
    dict(id="HILLS-A-107", nom="The Hills Residence A-107", secteur="Simpson Bay", prix=475000, chambres=2, sdb=1, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://www.thehillsresidence.com/condo-for-sale/",
         notes="75 m², meublé, jardin d'angle, vue lagon. Une seule salle de bain."),
    dict(id="RESXM-446", nom="Sapphire", secteur="Cupecoy", prix=486000, chambres=2, sdb=2, charges=865,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://realestatesxm.com/property/for-sale/2-bedrooms-condo-for-sale-st-maarten-cupecoy-sapphire",
         notes="101 m², 3e étage, meublé, piscine, salle de sport, résidence sécurisée. Prix passé de 450 000 à 486 000 $."),
    dict(id="RESXM-595", nom="Vivid Residences (neuf)", secteur="Point Blanche", prix=468720, chambres=2, sdb=2.5, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://realestatesxm.com/property/for-sale/sxm-point-blanche-2-bedroom-oceanfront-property-for-sale",
         notes="Neuf, face à la mer, 16 logements, volets anticycloniques. De 468 720 à 578 550 $ selon le logement chez Real Estate SXM ; Andreu affiche un logement à 458 800 $ (2 ch., 3 sdb, 1 346 pi²)."),
    dict(id="RESXM-626C", nom="Jordan Village M14 (studio)", secteur="Cupecoy", prix=245000, chambres=None, sdb=1, charges=180,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://realestatesxm.com/property/for-sale/sxm-cupecoy-jordan-village-condo-for-sale-m14",
         notes="Studio de 64 m² avec mezzanine, meublé, vue lagon. Déjà loué à l'année (loyer à demander). Près de l'université AUC."),
    dict(id="HILLS-C-313", nom="The Hills Residence C-313", secteur="Simpson Bay", prix=284000, chambres=1, sdb=1, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://www.thehillsresidence.com/condo-for-sale/", notes="Rez-de-chaussée, bâtiment 3."),
    dict(id="HILLS-C-315", nom="The Hills Residence C-315", secteur="Simpson Bay", prix=299000, chambres=1, sdb=1, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://www.thehillsresidence.com/condo-for-sale/", notes="53 m², meublé."),
    dict(id="HILLS-A-103", nom="The Hills Residence A-103", secteur="Simpson Bay", prix=345000, chambres=1, sdb=1, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://www.thehillsresidence.com/condo-for-sale/", notes="81 m², meublé, jardin privé."),
    dict(id="RESXM-624", nom="Port de Plaisance, 1 chambre (neuf)", secteur="Cole Bay", prix=388000, chambres=1, sdb=1, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://realestatesxm.com/property/for-sale/premium-luxury-1-bedroom-condos-for-sale-at-port-de-plaisance",
         notes="65 m², programme neuf haut de gamme."),
    dict(id="RESXM-619", nom="T-Residence, 1 chambre", secteur="Maho", prix=445000, chambres=1, sdb=1, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://realestatesxm.com/property/for-sale/luxury-1-bdr-apartment-for-sale-at-t-residence-in-the-heart-of-maho-gated-community",
         notes="Résidence fermée au cœur de Maho. Cher pour 1 chambre."),
    # Nouveaux le 2026-11-16 (andreurealty.com, realestatesxm.com)
    dict(id="ANDREU-1128", nom="Cole Bay, 2 chambres rénové dernier étage", secteur="Cole Bay", prix=425000, chambres=2, sdb=1, charges=0,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://www.andreurealty.com/sint-maarten-real-estate/renovated-2-bedroom-top-floor-condo-with-sea-view-for-sale-in-cole-bay-sint-maarten",
         notes="90 m², entièrement rénové, meublé, vue lagon et mer, parking, AUCUNE charge de copropriété (assurance du bâtiment à prévoir soi-même). Libre."),
    dict(id="ANDREU-11078", nom="Guana Bay, duplex 5 chambres", secteur="Guana Bay", prix=460000, chambres=5, sdb=4, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://www.andreurealty.com/sint-maarten-real-estate/spacious-5-bedroom-duplex-condo-in-guana-bay-st-maarten",
         notes="273 m² sur deux niveaux, 5 chambres et 4 salles de bain, semi-meublé, résidence fermée. Idéal pour une colocation à l'année. Charges non publiées. Libre."),
    dict(id="ANDREU-11109", nom="Belair Plaza, 2 chambres (sur plan)", secteur="Cay Hill", prix=380000, chambres=2, sdb=3, charges=357,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://www.andreurealty.com/sint-maarten-real-estate/pre-construction-condo-for-sale-in-cay-hill-belair-plaza-sint-maarten",
         notes="Vente sur plan, livraison prévue en 2026, 129 m², 2 suites, 4e étage, non meublé. Risque de retard de chantier. Secteur résidentiel (Little Bay / Cay Hill), peu touristique."),
    dict(id="RESXM-631", nom="Ocean Blue Residence, studio (neuf)", secteur="Cupecoy", prix=380076, chambres=None, sdb=1, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://realestatesxm.com/property/for-sale/st-maarten-blue-mall-ocean-blue-condos-for-sale-studio",
         notes="Studio neuf de 66 m², vue mer et lagon. Cher pour un studio."),
    # Nouveaux le 2026-11-23
    dict(id="ANDREU-1122", nom="The Hills Residence, 1 chambre neuve vue marina", secteur="Simpson Bay", prix=275000, chambres=1, sdb=1, charges=300,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://www.andreurealty.com/sint-maarten-real-estate/the-hills-residence-brand-new-1-bedroom-condo-with-lagoon-and-marina-view-for-sale-in-simpson-bay-sint-maarten",
         notes="Neuf (2025), 53 m², vue lagon et marinas, piscine sur le toit, semi-meublé, libre. Charges de 300 $/mois."),
    dict(id="ANDREU-1129", nom="The Emerald, studio clé en main", secteur="Maho", prix=199000, chambres=None, sdb=1, charges=250,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://www.andreurealty.com/sint-maarten-real-estate/the-emerald-turnkey-rental-studio-with-pool-view-for-sale-in-maho-sint-maarten",
         notes="Studio de 27 m², meublé, balcon sur la piscine. Déjà des réservations pour la haute saison 2026-2027 (location courte durée pratiquée). Petit."),
    dict(id="RESXM-632", nom="Ocean Blue Residence, 1 chambre (sur plan)", secteur="Cupecoy", prix=441771, chambres=1, sdb=1, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://realestatesxm.com/property/for-sale/caribbean-ocean-blue-cupecoy-sxm-condos-for-sale",
         notes="Vente sur plan, 78 m², vue mer. Cher pour 1 chambre."),
    # Non revérifiés : pages Century 21 refusées (erreur 403), Blue Marine sans détail lisible
    dict(id="1145339", nom="Rainbow Beach Club", secteur="Cupecoy", prix=425000, chambres=2, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://century21stmaarten.com/en/d/1145339",
         notes="NON REVÉRIFIÉE (Century 21 inaccessible). Attention : un 2 chambres meublé de Rainbow Beach Club est sous compromis chez Andreu (525 000 $), peut-être le même logement. Bord de plage. Prix vu à 425 000 et 490 000 $."),
    dict(id="1151842", nom="Lajas Residence", secteur="Point Blanche", prix=434920, chambres=2, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://century21stmaarten.com/en/d/1151842",
         notes="NON REVÉRIFIÉE (Century 21 inaccessible)."),
    dict(id="", nom="Blue Marine Residence", secteur="Maho", prix=490000, chambres=2, sdb=2, charges=937,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://www.andreurealty.com/sint-maarten-real-estate/blue-marine-residence-condo-for-sale-2-bedroom-in-maho-sint-maarten",
         notes="Vérifié chez Andreu (fiche 11201) : 1 500 pi², angle, 2e étage, meublé, construit en 2012, actuellement occupé. Grande piscine, salle de sport, ascenseur."),
    dict(id="", nom="La Terrasse, Maho Village", secteur="Maho", prix=274000, chambres=1, sdb=1, charges=850,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://www.andreurealty.com/sint-maarten-real-estate/poolside-1-bedroom-condo-in-maho-village-la-terrasse-sint-maarten",
         notes="Petit (452 pi²), bord de piscine, charges lourdes."),
    dict(id="", nom="Seneca Apartments", secteur="Point Blanche", prix=410000, chambres=2, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://oasislivingrealty.com/sale-page-2/",
         notes="Toujours affiché chez Oasis. Résidence fermée récente, six étages, vue mer, piscine."),
    dict(id="", nom="Atlantica Beach Club", secteur="Dawn Beach", prix=499990, chambres=2, sdb=2, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://oasislivingrealty.com/sale-page-2/",
         notes="Toujours affiché chez Oasis. Résidence fermée de Dawn Beach Estates, vue mer, toit en béton, volets anticycloniques."),
]


def calc(b):
    charges = b["charges"] if b["charges"] is not None else HYP["charges_defaut"]
    cout = b["prix"] * (1 + HYP["frais_achat"])
    necessaire = (HYP["net_cible"] * cout / 12 + charges) / (1 - HYP["frais_location"])
    brut = net = None
    if b["loyer"]:
        brut = b["loyer"] * 12 / b["prix"]
        net = (b["loyer"] * 12 * (1 - HYP["frais_location"]) - charges * 12) / cout
    return charges, necessaire, brut, net


def score(b, charges, necessaire, net):
    # 40 : loyer nécessaire (1 500 $ ou moins = 40, 4 000 $ ou plus = 0), ou rendement net réel s'il est connu
    if net is not None:
        s = max(0, min(40, (net - 0.02) / 0.05 * 40))
    else:
        s = max(0, min(40, (4000 - necessaire) / 2500 * 40))
    s += max(0, min(15, (0.04 - charges * 12 / b["prix"]) / 0.03 * 15))   # 15 : poids des charges
    s += 15 if b["secteur"] in SECTEURS_FORTS else 8                       # 15 : secteur locatif
    s += {None: 3, 1: 6}.get(b["chambres"], 10)                            # 10 : taille
    s += 10 if b["str_ok"] else 0                                          # 10 : location courte durée confirmée
    s += 10 if b["pleine_propriete"] else 0                                # 10 : pleine propriété confirmée
    if b["str_ok"] is False:
        s = 0
    return round(s)


COLS = ["id_annonce", "nom", "secteur", "url", "prix", "prix_precedent", "chambres", "sdb", "charges_mensuelles",
        "loyer_connu_mensuel", "loyer_necessaire_5pct", "rendement_brut", "rendement_net", "location_courte_ok",
        "pleine_propriete", "date_premiere_vue", "date_derniere_vue", "statut", "score", "notes"]


def oui_non(v):
    return "" if v is None else ("oui" if v else "non")


rows = []
for b in BIENS:
    charges, necessaire, brut, net = calc(b)
    rows.append({
        "id_annonce": b["id"], "nom": b["nom"], "secteur": b["secteur"], "url": b["url"], "prix": b["prix"],
        "prix_precedent": "", "chambres": b["chambres"] or "", "sdb": b["sdb"] or "",
        "charges_mensuelles": b["charges"] if b["charges"] is not None else f"{HYP['charges_defaut']} (défaut)",
        "loyer_connu_mensuel": b["loyer"] or "", "loyer_necessaire_5pct": round(necessaire),
        "rendement_brut": f"{brut:.2%}" if brut else "", "rendement_net": f"{net:.2%}" if net is not None else "",
        "location_courte_ok": oui_non(b["str_ok"]), "pleine_propriete": oui_non(b["pleine_propriete"]),
        "date_premiere_vue": DATE, "date_derniere_vue": DATE, "statut": "nouveau",
        "score": score(b, charges, necessaire, net), "notes": b["notes"],
    })

# --- Fusion avec l'historique (passages précédents) ---
def cle(r):
    return r["id_annonce"] or r["nom"].lower().replace(" ", "")

passages = []
if os.path.exists("passages.txt"):
    passages = [l.strip() for l in open("passages.txt", encoding="utf-8") if l.strip()]
if DATE not in passages:
    passages.append(DATE)
anciens = {}
if os.path.exists("annonces.csv"):
    with open("annonces.csv", encoding="utf-8") as f:
        anciens = {cle(r): r for r in csv.DictReader(f)}
vus = set()
for r in rows:
    k = cle(r)
    vus.add(k)
    a = anciens.get(k)
    if not a:
        continue
    r["date_premiere_vue"] = a["date_premiere_vue"]
    if a["prix"] and int(r["prix"]) < int(a["prix"]):
        r["statut"], r["prix_precedent"] = "baisse", a["prix"]
    elif a["date_premiere_vue"] != DATE:
        r["statut"], r["prix_precedent"] = "actif", a["prix_precedent"]
for k, a in anciens.items():
    if k in vus:
        continue
    # absente lors des 2 derniers passages (celui-ci inclus) -> retirée
    if len(passages) >= 2 and a["date_derniere_vue"] < passages[-2]:
        a["statut"] = "retiré"
    elif a["statut"] == "nouveau":
        a["statut"] = "actif"
    rows.append(a)
with open("passages.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(passages) + "\n")

rows.sort(key=lambda r: -int(r["score"]))
with open("annonces.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
for r in rows:
    print(r["score"], r["nom"], r["prix"], r["loyer_necessaire_5pct"], r["statut"])
