# Mission : veille immobilière hebdomadaire, Montréal (achat pour colocation)

Ce fichier contient les consignes complètes que suit la tâche planifiée hebdomadaire. Les associés peuvent modifier les critères ici. Les hypothèses chiffrées se trouvent dans `HYP`, en haut de `calcul.py`.

## Déroulé d'un passage
1. Se placer sur la branche `claude/ecstatic-carson-di9olt` et récupérer la dernière version (`git pull`).
2. Lire ce fichier, le dernier `rapport_*.md`, `annonces.csv` et `passages.txt`.
3. **Le premier lundi du mois**, vérifier où en est l'interdiction fédérale d'achat par les non-Canadiens (expiration prévue le 1er janvier 2027, remplacement éventuel).
4. Rechercher les annonces (voir Sources) : quelques requêtes par quartier et par type de bien, sans pagination massive.
4 bis. **Revérifier chaque annonce déjà connue** d'`annonces.csv` (sauf les retirées) par une recherche de son numéro Centris ou de son adresse. N'inclure dans `BIENS` que celles qui sont retrouvées encore en vente. Une annonce non retrouvée faute d'accès aux sites ne doit pas être comptée comme retirée : la garder dans `BIENS` avec ses données précédentes et noter « non revérifiée ».
5. Mettre à jour la liste `BIENS` de `calcul.py` avec **les annonces vues lors de ce passage**, y compris celles déjà connues encore en ligne, au prix actuel. Pour chaque annonce, renseigner `id` (numéro Centris) dès qu'il est connu. Si une fiche récente le permet, remplacer les données estimées par les vraies (revenus, taxes, chambres, salles de bain).
6. Lancer `python3 calcul.py AAAA-MM-JJ` depuis `veille-immo/`. Le script fusionne avec l'historique : il détecte les baisses de prix et passe en « retiré » les annonces absentes de 2 passages consécutifs.
7. Écrire `rapport_AAAA-MM-JJ.md` (format ci-dessous), puis faire un commit et pousser.
8. Envoyer le résumé par courriel (voir le message de la tâche planifiée pour le destinataire).

## Critères de recherche
- **Budget** : prix affiché de 700 000 $ CA au maximum, plus environ 13 000 $ de frais d'achat.
- **Types de bien** : condo de 3 chambres ou plus, duplex, triplex, quadruplex. ⚠️ Signaler en priorité les biens de 4 logements ou plus, qui ne sont pas visés par l'interdiction fédérale.
- **Chambres** : au moins 3 dans le logement destiné à la colocation. 4 ou plus donne un bonus.
- **Salles de bain** : 2 ou plus donne un bonus. Une seule salle de bain pour 4 colocataires donne une pénalité.
- **Quartiers prioritaires** : Mercier–Hochelaga-Maisonneuve, Rosemont–La Petite-Patrie, Villeray–Saint-Michel–Parc-Extension.
- **Quartiers secondaires** : Plateau-Mont-Royal, Côte-des-Neiges, Verdun, Sud-Ouest.
- **Transport** : métro à 10 minutes à pied ou moins (bonus fort), ou bus express, ou REM.
- **À exclure** : résidences pour aînés, coopératives, ventes « avec travaux majeurs » non chiffrés, condos dont le règlement interdit la location à la chambre.

## Sources (dans cet ordre)
1. Centris.ca
2. Realtor.ca
3. DuProprio.com
4. Alertes Centris reçues dans Gmail : chercher les courriels d'alerte des 7 derniers jours.

Règles :
- Si un site refuse l'accès, **ne pas le contourner** : pas de curl, de miroir ni de cache. Le noter dans le rapport et passer à la source suivante.
- Si les fiches ne sont pas joignables, chercher le numéro Centris avec une recherche du type `centris "<adresse>"`.
- **Ne jamais contacter un courtier ni un vendeur.**
- Ne jamais inventer de données. Un champ inconnu reste vide et figure parmi les points de vigilance.

## Calcul et score
Le calcul et le score sont faits par `calcul.py`.
- **Rendement brut** = loyers annuels / prix.
- **Rendement net** = (loyers − taxes − frais de copropriété − assurance − électricité et internet des logements en colocation − vacance de 5 % − entretien de 3 %) / (prix + frais d'achat).
- **Score sur 100** : rendement net 40, métro 20, chambres et salles de bain 15, quartier 10, réglementation 10, état 5.

## Format du rapport `rapport_AAAA-MM-JJ.md`
1. **Nouveautés** : nouvelles annonces et baisses de prix, triées par score.
2. **Top 10 du stock actuel**, trié par score.
3. Pour chaque bien : lien direct vers la fiche, adresse, prix, type, chambres et salles de bain, loyer estimé, rendements brut et net, score, 2 points forts et 2 points de vigilance.
4. **Alertes** : sources inaccessibles, annonces retirées, anomalies.
5. **Rappels réglementaires** (sans les présenter comme des conseils juridiques) : interdiction fédérale, déclaration de copropriété, risque de requalification en maison de chambres, fiscalité à valider avec un fiscaliste.

## Courriel hebdomadaire
- **Objet** : `Veille immo Montréal – semaine du AAAA-MM-JJ`.
- **Corps**, en texte simple et en français, sans données personnelles d'un tiers :
  - les nouveautés et les baisses de prix (adresse, prix, score, lien) ;
  - le Top 5 ;
  - les alertes ;
  - le chemin du rapport complet dans le dépôt.
- S'il n'y a aucune nouveauté, envoyer quand même le courriel avec la mention « aucune nouveauté cette semaine ».
