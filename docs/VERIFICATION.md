# Registre de vérification des sources

*Mis à jour le 17 novembre 2026. Collecte : sous-agents Sonnet (règle de `CLAUDE.md`). Contrôle et décisions : Opus.*

**Statuts**
- **PRIMAIRE** : texte officiel lu, via Legal Data Hunter (EUR-Lex, Légifrance).
- **SECONDAIRE** : uniquement des résumés fiables.
- **NON TROUVÉ** : aucune source n'a été trouvée.

**Passes de vérification**
- **16 nov. 2026** : WebSearch seul (sites officiels bloqués) ; aucun point au statut primaire.
- **17 nov. 2026** : Legal Data Hunter, 10 appels réussis, puis HTTP 429 (limite de débit ou quota).

| Point | Constat | Statut | Effet sur nos documents |
|---|---|---|---|
| CPC art. 1450 | « La mission d'arbitre ne peut être exercée que par une personne physique […]. Si la convention d'arbitrage désigne une personne morale, celle-ci ne dispose que du pouvoir d'organiser l'arbitrage. » (LEGIARTI000023450931, en vigueur depuis le 1er mai 2011) | **PRIMAIRE** | Conclusion « NOVARYS ne peut pas être arbitre » confirmée |
| Décret 2026-741 | JO du 7 août 2026, applicable au 1er janv. 2027 ; « centre d'arbitrage ou autre personne chargée par les parties d'organiser l'arbitrage » | SECONDAIRE | Conforme ; texte du décret non relu |
| AI Act art. 85 | « any natural or legal person having grounds to consider that there has been an infringement […] may submit complaints to the relevant market surveillance authority » | **PRIMAIRE** | **Correction :** une plainte est ouverte à toute personne, mais son application aux obligations des modèles d'IA à usage général reste à confirmer |
| AI Act art. 89(2) | « Downstream providers shall have the right to lodge a complaint alleging an infringement of this Regulation » | **PRIMAIRE** | Conforme : plainte propre aux modèles à usage général réservée aux fournisseurs en aval |
| AI Act art. 101(1) | Amendes jusqu'à 3 % du chiffre d'affaires mondial ou 15 M€, le montant le plus élevé étant retenu | **PRIMAIRE** | Conforme |
| DGA art. 2(11)(b) | Exclusion : « services that focus on the intermediation of copyright-protected content » (liste ouverte : « at least ») | **PRIMAIRE** | Conforme |
| eIDAS art. 41 | (1) Un horodatage non qualifié reste recevable comme preuve. (2) Présomption d'exactitude de la date, de l'heure et de l'intégrité pour l'horodatage qualifié | **PRIMAIRE** (texte de 2014) | Conforme ; version modifiée par le règlement 2024/1183 non relue |
| CPI art. L.218-4 | Les services en ligne fournissent « tous les éléments d'information […] nécessaires à une évaluation transparente de la rémunération » (LEGIARTI000038826736) | **PRIMAIRE** | Conforme |
| Loi 71-1130 art. 54 ; Cass. crim. 21 mars 2017 (*Demander Justice*) | Texte cité par le CNB ; relaxe confirmée | SECONDAIRE | Conforme ; relecture primaire à faire |
| CPI art. L.321-6 (OGI) | — | NON RELU (429) | Inchangé |
| Code GPAI, mesure 1.5 | Point de contact et mécanisme de plainte confirmés en paraphrase | SECONDAIRE | Formulation prudente maintenue |
| Modèle de résumé d'entraînement | Top 10 % des domaines par volume ; seuil PME non trouvé | SECONDAIRE | Seuil PME non cité |
| **OLG Hamburg, Kneschke c. LAION** | Réserve « pas démontrablement lisible par machine » (dépêche dpa) ; charge de la preuve non confirmée | SECONDAIRE ; non relu en primaire (429) | Corrigé le 16 nov. dans `ARBITRE.md` |
| **Rb Amsterdam 2024** | Lecture « la réserve doit viser les robots concernés » = commentateurs ; appel pendant | SECONDAIRE ; non relu en primaire (429) | Corrigé le 16 nov. partout |
| Licence IA de STIM | Attribution par un tiers neutre obligatoire, analyses mensuelles | SECONDAIRE | Conforme |
| Omnibus IA 2026/1744 | Annexe III repoussée au 2 déc. 2027 | SECONDAIRE | Conforme |
| Jeton `__usage_ai-training` | Bing l'applique au 1er févr. 2027 ; Google en 2027 | SECONDAIRE | Déjà marqué *reported* |
| Search Console « Search generative AI » | Déploiement mondial au 31 août, une seule source | SECONDAIRE | Déjà marqué *reported* |
| CMA, 3 juin 2026 | Délais de 6 mois (déc. 2026) et de 9 mois pour le niveau page (mars 2027), sources en conflit | SECONDAIRE | Conforme, avec réserve |

**Reste à relire en source primaire :**
- OLG Hamburg 5 U 104/24 ;
- ECLI:NL:RBAMS:2024:6563 ;
- CPI L.321-6 à L.321-12 ;
- loi 71-1130 art. 54 ;
- décret 2026-741 ;
- eIDAS consolidé.

Une nouvelle passe est programmée le 18 nov. 2026 à 03 h UTC.
