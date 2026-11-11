# Mission : veille immobilière hebdomadaire, Sint Maarten (côté hollandais)

Ce fichier contient les consignes complètes que suit la tâche planifiée hebdomadaire (le lundi). Il remplace la veille de Montréal, dont l'historique est conservé dans `veille-immo/`. Les associés peuvent modifier les critères ici. Les hypothèses chiffrées sont dans `HYP`, en haut de `calcul.py`.

## Objectif
Trouver des condos à vendre **côté hollandais de Saint-Martin (Sint Maarten)** à louer, en location saisonnière ou à l'année. Les associés vivent sur l'île et peuvent gérer la location eux-mêmes.

## Critères
- **Budget** : prix affiché de 550 000 $ US au maximum (cible : environ 500 000 $), plus environ 5,5 % de frais d'achat.
- **Côté hollandais uniquement** : Simpson Bay, Cupecoy, Maho, Cole Bay, Pelican Key, Point Blanche, Philipsburg, Dawn Beach, Oyster Pond côté hollandais. Exclure le côté français.
- **Types de bien** : condo ou appartement, de 1 chambre minimum. 2 chambres ou plus donne un bonus.
- **Secteurs prioritaires** : Simpson Bay, Cupecoy, Maho (la plupart des locations saisonnières).
- **À signaler** : location courte durée interdite par la copropriété (exclusion), terrain en bail emphytéotique (« erfpacht »), dégâts cycloniques, charges supérieures à 1 000 $ par mois.

## Déroulé d'un passage
1. Se placer sur la branche `claude/ecstatic-carson-di9olt` et récupérer la dernière version (`git pull`).
2. Lire ce fichier, le dernier `rapport_*.md`, `annonces.csv` et `passages.txt` dans `veille-immo-sxm/`.
3. **Revérifier chaque annonce déjà connue** (sauf les retirées) en cherchant son nom et son numéro. Une annonce non retrouvée faute d'accès aux sites ne doit pas être comptée comme retirée : la garder dans `BIENS` et noter « non revérifiée ».
4. Rechercher les nouvelles annonces : quelques requêtes par secteur, sans pagination massive.
5. Mettre à jour `BIENS` dans `calcul.py` avec toutes les annonces vues pendant ce passage, au prix actuel. Remplir `loyer`, `charges`, `str_ok` et `pleine_propriete` dès qu'une information fiable existe.
6. Lancer `python3 calcul.py AAAA-MM-JJ` depuis `veille-immo-sxm/`.
7. Écrire `rapport_AAAA-MM-JJ.md` (format ci-dessous), puis faire un commit et pousser.
8. Envoyer le résumé par courriel (voir le message de la tâche planifiée pour le destinataire).

## Sources
- Sites d'agences : realestatesxm.com, century21stmaarten.com / century21-stmaarten.com, andreurealty.com, sxmrealestate.com, oasislivingrealty.com, kwsintmaarten.com, remaxislandproperties.com, 7thheavenproperties.com, idr.sx, weilandgraf.com.
- Recherche web quand ces sites sont bloqués.
- Gmail : alertes des agences reçues dans les 7 derniers jours.

Règles :
- Si un site refuse l'accès, **ne pas le contourner** : pas de curl, de miroir ni de cache. Le noter dans le rapport et passer à la source suivante.
- **Ne jamais contacter une agence, un vendeur ou un propriétaire.**
- Ne jamais inventer de données : un champ inconnu reste vide et figure parmi les points de vigilance.

## Calcul et score (`calcul.py`)
- **Loyer nécessaire pour 5 % net** = (5 % × prix × 1,055 / 12 + charges mensuelles) / 0,8. C'est le loyer mensuel moyen à encaisser, après 20 % de frais de location, pour atteindre 5 % net.
- Si un loyer réel est connu : rendement brut = loyer × 12 / prix ; rendement net = (loyer × 12 × 0,8 − charges × 12) / (prix × 1,055).
- **Score sur 100** : loyer nécessaire ou rendement net réel 40, poids des charges 15, secteur 15, taille 10, location courte durée confirmée 10, pleine propriété confirmée 10. Location courte durée interdite : score 0.

## Format du rapport `rapport_AAAA-MM-JJ.md`
1. **Nouveautés et baisses de prix**, triées par score.
2. **Top 10 du stock**, trié par score.
3. Pour chaque bien : lien, secteur, prix, chambres et salles de bain, charges, loyer nécessaire, rendement réel s'il est connu, score, 2 points forts et 2 points de vigilance.
4. **Alertes** : sources inaccessibles, annonces retirées, prix incohérents.
5. **Rappels** (sans les présenter comme des conseils juridiques ou fiscaux) : pas de convention fiscale connue entre la France et Sint Maarten, vérifier le statut du terrain, l'assurance cyclone et le règlement de copropriété.

## Courriel hebdomadaire
- **Objet** : `Veille immo Sint Maarten – semaine du AAAA-MM-JJ`.
- **Corps**, en texte simple et en français : nouveautés et baisses de prix (nom, secteur, prix, score, lien), Top 5, alertes, chemin du rapport complet dans le dépôt.
- S'il n'y a aucune nouveauté, envoyer quand même le courriel avec la mention « aucune nouveauté cette semaine ».
