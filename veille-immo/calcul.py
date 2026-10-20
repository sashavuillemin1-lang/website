"""Calcul des rendements et scores pour la veille immobilière (colocation, Montréal).

Usage : python3 calcul.py AAAA-MM-JJ -> met à jour annonces.csv à partir de la liste BIENS du passage
(dédoublonnage par id ou adresse, détection des baisses de prix, retrait après 2 passages absents).
Toutes les hypothèses sont regroupées dans HYP pour être ajustées par les associés.
"""
import csv

import sys
DATE = sys.argv[1] if len(sys.argv) > 1 else "2026-10-20"
HYP = {
    "frais_achat": 13000,
    "taxe_taux": 0.008,          # taxes municipales + scolaires estimées à 0,8 % du prix (inconnues dans l'index)
    "frais_condo_an": 3000,      # 250 $/mois si non indiqué
    "assurance": 1500,
    "charges_coloc_an": 2400,    # électricité + internet par logement en colocation (toutes charges incluses)
    "vacance": 0.05,
    "entretien": 0.03,
    # loyer par chambre, milieu de fourchette + 100 $ (toutes charges et meublé)
    "loyer_ch": {"MHM": 800, "Rosemont": 900, "Villeray": 900, "Saint-Michel/Parc-Ex": 850},
    # loyers par défaut quand les loyers en place sont inconnus (hypothèse, à recaler)
    "loyer_defaut": {"3½": 950, "4½": 1150, "5½": 1350, "6½": 1500},
}
CH = {"3½": 1, "4½": 2, "5½": 3, "6½": 3, "7½": 4, "8½": 4}
PIECES = {"3½": 3.5, "4½": 4.5, "5½": 5.5, "6½": 6.5, "7½": 7.5, "8½": 8.5}
PRIORITAIRES = {"MHM", "Rosemont", "Villeray", "Saint-Michel/Parc-Ex"}

def U(cat):
    return f"https://www.centris.ca/fr/{cat}"

