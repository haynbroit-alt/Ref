# Proposition de pilote : une mesure commune et des preuves datées entre éditeurs et fournisseurs d'IA

> **BROUILLON, NON ENVOYÉ.**

## 1. Le problème que le pilote veut résoudre

Les éditeurs et les fournisseurs d'IA n'ont aujourd'hui **ni faits communs ni mesure commune** :

- **Les mesures divergent.** Le ratio pages explorées / visites renvoyées d'un même fournisseur varie d'un facteur **3 à 6** selon la source publiée (Cloudflare, TollBit).
- **Les observateurs ne voient pas la même chose.** Deux recensements indépendants du même top 10 000 ne s'accordent pas sur la lisibilité même du robots.txt pour **14,9 %** des domaines.
- **Les réserves changent.** 26 % des fichiers comparables ont changé de statut pour au moins un robot IA en cinq mois (`studies/observer_agreement.py`).
- **La preuve à date compte devant le juge.** Dans *Kneschke c. LAION* (OLG Hamburg, 10 déc. 2025), la réserve a été jugée, selon la presse, « pas démontrablement lisible par machine ».
- **Le cadre réglementaire se resserre.** Depuis le 2 août 2026, l'AI Office peut sanctionner les fournisseurs de modèles d'IA à usage général sur leur politique de droit d'auteur (AI Act art. 53(1)(c), art. 101).

Notre simulation d'arbitrage à offre finale montre qu'une information partagée réduit l'écart des offres et la probabilité de litige (45 % → 17 % selon l'erreur d'estimation). L'arbitrage à offre finale ne réduit pas, à lui seul, les litiges (Ashenfelter et al., 1992).

## 2. Ce que le pilote teste

1. **Faisabilité opérationnelle.** Des éditeurs tiennent un registre daté de leurs signaux (robots.txt, TDMRep) et produisent un rapport mensuel de mesure, sans transmettre leurs logs.
2. **Acceptabilité bilatérale.** Un fournisseur d'IA et un collectif d'éditeurs acceptent, après revue, la même méthode de mesure (v0.1 → v0.2).
3. **Validité de la mesure.** Les comptages NOVARYS des robots vérifiés concordent avec les comptages internes du fournisseur, si celui-ci accepte de les partager en agrégé.
4. **Utilité.** Au moins une utilisation réelle : référence de négociation, dossier de plainte au titre de la mesure 1.5 du code de pratique GPAI, ou pièce d'une procédure.

## 3. Participants visés (à confirmer, aucun contact pris)

- **Côté éditeurs :** 10 à 30 sites issus d'un collectif de presse (en France, par exemple l'organisme de gestion des droits voisins de la presse ou un syndicat d'éditeurs).
- **Côté IA :** un fournisseur signataire du code de pratique GPAI, qui dispose déjà d'un point de contact « droit d'auteur » (mesure 1.5, *reported*).
- **Pas de régulateur** dans le pilote, sauf accord des deux côtés.

## 4. Ce que chacun apporte

| Partie | Apporte | Ne transmet pas |
|---|---|---|
| Éditeur | Un instantané quotidien de ses signaux ; un rapport mensuel produit **chez lui** avec `novarys` | Ses logs bruts, ses données personnelles, ses prix |
| Fournisseur d'IA | Confirmation de ses agents et plages IP (déjà publics) ; un relecteur de la méthode ; en option, des comptages agrégés par domaine participant | Ses données d'entraînement, ses prix |
| NOVARYS (opérateur) | Outils libres, journal public de transparence, agrégats k-anonymes, constats sur demande, animation du comité de méthode | Aucune position dans les négociations ; aucun conseil juridique |

## 5. Critères de succès (mesurables)

| Critère | Cible |
|---|---|
| Sites tenant un instantané quotidien pendant 90 jours | ≥ 90 % des sites inscrits |
| Preuves d'inclusion et de cohérence vérifiables par un tiers | 100 % |
| Reproductibilité : deux recalculs indépendants d'un rapport | Empreintes SHA-256 identiques |
| Écart entre comptage NOVARYS et comptage du fournisseur (robots vérifiés) | ≤ 10 %, si le fournisseur partage ses comptages |
| Méthode v0.2 approuvée par les deux collèges du comité | Oui ou non |
| Usage réel documenté | ≥ 1 |

## 6. Critères d'abandon

- Aucun fournisseur d'IA n'accepte de relire la méthode dans les 3 mois suivant la première approche.
- Moins de 50 % des sites tiennent leurs instantanés après 6 semaines.
- Désaccord persistant sur une métrique centrale après deux cycles de revue.

## 7. Calendrier (12 semaines)

| Semaines | Étapes |
|---|---|
| S0–S2 | Accords (protocole de pilote, confidentialité, et contrat de sous-traitance si un hébergement est retenu) ; audit initial de chaque site (`novarys audit`) ; récupération des fichiers de plages IP |
| S2–S10 | Instantanés quotidiens ; deux cycles mensuels de rapports et d'agrégats ; constats à la demande |
| S10–S12 | Revue de la méthode par le comité (v0.2) ; rapport final public si les deux collèges l'acceptent |

## 8. Coûts

- **Pour les participants : 0 €.** Les outils sont libres et tournent chez eux, et le journal public peut être tenu dans un dépôt Git.
- **Options payantes, à chiffrer et à décider par le titulaire du projet :**
  - horodatage qualifié eIDAS des têtes d'arbre ;
  - constats de commissaire de justice pour les pièces décisives ;
  - relecture juridique par un avocat.

## 9. Ce que le pilote ne fait pas

- Pas de négociation de prix, pas d'échange d'informations tarifaires.
- Pas de décision sur un litige : arbitres, médiateurs et juges restent seuls compétents.
- Pas d'affirmation sur l'entraînement d'un modèle. Les canaris pré-enregistrés sont proposés en option expérimentale, et leur pouvoir de détection dépend de l'accès au modèle.
