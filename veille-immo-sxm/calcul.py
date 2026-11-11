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
    dict(id="", nom="The Hills Residence D-448", secteur="Simpson Bay", prix=291000, chambres=2, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://www.thehillsresidence.com/condo-for-sale/",
         notes="2 chambres le moins cher trouvé. Page vue il y a environ 190 jours."),
    dict(id="", nom="Jordan Village", secteur="Cupecoy", prix=285000, chambres=1, sdb=None, charges=180,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://realestatesxm.com/property/for-sale/sint-maarten-condo-for-sale-cupecoy-jordan-village-1bedroom",
         notes="Charges très basses. Près de l'université AUC : location à l'année possible (700 à 1 300 $/mois pour 1 chambre)."),
    dict(id="1145339", nom="Rainbow Beach Club", secteur="Cupecoy", prix=425000, chambres=2, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://century21stmaarten.com/en/d/1145339",
         notes="Bord de plage. Prix vu à 425 000 $ et à 490 000 $ selon les pages."),
    dict(id="", nom="Sapphire", secteur="Cupecoy", prix=450000, chambres=2, sdb=2, charges=865,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://realestatesxm.com/property/for-sale/2-bedrooms-condo-for-sale-st-maarten-cupecoy-sapphire",
         notes="Charges élevées."),
    dict(id="", nom="The Hills Residence A-107", secteur="Simpson Bay", prix=475000, chambres=2, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://www.thehillsresidence.com/condo-for-sale/",
         notes="Avec jardin."),
    dict(id="", nom="Blue Marine Residence", secteur="Maho", prix=490000, chambres=2, sdb=2, charges=937,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://www.sxmrealestate.com/property/blue-marine-residence-condo-for-sale-2/",
         notes="1 500 pi². D'autres pages affichent 365 000 $ (1,5 chambre) ou 999 000 $ : prix à confirmer."),
    dict(id="C21114220368", nom="Echo View (neuf)", secteur="Point Blanche", prix=395000, chambres=None, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None,
         url="https://c21responsive.immobel.com/property/new-oceanview-echo-view-condos-for-sale-pointe-blanche-sint-maarten-C21114220368-USD",
         notes="Construction neuve, vue mer. Nombre de chambres à confirmer."),
    dict(id="", nom="Seneca Apartments", secteur="Point Blanche", prix=410000, chambres=2, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://oasislivingrealty.com/sale-page-2/",
         notes="Résidence fermée avec piscine, vue mer. Annonce peut-être ancienne."),
    dict(id="1151842", nom="Lajas Residence", secteur="Point Blanche", prix=434920, chambres=2, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://century21stmaarten.com/en/d/1151842", notes=""),
    dict(id="1155957", nom="Condo face à la mer, Point Blanche", secteur="Point Blanche", prix=468720, chambres=2, sdb=2.5,
         charges=None, loyer=None, str_ok=None, pleine_propriete=None,
         url="https://century21stmaarten.com/en/d/point-blanche-2-bedroom-oceanfront-condos-for-sale-1155957",
         notes="Prix vu à 468 720 $ et à 522 000 $ : à confirmer."),
    dict(id="", nom="Atlantica Beach Club", secteur="Dawn Beach", prix=499990, chambres=2, sdb=None, charges=None,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://oasislivingrealty.com/sale-page-2/",
         notes="Résidence fermée, vue mer. Annonce peut-être ancienne."),
    dict(id="", nom="La Terrasse, Maho Village", secteur="Maho", prix=285000, chambres=1, sdb=1, charges=850,
         loyer=None, str_ok=None, pleine_propriete=None, url="https://www.andreurealty.com/post/st-martin-condos-for-sale",
         notes="Petit (452 pi²) et charges lourdes."),
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