# metro : minutes à pied estimées (None = inconnu) ; logements : composition connue ou None
BIENS = [
    dict(adresse="8370A-8372, avenue Querbes", quartier="Saint-Michel/Parc-Ex", type="triplex", nb=3, logements=None,
         revenus=57600, prix=650000, annee=1948, sdb=None, metro=12, id="24859967", url=U("triplex~a-vendre~montreal-villeray-saint-michel-parc-extension/24859967"),
         notes="Revenus bruts potentiels 57 600 $ (ratio 8,9 %, inhabituel : vérifier les baux). Composition des logements non indiquée."),
    dict(adresse="7152-7156, 17e Avenue", quartier="Saint-Michel/Parc-Ex", type="triplex", nb=3, logements=["3½", "3½", "6½"],
         revenus=48000, prix=648000, annee=1932, sdb=1, metro=13, id="24737003", url=U("triplex~a-vendre~montreal-villeray-saint-michel-parc-extension/24737003"),
         notes="Jumelé. Revenus bruts potentiels 48 000 $. Logement principal (6½) : 3 ch., 1 sdb. Courtier RE/MAX Alliance."),
    dict(adresse="5483-5487, boulevard Saint-Michel", quartier="Rosemont", type="triplex", nb=3, logements=None,
         revenus=39600, prix=660000, annee=None, sdb=None, metro=20, url=U("triplex~a-vendre~montreal-rosemont-la-petite-patrie"),
         notes="Composition et année non indiquées. Artère passante."),
    dict(adresse="5343-5347, 3e Avenue", quartier="Rosemont", type="triplex", nb=3, logements=["5½", "5½", "6½"],
         revenus=None, prix=699000, annee=1919, sdb=None, metro=18, id="26983111", url=U("triplex~a-vendre~montreal-rosemont-la-petite-patrie/26983111"),
         notes="Trois logements de 3 chambres : 3 colocations possibles. Revenus non indiqués. Ancienne fiche 16256335 à 639 000 $ (prix relevé ou nouvelle inscription ?)."),
    dict(adresse="6992-6994, avenue d'Outremont", quartier="Saint-Michel/Parc-Ex", type="duplex", nb=2, logements=None,
         revenus=43200, prix=650000, annee=1927, sdb=1, metro=10, id="23398820", url=U("duplex~a-vendre~montreal-villeray-saint-michel-parc-extension/23398820"),
         notes="HORS CRITÈRES : logement principal de 6 pièces mais 2 ch. seulement (+ sdb et salle d'eau) ; 4½ du haut VACANT (valeur locative 1 600 $). Revenus potentiels 3 600 $/mois. Taxes 2025 : 4 066 $. Métro Acadie et REM à proximité. Sous-sol > 6 pi : 3e chambre possible ?"),
    dict(adresse="8115-8117, rue Boyer", quartier="Villeray", type="duplex", nb=2, logements=None,
         revenus=22140, prix=599000, annee=None, sdb=None, metro=12, url=U("duplex~a-vendre~montreal-villeray-saint-michel-parc-extension"),
         notes="Revenus bas (22 140 $) : potentiel si un logement se libère. Composition non indiquée."),
    dict(adresse="2772-2774, rue de Cadillac", quartier="MHM", type="duplex", nb=2, logements=["4½", "8½"],
         revenus=31920, prix=615000, annee=1953, sdb=None, metro=7, url=U("duplex~a-vendre~montreal-mercier-hochelaga-maisonneuve"),
         notes="Fiche exacte non trouvée dans l'index (lien = recherche du quartier). Décrit comme rénové. Un 8½ idéal pour la colocation (4 chambres ou plus). Sous-sol aménageable. Stationnement en allée."),
    dict(adresse="2185-2185A, avenue Mercier", quartier="MHM", type="duplex", nb=2, logements=None,
         revenus=None, prix=529900, annee=1959, sdb=None, metro=15, url=U("duplex~a-vendre~montreal-mercier-hochelaga-maisonneuve"),
         notes="822 pi² habitables seulement : sans doute trop petit pour une colocation de 3 chambres. Info manquante."),
    dict(adresse="5534-5536, rue Pierre-Tétreault", quartier="MHM", type="duplex", nb=2, logements=None,
         revenus=None, prix=615000, annee=1954, sdb=None, metro=None, url=U("duplex~a-vendre~montreal-mercier-hochelaga-maisonneuve"),
         notes="Détaché, stationnement. Composition et revenus non indiqués."),
    dict(adresse="5310, 16e Avenue", quartier="Rosemont", type="duplex", nb=2, logements=["4½", "4½"],
         revenus=28320, prix=674900, annee=None, sdb=None, metro=20, url=U("duplex~a-vendre~montreal-rosemont-la-petite-patrie"),
         notes="HORS CRITÈRES : aucun logement de 3 chambres (2 × 4½)."),
    dict(adresse="2323-2325, rue Monsabré", quartier="MHM", type="duplex", nb=2, logements=["4½", "4½"],
         revenus=22800, prix=549000, annee=1908, sdb=None, metro=12, url=U("duplex~a-vendre~montreal-mercier-hochelaga-maisonneuve"),
         notes="HORS CRITÈRES : aucun logement de 3 chambres (2 × 4½)."),
    dict(adresse="2831-2833, rue Dickson", quartier="MHM", type="duplex", nb=2, logements=["4½", "4½"],
         revenus=None, prix=549000, annee=1914, sdb=None, metro=12, url=U("duplex~a-vendre~montreal-mercier-hochelaga-maisonneuve"),
         notes="HORS CRITÈRES : aucun logement de 3 chambres (2 × 4½)."),
    dict(adresse="6730, place Beaubien", quartier="MHM", type="condo", nb=1, chambres=3, sdb=2,
         prix=694800, annee=1985, metro=None, id="25760012", url=U("condo~a-vendre~montreal-mercier-hochelaga-maisonneuve/25760012"),
         notes="Nouveau-Rosemont. Même unité aussi inscrite à 688 800 $ (fiches 18926174 et 22288044, intergénération). 1 726 pi², 1 chambre au sous-sol, garage, cour. Frais de copropriété et règlement (location à la chambre) inconnus."),
    dict(adresse="4816, rue De Chambly, app. 3", quartier="Rosemont", type="condo", nb=1, chambres=3, sdb=1,
         prix=639700, annee=2000, metro=15, id="17409780", url=U("condo~a-vendre~montreal-rosemont-la-petite-patrie/17409780"),
         notes="1 158 pi², balcon, stationnement. Frais de copropriété et règlement inconnus."),
    dict(adresse="4245, boulevard Rosemont, app. 6", quartier="Rosemont", type="condo", nb=1, chambres=3, sdb=1,
         prix=629000, annee=1999, metro=15, id="20794958", url=U("condo~a-vendre~montreal-rosemont-la-petite-patrie/20794958"),
         notes="1 213 pi², foyer au bois, stationnement. Frais de copropriété et règlement inconnus."),
    dict(adresse="6535, rue De Lanaudière", quartier="Rosemont", type="condo", nb=1, chambres=3, sdb=1,
         prix=599900, annee=1926, metro=8, id="16582342", url=U("condo~a-vendre~montreal-rosemont-la-petite-patrie/16582342"),
         notes="COPROPRIÉTÉ INDIVISE : financement plus difficile, convention d'indivision à lire. 1 072 pi²."),
]

