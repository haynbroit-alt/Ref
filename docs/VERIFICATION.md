# Registre de vérification des sources

*Mis à jour le 18 novembre 2026. Collecte : sous-agents Sonnet (règle de `CLAUDE.md`). Contrôle et décisions : Opus.*

**Statuts**
- **PRIMAIRE** : texte officiel lu, via Legal Data Hunter (EUR-Lex, Légifrance).
- **SECONDAIRE** : uniquement des résumés fiables.
- **NON TROUVÉ** : aucune source n'a été trouvée.

**Passes de vérification**
- **16 nov. 2026** : WebSearch seul (sites officiels bloqués) ; aucun point au statut primaire.
- **17 nov. 2026** : Legal Data Hunter, 10 appels réussis, puis HTTP 429 (limite de débit ou quota).
- **18 nov. 2026** : Legal Data Hunter, 18 appels du sous-agent et 2 appels de contrôle par Opus, sans erreur de quota. Opus a relu lui-même l'art. L.321-6 CPI et le point (41) de l'art. 1 du règlement 2024/1183.

| Point | Constat | Statut | Effet sur nos documents |
|---|---|---|---|
| CPC art. 1450 | « La mission d'arbitre ne peut être exercée que par une personne physique […]. Si la convention d'arbitrage désigne une personne morale, celle-ci ne dispose que du pouvoir d'organiser l'arbitrage. » (LEGIARTI000023450931, en vigueur depuis le 1er mai 2011 ; relu le 18 nov., seule version disponible, aucune version future indexée) | **PRIMAIRE** | Conclusion « NOVARYS ne peut pas être arbitre » confirmée |
| Décret 2026-741 | Source secondaire : JO du 7 août 2026, applicable au 1er janv. 2027 ; « centre d'arbitrage ou autre personne chargée par les parties d'organiser l'arbitrage ». **Absent de Legal Data Hunter** (recherche directe et recherche sur juil.–sept. 2026). La base contient pourtant d'autres décrets d'août 2026 (2026-752 du 6 août, 2026-779 du 13 août). Une PPL n° 3310 « portant adaptation de certaines dispositions relatives à l'arbitrage » a été déposée le 13 oct. 2026 (début de l'exposé des motifs lu ; rien sur ce décret) | SECONDAIRE | Formulation prudente ajoutée dans `ARBITRE.md`. **Aucun effet sur la décision**, qui repose sur l'art. 1450 en vigueur. À vérifier au JO avant toute citation externe |
| AI Act art. 85 | « any natural or legal person having grounds to consider that there has been an infringement […] may submit complaints to the relevant market surveillance authority » | **PRIMAIRE** | **Correction :** une plainte est ouverte à toute personne, mais son application aux obligations des modèles d'IA à usage général reste à confirmer |
| AI Act art. 89(2) | « Downstream providers shall have the right to lodge a complaint alleging an infringement of this Regulation » | **PRIMAIRE** | Conforme : plainte propre aux modèles à usage général réservée aux fournisseurs en aval |
| AI Act art. 101(1) | Amendes jusqu'à 3 % du chiffre d'affaires mondial ou 15 M€, le montant le plus élevé étant retenu | **PRIMAIRE** | Conforme |
| DGA art. 2(11)(b) | Exclusion : « services that focus on the intermediation of copyright-protected content » (liste ouverte : « at least ») | **PRIMAIRE** | Conforme |
| eIDAS art. 41 | (1) Un horodatage non qualifié reste recevable comme preuve. (2) Présomption d'exactitude de la date, de l'heure et de l'intégrité pour l'horodatage qualifié. Règlement 2024/1183, art. 1, point (41) : « in Article 41, paragraph 3 is deleted » ; la reconnaissance mutuelle de l'horodatage qualifié figure désormais au nouvel art. 24a(6) (CELEX 32024R1183) | **PRIMAIRE** (texte de 2014 et règlement modificatif ; pas de consolidé lu) | Conforme : nos documents ne s'appuient que sur les §§ 1 et 2, inchangés |
| CPI art. L.218-4 | Les services en ligne fournissent « tous les éléments d'information […] nécessaires à une évaluation transparente de la rémunération » (LEGIARTI000038826736) | **PRIMAIRE** | Conforme |
| CPI art. L.321-6 (OGI) | « Un organisme de gestion indépendant est une personne morale à but lucratif dont l'objet principal consiste à gérer le droit d'auteur ou les droits voisins […] pour le compte de plusieurs titulaires de droits […], qui n'est pas contrôlée, directement ou indirectement, par ces titulaires de droits. » Soumis à la commission de contrôle (L.327-1). Texte coupé en fin d'article par l'outil (LEGIARTI000033687844, en vigueur depuis le 24 déc. 2016) | **PRIMAIRE** | Conforme ; `ARBITRE.md` passé de R à V. L.321-7 à L.321-12 non relus : aucun de nos documents ne s'y appuie |
| Loi 71-1130 art. 54 ; Cass. crim. 21 mars 2017 (*Demander Justice*) | Texte cité par le CNB ; relaxe confirmée. La loi est indexée dans Legal Data Hunter (LEGITEXT000006068396), mais le texte renvoyé ne contient pas l'art. 54 | SECONDAIRE | Conforme ; défaut d'indexation de la base, relecture sur Légifrance à faire |
| Code GPAI, mesure 1.5 | Point de contact et mécanisme de plainte confirmés en paraphrase | SECONDAIRE | Formulation prudente maintenue |
| Modèle de résumé d'entraînement | Top 10 % des domaines par volume ; seuil PME non trouvé | SECONDAIRE | Seuil PME non cité |
| **OLG Hamburg, Kneschke c. LAION** | Réserve « pas démontrablement lisible par machine » (dépêche dpa) ; charge de la preuve non confirmée. **Décision absente de Legal Data Hunter** (référence et recherche, 18 nov.) | SECONDAIRE | Corrigé le 16 nov. dans `ARBITRE.md` ; inchangé |
| **Rb Amsterdam 2024** | Lecture « la réserve doit viser les robots concernés » = commentateurs ; appel pendant. **ECLI:NL:RBAMS:2024:6563 absent de Legal Data Hunter** (« Document not found », 18 nov.) | SECONDAIRE | Corrigé le 16 nov. partout ; inchangé |
| Licence IA de STIM | Attribution par un tiers neutre obligatoire, analyses mensuelles | SECONDAIRE | Conforme |
| Omnibus IA 2026/1744 | Annexe III repoussée au 2 déc. 2027 | SECONDAIRE | Conforme |
| Jeton `__usage_ai-training` | Bing l'applique au 1er févr. 2027 ; Google en 2027 | SECONDAIRE | Déjà marqué *reported* |
| Search Console « Search generative AI » | Déploiement mondial au 31 août, une seule source | SECONDAIRE | Déjà marqué *reported* |
| CMA, 3 juin 2026 | Délais de 6 mois (déc. 2026) et de 9 mois pour le niveau page (mars 2027), sources en conflit | SECONDAIRE | Conforme, avec réserve |

**Bilan de la passe du 18 nov.** Deux points passent au statut primaire : CPI L.321-6 et eIDAS après le règlement 2024/1183. Aucun point ne contredit nos conclusions. Le décret 2026-741 n'a pas été trouvé en source primaire. Il ne sert pas aux décisions, mais il ne faut pas le citer à l'extérieur sans l'avoir lu au JO.

**Restent en source secondaire.** Legal Data Hunter ne les contient pas ou les indexe mal. Il faut une autre source primaire, sans dépense :
- OLG Hamburg 5 U 104/24 (justiz.hamburg.de ou openjur.de) ;
- ECLI:NL:RBAMS:2024:6563 (uitspraken.rechtspraak.nl) ;
- loi 71-1130 art. 54 (Légifrance, version consolidée) ;
- décret 2026-741 (JO du 7 août 2026, sur Légifrance).

Ces sites étaient bloqués depuis l'environnement de recherche le 16 nov. Aucune nouvelle passe n'est programmée. La lecture d'un document téléchargé à la main suffirait pour chacun de ces quatre points.
