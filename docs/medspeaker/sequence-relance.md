# Séquence de relance MedSpeaker

Référence unique pour les agents `medspeaker-relances` et `medspeaker-email-cadeau`. Consolide les deux docs Drive « MedSpeaker_Scripts_Prospection » (27/08/2026) et « Scripts de Prospection - MedSpeaker » (28/08/2026).

| Jour | Canal | Action | Condition |
| --- | --- | --- | --- |
| J0 | Email | Email initial « Une question rapide sur votre site » | Adresse connue |
| J0 | Téléphone puis email | Appel secrétariat puis email « cadeau » dans l'heure | Uniquement si un article ou audit existe déjà pour ce praticien |
| J+3 | LinkedIn | Relance courte, ou message de suivi si la connexion vient d'être acceptée | Pas de réponse |
| J+7 | Email | Email de relance en « Re: » | Pas de réponse |
| J+14 | Téléphone | Appel au secrétariat, dernier recours | Pas de réponse aux deux relances |
| Après réponse | Selon la réponse | Sortie de séquence, notes dans la feuille | Colonne « Réponse » renseignée |

## Modèles

### Email initial

Objet : Une question rapide sur votre site

Bonjour Docteur [Nom],

Je me permets une question rapide : qui s'occupe aujourd'hui de votre site et de son contenu ?

Je travaille avec des praticiens en [médecine et chirurgie esthétiques / dentisterie esthétique / greffe capillaire], et j'ai plusieurs services qui pourraient vous intéresser. Ça vous dirait qu'on échange 15 minutes cette semaine ?

https://calendar.app.google/nGHNJYZUcua1S7ndA

Sasha Vuillemin — https://medspeaker.netlify.app/

### Relance LinkedIn (J+3)

Bonjour Docteur [Nom], je vous ai écrit par email au sujet de votre site. Avez-vous eu l'occasion d'y jeter un œil ? Question rapide : qui s'occupe aujourd'hui de son contenu ?

### Message de suivi LinkedIn (connexion acceptée, pas d'email envoyé)

Bonjour Docteur [Nom], merci pour la connexion. Question rapide : qui s'occupe aujourd'hui de votre site et de son contenu ? J'ai plusieurs services qui pourraient vous intéresser, ça vous dirait qu'on échange ? https://calendar.app.google/nGHNJYZUcua1S7ndA

### Email de relance (J+7)

Objet : Re: Une question rapide sur votre site

Bonjour Docteur [Nom],

Je reviens vers vous suite à mon email du [date]. Je fais court : qui s'occupe aujourd'hui du contenu de votre site ?

Je travaille avec des praticiens en [spécialité] sur du contenu sourcé (PubMed) et rédigé dans le respect des règles de l'Ordre. Si un échange de 15 minutes vous tente : https://calendar.app.google/nGHNJYZUcua1S7ndA

Bonne journée,

Sasha Vuillemin — https://medspeaker.netlify.app/

### Email « cadeau » (après appel ou accord)

Objet : Suite à notre échange / Dossier de recherche - Dr [Nom]

Bonjour Docteur [Nom],

Comme convenu, voici l'article rédigé pour vous sur [Sujet]. Il est sourcé via notre outil MedSeeker (PubMed, ClinicalTrials) et rédigé sans publicité ni promesse de résultat, conformément aux règles de l'Ordre.

Vous trouverez le document en pièce jointe. N'hésitez pas à l'utiliser pour votre site.

Bonne lecture,

Sasha Vuillemin — MedSpeaker

## Règles fixes

- Rien n'est envoyé par un agent. Les agents produisent des brouillons, l'envoi se fait à la main depuis Gmail et LinkedIn.
- Aucune pièce jointe n'est promise si elle n'existe pas dans Drive.
- Aucune adresse email n'est inventée.
- Après chaque envoi manuel, reporter la date dans la feuille `Prospection_LISTE_ACTION` (colonnes Email envoyé, LinkedIn, Appel).