def calc(b):
    rch = HYP["loyer_ch"][b["quartier"]]
    coloc_units = 0
    if b["type"] == "condo":
        ch = b["chambres"]
        loyers = ch * rch * 12
        coloc_units, ch_coloc = 1, ch
        frais_condo = HYP["frais_condo_an"]
    else:
        frais_condo = 0
        lg = b["logements"]
        ch_coloc = 0
        if lg:
            # le plus grand logement de 3 chambres ou plus passe en colocation ; les autres au loyer en place
            big = [l for l in lg if CH[l] >= 3]
            coloc = set()
            if b["type"] == "triplex" and len(big) == 3:
                coloc = {max(range(3), key=lambda i: PIECES[lg[i]])}  # scénario prudent : 1 seul logement libéré
            elif big:
                coloc = {max(range(len(lg)), key=lambda i: PIECES[lg[i]])}
            tot_p = sum(PIECES[l] for l in lg)
            loyers = 0
            for i, l in enumerate(lg):
                if i in coloc:
                    loyers += CH[l] * rch * 12
                    ch_coloc = CH[l]
                elif b["revenus"]:
                    loyers += b["revenus"] * PIECES[l] / tot_p
                else:
                    loyers += HYP["loyer_defaut"][l] * 12
            coloc_units = len(coloc)
        else:
            loyers = b["revenus"] or 0
    if not loyers:
        return None
    depenses = (b["prix"] * HYP["taxe_taux"] + frais_condo + HYP["assurance"] + coloc_units * HYP["charges_coloc_an"]
                + loyers * (HYP["vacance"] + HYP["entretien"]))
    brut = loyers / b["prix"]
    net = (loyers - depenses) / (b["prix"] + HYP["frais_achat"])
    return loyers, brut, net, ch_coloc

def score(b, net, ch_coloc):
    s_rend = max(0, min(40, (net - 0.02) / 0.05 * 40)) if net is not None else 0
    m = b.get("metro")
    s_metro = 5 if m is None else (20 if m <= 10 else 10 if m <= 15 else 4)
    sdb = b.get("sdb") or 1
    s_ch = {0: 0, 1: 0, 2: 0, 3: 6, 4: 10}.get(ch_coloc, 12 if ch_coloc >= 5 else 0)
    if sdb >= 2: s_ch += 3
    if ch_coloc >= 4 and sdb == 1: s_ch -= 3
    s_ch = max(0, min(15, s_ch))
    s_q = 10 if b["quartier"] in PRIORITAIRES else 5
    s_reg = 10 if b["nb"] >= 4 else {3: 3, 2: 2}.get(b["nb"], 0)
    a = b.get("annee")
    s_etat = 2 if a is None else 5 if a >= 2000 else 4 if a >= 1970 else 3 if a >= 1940 else 2
    return round(s_rend + s_metro + s_ch + s_q + s_reg + s_etat)

COLS = ["id_annonce", "source", "url", "adresse", "quartier", "type", "nb_logements", "chambres", "sdb", "prix",
        "prix_precedent", "date_premiere_vue", "date_derniere_vue", "statut", "loyer_estime_mensuel", "rendement_brut",
        "rendement_net_estime", "score", "notes"]

rows = []
for b in BIENS:
    r = calc(b)
    hors = "HORS CRITÈRES" in b["notes"]
    if r:
        loyers, brut, net, chc = r
    else:
        loyers = brut = net = None
        chc = b.get("chambres", 0)
    if b["type"] != "condo":
        chc_txt = "/".join(str(CH[l]) for l in b["logements"]) if b["logements"] else ""
    else:
        chc_txt = str(b["chambres"])
    sc = 0 if hors else score(b, net, chc)
    rows.append({
        "id_annonce": b.get("id", ""), "source": "Centris (index de recherche)", "url": b["url"], "adresse": b["adresse"],
        "quartier": b["quartier"], "type": b["type"], "nb_logements": b["nb"], "chambres": chc_txt,
        "sdb": b.get("sdb") or "", "prix": b["prix"], "prix_precedent": "", "date_premiere_vue": DATE,
        "date_derniere_vue": DATE, "statut": "nouveau",
        "loyer_estime_mensuel": round(loyers / 12) if loyers else "",
        "rendement_brut": f"{brut:.2%}" if brut else "", "rendement_net_estime": f"{net:.2%}" if net is not None else "",
        "score": sc, "notes": b["notes"],
    })
# --- Fusion avec l'historique (passages précédents) ---
import os
def cle(r):
    return r["id_annonce"] or r["adresse"].lower().replace(" ", "")

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
    rows.append(a)
with open("passages.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(passages) + "\n")

rows.sort(key=lambda r: -int(r["score"]))
with open("annonces.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
for r in rows:
    print(r["score"], r["adresse"], r["prix"], r["loyer_estime_mensuel"], r["rendement_brut"], r["rendement_net_estime"])
