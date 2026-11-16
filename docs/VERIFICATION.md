# Registre de vérification des sources

*Mis à jour le 16 novembre 2026. Collecte : sous-agent Sonnet (règle de `CLAUDE.md`). Contrôle et décisions : Opus.*

**Statuts**
- **PRIMAIRE** : texte officiel lu.
- **SECONDAIRE** : uniquement des résumés fiables (cabinets, presse spécialisée, pages institutionnelles non ouvertes).
- **NON TROUVÉ** : aucune source n'a été trouvée.

Aucun point n'est encore au statut PRIMAIRE, car le réseau du conteneur bloque Légifrance, EUR-Lex et les sites des juridictions. Une relecture en source primaire via Legal Data Hunter est programmée après le rétablissement du quota gratuit, le **17 nov. 2026 à 03 h UTC**.

| Point | Constat | Statut | Effet sur nos documents |
|---|---|---|---|
| CPC art. 1450 (arbitre = personne physique ; une personne morale ne fait qu'organiser) | Retrouvé seulement dans le projet de décret de déc. 2025 | SECONDAIRE | Conclusion maintenue (règle constante depuis la réforme de 2011), à confirmer |
| Décret 2026-741 | JO du 7 août 2026, entrée en vigueur le 1er janv. 2027. « Centre d'arbitrage ou autre personne chargée par les parties d'organiser l'arbitrage » (art. 1450, 1452-1457) | SECONDAIRE | Conforme |
| Loi 71-1130 art. 54 ; Cass. crim. 21 mars 2017 (*Demander Justice*) | Texte cité par le CNB ; relaxe confirmée, pas d'assistance ni de représentation | SECONDAIRE | Conforme (la chambre est à vérifier sur Judilibre) |
| AI Act art. 89(2) | Droit de plainte réservé aux **fournisseurs en aval** | SECONDAIRE | Conforme : pas de droit de plainte pour les ayants droit |
| AI Act art. 85 | Seul le considérant 170 a été retrouvé, pas la lettre de l'article | SECONDAIRE | Inchangé (déjà marqué incertain) |
| Code GPAI, mesure 1.5 | Point de contact et mécanisme de plainte confirmés en paraphrase. La formule « représentants autorisés » n'a pas été trouvée mot pour mot | SECONDAIRE | Formulation à garder prudente |
| Modèle de résumé d'entraînement (24 juil. 2025) | Top 10 % des domaines par volume confirmé ; seuil PME non trouvé | SECONDAIRE / NON TROUVÉ | Nous ne citons pas le seuil PME |
| **OLG Hamburg, Kneschke c. LAION** | Appel rejeté ; réserve « pas démontrablement lisible par machine » (dépêche dpa) ; usage couvert aussi par le § 60d ; recours devant le BGH ouvert. **Aucune source ne confirme la charge de la preuve** | SECONDAIRE / NON TROUVÉ | **Corrigé** dans `ARBITRE.md` |
| **Rb Amsterdam 2024** | Robots.txt ne nommant que certains bots ; robot en cause jugé non exclu ; lecture « la réserve doit viser les robots concernés » = commentateurs ; appel pendant | SECONDAIRE | **Corrigé** dans `README.md`, `RAPPORT.md`, `ARBITRE.md`, la base juridique et le texte du constat `NAMED_BOTS_ONLY` |
| Licence IA de STIM | Attribution par un tiers neutre obligatoire (FAQ STIM), analyses mensuelles, Sureel prestataire préféré | SECONDAIRE | Conforme |
| DGA art. 2(11)(b) | Exclusion des services centrés sur l'intermédiation de contenus protégés | SECONDAIRE | Conforme |
| Omnibus IA 2026/1744 | Annexe III repoussée au 2 déc. 2027 ; annexe I au 2 août 2028 | SECONDAIRE | Conforme |
| eIDAS art. 41 | 41(1) non-discrimination ; 41(2) présomption pour l'horodatage qualifié (texte UK retenu de 2014) | SECONDAIRE | Conforme |
| Jeton `__usage_ai-training` | Draft Kelley (Anthropic) ; Bing l'applique au 1er févr. 2027 ; annonce le 30 oct. 2026 ; Google en 2027 (selon les sources) | SECONDAIRE | Conforme (déjà marqué *reported*) |
| Contrôle Search Console « Search generative AI » | Réglage au niveau du domaine ; déploiement mondial au 31 août une seule source | SECONDAIRE | Déjà marqué *reported* |
| CMA, 3 juin 2026 | Délais en conflit : 6 mois (déc. 2026) et 9 mois pour le niveau page (mars 2027) | SECONDAIRE | Conforme à nos dates, avec réserve |
