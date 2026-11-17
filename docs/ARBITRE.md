# NOVARYS, tiers neutre entre éditeurs et IA : leviers légaux, tests, décision

*16 novembre 2026. Aide à la décision, pas un avis juridique. Les statuts suivent la convention du dépôt :*
- ***V*** *: texte primaire relu ;*
- ***R*** *: source secondaire ;*
- ***U*** *: non vérifié.*

## 0. Verdict

**NOVARYS ne peut pas être « l'arbitre » au sens juridique, et ne doit pas chercher à l'être.**

**Ce que la loi interdit :**
- **Être arbitre.** En France, seule une personne physique peut arbitrer ; une société peut seulement *organiser* l'arbitrage (art. 1450 CPC, V : « Si la convention d'arbitrage désigne une personne morale, celle-ci ne dispose que du pouvoir d'organiser l'arbitrage »). Le décret 2026-741, applicable au 1er janvier 2027, consacre le « centre d'arbitrage » (R).
- **Donner des consultations juridiques personnalisées** (loi 71-1130, art. 54 ; jurisprudence *Demander Justice*, Cass. crim. 21 mars 2017, R).
- **Faire circuler des informations de prix entre éditeurs concurrents** (art. 101 TFUE).

**La position légale et inexploitée est celle de tiers de confiance de la preuve et de la mesure.** C'est l'infrastructure neutre et vérifiable par tous dont ont besoin ceux qui tranchent :
- les tribunaux arbitraux (comme celui prévu dans les engagements Google 22-D-13) ;
- le CRTC canadien, qui peut acheter une « assistance technique » (*Online News Act*, art. 36) ;
- l'AI Office, qui envoie ses premières demandes d'information depuis août 2026 (R) ;
- les sociétés de gestion (STIM impose déjà une attribution par un tiers neutre, R) ;
- les juges. Dans Kneschke c. LAION (OLG Hamburg, 10 déc. 2025), la réserve a été jugée, selon la dépêche dpa, « nicht nachweislich maschinenlesbar » (pas démontrablement lisible par machine), donc inopérante (R). La preuve datée de la lisibilité est décisive. *Correction : aucune source vérifiée n'énonce explicitement la règle de charge de la preuve que j'avais d'abord indiquée.*

**Décision : GO sur 4 briques neutres**, construites, testées et poussées. **NO-GO sur 5 autres**, faute de preuves ou par incompatibilité avec la neutralité (§ 4).

## 1. Ce que les tests ont prouvé

| Test | Résultat | Fichier |
|---|---|---|
| Valeur économique d'une information neutre (arbitrage à offre finale) | Écart d'offres calculé = prédiction de Farber à 0,01 % près. Diviser l'incertitude par 2 divise l'écart par 2. Probabilité de litige : 45 % → 17 % quand l'erreur d'estimation passe de 60 % à 7,5 % | `studies/arbitration_sim.py` |
| Les mesures actuelles s'accordent-elles ? | Non : le ratio crawl/visite d'un même fournisseur varie d'un facteur **3 à 6** selon la source (Cloudflare vs TollBit) | idem |
| Deux observateurs voient-ils la même réserve ? | Désaccord sur la *lisibilité même* du robots.txt pour **14,9 %** de 9 801 domaines du top 10k. **26 %** des fichiers comparables ont changé de statut pour au moins un agent IA en 5 mois | `studies/observer_agreement.py` |
| Registre neutre vérifiable à l'échelle du web | Voir le détail ci-dessous | `studies/registry_scale.py` |
| Preuve d'entraînement par canaris pré-enregistrés | Faux positifs **5,8 %** (seuil 5 %) même avec un biais de distribution. Le test naïf monte à **93 %** avec un décalage de 0,2 écart-type. Puissance égale à effet donné | `studies/canary_preregistration.py` |
| Intégrité du journal (preuves d'inclusion et de cohérence) | **7 598** vérifications, 0 échec, contre-tests de falsification compris. 50 tests automatisés passent | `tests/test_arbiter.py` |

**Détail du test de registre.** Le registre neutre tient sans difficulté à l'échelle du web :
- 998 497 domaines indexés en 7 secondes, pour environ 8,8 Mo compressés par instantané ;
- une preuve d'inclusion fait 640 octets et se vérifie en 0,011 ms ;
- la racine produite par le code du produit est **identique** à celle d'une implémentation indépendante ;
- la falsification d'un enregistrement est détectée ;
- la cohérence entre l'état à 900 000 enregistrements et le journal complet est vérifiée.

Deux défauts réels ont été trouvés et corrigés grâce aux tests :
- un double comptage du premier enregistrement du journal ;
- un vocabulaire non neutre (« violation ») dans le module de logs.

**Limites des tests :**
- la simulation économique repose sur des modèles stylisés ;
- l'expérience de laboratoire d'Ashenfelter et al. (*Econometrica* 1992) montre que l'arbitrage à offre finale *ne réduit pas à lui seul* le taux de litiges. C'est l'information partagée qui le fait, pas le mécanisme ;
- aucun modèle d'IA réel n'a été testé : les canaris montrent une propriété statistique, pas une détectabilité.

## 2. Les leviers et les quatre preuves

| Levier | Juridique | Technique | Commercial | Économique | Décision |
|---|---|---|---|---|---|
| **A. Journal public de transparence des réserves** | Kneschke (réserve « pas démontrablement lisible par machine », R) ; AI Act 53(1)(c) (« technologies de pointe ») ; Rb Amsterdam 2024 (lecture des commentateurs, appel pendant) ; eIDAS art. 41 (horodatage non qualifié recevable, présomption si qualifié) ; résolution PE du 10 mars 2026 et étude Commission du 13 juil. 2026 sur un registre européen (R, pas d'engagement) | Prouvé (§ 1) | Indirect : observateurs en désaccord (14,9 %), réserves changeantes (26 %). Concurrents : Liccium TDM·AI (ISCC, sur la liste de consultation de la Commission), Spawning (seul registre consulté par un fournisseur, Stability) | Coût quasi nul | **GO** |
| **B. Constat technique neutre** | Preuve libre entre commerçants (C. com. L.110-3, U) ; écrit électronique (C. civ. 1366, U) ; rapport factuel autorisé, conseil personnalisé interdit (loi 71-1130) | Prouvé : déterministe, même empreinte quel que soit le demandeur, vérifiable | Besoin illustré par Kneschke, la mesure 1.5 du code GPAI (contact et plaintes, R/U), l'art. L.218-4 CPI (obligation de fournir « tous les éléments d'information […] nécessaires à une évaluation transparente de la rémunération », V) et la loi droits voisins 2026 (CMP du 4 nov. 2026, R) | Coût marginal nul | **GO** |
| **C. Mesure d'usage neutre et agrégée** | Canada art. 36/38/86 ; Australie, taxe NBI en vigueur depuis le 27 août 2026 (vérification des compensations, R/V) ; Indonésie Perpres 32/2024 art. 7(3) (V) ; STIM (attribution tierce obligatoire, R). Pas d'échange de prix (art. 101 TFUE) | Métriques calculées depuis les logs ; agrégat k-anonyme (k ≥ 5) ; engagement par empreinte | Aucun organisme n'accrédite aujourd'hui la mesure des usages IA (MRC, Médiamétrie, ACPM : niche ouverte, R) | Valeur = coûts de litige évités (≈ 2,8 points de valeur de contrat dans la simulation) | **GO** (méthode v0.1) |
| **D. Pré-enregistrement de canaris** | Contenu propre ; seule la reproduction a été acceptée en justice (GEMA, LG München I, 11 nov. 2025) ; aucun tribunal n'a encore accepté de statistiques d'appartenance aux données d'entraînement | Propriété statistique prouvée ; détection réelle dépendante de l'accès au modèle (log-probabilités ou poids) | Aucun service neutre de ce type identifié | Coût quasi nul | **GO limité** (outil de preuve, pas de promesse de détection) |
| E. Être arbitre | Interdit à une personne morale (CPC 1450) | — | — | — | **NO-GO** |
| F. Centre d'arbitrage ou de médiation | Licite (CPC 1450, décret 2026-741, médiation B2B ouverte) ; un outil d'IA d'aide à la résolution des litiges serait à haut risque (AI Act annexe III 8(a), au 2 déc. 2027 via l'Omnibus 2026/1744, R) | Pas un problème logiciel | Google a déjà choisi CEDR pour la médiation DMA 6(12) (R) ; les plateformes refusent ou contournent (Meta, Danemark, U) ; aucune réputation | Arbitres, règlement, avocats : pas à 0 € | **NO-GO maintenant**, option stratégique |
| G. Mandataire de licences ou OGI | Licite en organisme de gestion indépendant (L.321-6 CPI, R ; directive 2014/26) | — | — | — | **NO-GO** : incompatible avec la neutralité, risque d'entente |
| H. Indice de conformité des crawlers par sites-pièges | Licite sur nos propres domaines ; risque de dénigrement à encadrer | Méthode conçue (environ 865 événements par fournisseur pour ±2 points) | Fort intérêt potentiel | Domaines et hébergement : budget > 0 | **Différé** |
| I. Contrôle croisé des résumés d'entraînement (AI Act 53(1)(d)) | Le modèle impose le top 10 % des domaines (R) ; publication inégale (5 à 78 résumés selon les sources, U) | Données inaccessibles ici | — | — | **Différé** (collecte à confier à Haiku quand le réseau le permettra) |

## 3. Ce qui a été construit

Tout est déterministe, sans apprentissage automatique, et se vérifie hors ligne.

- **`novarys/transparency.py`** : journal append-only (hachage RFC 9162), preuves d'inclusion et de cohérence, tête d'arbre ancrable par horodatage RFC 3161.
  - `novarys tlog …` et `novarys check preuve.json`.
- **`novarys/constat.py`** : constat technique daté.
  - Contenu : signaux publiés, lecture RFC 9309 et parseur ancien, activité des robots, engagement public, dispositions applicables *pour référence*, limites.
  - Le demandeur reste hors de l'empreinte, et le constat est refusé s'il contient un vocabulaire de conclusion juridique.
  - `novarys snapshot …`, `novarys constat …`, `novarys constat-verify …`.
- **`novarys/metering.py`** : méthode `novarys-metering/0.1`.
  - Rapport par éditeur, engagement par empreinte (l'identifiant de l'éditeur n'est publié que haché), agrégat k-anonyme sans aucune donnée de prix.
  - `novarys meter report|commit|aggregate …`.
- **`novarys/canary.py`** : création de paires, tirage secret, engagement public, révélation vérifiable, test apparié exact jusqu'à 20 paires (Monte-Carlo au-delà).
  - `novarys canary create|verify|test …`.

## 4. Garde-fous juridiques inscrits dans le code

1. **Neutralité vérifiable.** Même entrée, même constat, quel que soit le demandeur. Le journal permet à chacun de vérifier qu'aucune donnée n'a été réécrite.
2. **Des faits, pas de conclusions.** Le constat se bloque s'il contient « infraction », « illicite », « violation », etc. Les dispositions de droit sont listées sans être appliquées au cas (loi 71-1130).
3. **Hors du champ « système d'IA ».** Les règles sont définies par des humains (AI Act art. 3(1) et considérant 12, lignes directrices du 6 février 2025, R). Toute brique d'apprentissage automatique future destinée à aider un médiateur ou un arbitre serait à haut risque (annexe III 8(a)), avec une conformité exigible au 2 décembre 2027.
4. **Pas d'échange d'informations sensibles.** Aucun prix, et des agrégats seulement à partir de 5 éditeurs (art. 101 TFUE, L.420-1 C. com.).
5. **RGPD.** Aucune IP humaine en sortie, et les identifiants d'éditeurs ne sont publiés que hachés.
6. **Aucune prétention officielle.** Pas de « registre européen ». La plainte propre aux modèles d'IA à usage général est réservée aux fournisseurs en aval (art. 89(2), V). L'art. 85 permet à « toute personne physique ou morale » de saisir l'autorité de surveillance du marché (V), mais son application aux obligations de ces modèles, supervisées par l'AI Office, reste à confirmer. *Correction du 17 nov. 2026 : j'avais écrit à tort qu'aucune plainte n'était ouverte aux ayants droit.*

## 5. Gouvernance de neutralité proposée (à valider par avocat)

- **Entité séparée de toute offre « côté éditeur »**, comme l'impose l'art. 12 du DGA pour les intermédiaires de données. Le DGA exclut toutefois les « services that focus on the intermediation of copyright-protected content » (art. 2(11)(b), V) et n'est donc pas obligatoire ici.
- **Méthodes publiques et versionnées**, révisées par un comité paritaire éditeurs / fournisseurs d'IA sur le modèle des comités d'audience (JIC), avec un droit de réponse avant publication de toute mesure.
- **Tarification bilatérale publiée et déclaration des intérêts**, par analogie avec l'obligation de révélation de l'arbitre (art. 1456 CPC).
- **Ancrage des têtes d'arbre** auprès d'un prestataire de confiance qualifié eIDAS, pour la présomption d'exactitude de la date, de l'heure et de l'intégrité, réservée à l'horodatage qualifié (art. 41(2), V, texte de 2014). Un horodatage non qualifié reste recevable (art. 41(1), V). Constats décisifs doublés d'un constat de commissaire de justice (NF Z67-147).

## 6. Modèle économique (qui paie, pourquoi)

| Payeur | Service | Justification |
|---|---|---|
| Éditeur | Instantanés horodatés + constats | Prouver une réserve lisible à la date de l'usage (Kneschke). Prix indicatif : 49 €/mois et par site (offre Pro existante) |
| Fournisseur d'IA | Consultation du journal avec preuves, pour documenter la mesure 1.3 du code GPAI et l'art. 53(1)(c) | Demandes d'information de l'AI Office depuis août 2026 ; amendes jusqu'à 3 % (art. 101, V) |
| Société de gestion, collectif, régulateur | Mesure d'usage (rapports, agrégats) et assistance technique | Modèle STIM ; Canada art. 36 ; Australie NBI ; Inde (organisme collecteur CRCAT, si adopté) |
| Arbitres et médiateurs (plus tard) | Dossiers de preuve communs aux deux parties | Simulation : l'information partagée réduit écart d'offres et litiges |

**Ordre de grandeur pour un contrat stratégique.** Si l'information partagée évite environ 2,8 % de la valeur d'un accord de 20 M€/an (ordre de grandeur Amazon–NYT), le gain est d'environ 560 k€/an par accord. Un contrat de 250 k€ à 1 M€ sur 3 ans pour un collectif reste donc défendable.

C'est un calcul de modèle : **aucun acheteur n'a confirmé**, et aucun contact n'a eu lieu sans votre accord.

## 7. Calendrier (opportunités datées)

| Date | Événement |
|---|---|
| Depuis le 2 août 2026 | Pouvoirs d'amende de l'AI Office sur les modèles d'IA à usage général |
| Depuis le 27 août 2026 | Taxe australienne NBI |
| Nov. 2026 | Loi française sur l'effectivité des droits voisins (pouvoirs de l'Arcom, votes finaux annoncés pour les 12 et 19 nov.) |
| En attente | Arrêt CJUE C-250/25 (conclusions de l'avocat général du 3 nov. 2026) |
| 1er janv. 2027 | Décret 2026-741 (centres d'arbitrage) |
| Mars 2027 | Exclusion des AI Overviews page par page imposée par la CMA |
| 2 déc. 2027 | Haut risque, annexe III |

## 8. Risques

- Un registre officiel européen géré par l'EUIPO, si la Commission y donne suite, en concurrence directe.
- Liccium TDM·AI déjà sur la liste des protocoles.
- Les plateformes refusent les tiers : Google a choisi CEDR, et aurait refusé un médiateur au Danemark (U).
- Les fournisseurs d'IA peuvent ignorer un journal qu'ils n'ont pas co-gouverné.
- La valeur probante d'un horodatage non qualifié reste à l'appréciation du juge.
- La formule de mesure doit être acceptée par les deux côtés pour valoir « monnaie commune ».

## 9. Ce qui exige votre autorisation

Le dossier de pilote est prêt en brouillon, non envoyé, dans [`docs/pilote/`](pilote/README.md) : proposition, méthode normative, charte de gouvernance, données, mode d'emploi répété par `examples/pilot_demo.py`, et projets de messages.

1. Publier le journal et la méthode `novarys-metering/0.1`, ce qui en fait des engagements publics.
2. Approcher un collectif (DVP, STIM, CJC canadien) et un fournisseur d'IA pour co-gouverner la méthode. Critère d'abandon : aucun des deux côtés n'accepte un pilote en 3 mois.
3. Choisir un prestataire de confiance qualifié et un commissaire de justice partenaire. C'est payant.
4. Consulter un avocat sur les 10 questions ouvertes (statut d'organisme de gestion indépendant, plainte AI Office, art. 6(3) AI Act, DGA, logs et RGPD, gouvernance).
5. L'outil juridique Legal Data Hunter a atteint sa limite gratuite. Je n'ai rien acheté : faute de budget, la vérification des textes primaires reprend après la remise à zéro du quota (17 nov. 2026, 02 h 45 UTC).

## 10. Auto-audit

**Solide :**
- les propriétés cryptographiques et statistiques testées ;
- les mesures de désaccord entre observateurs ;
- la qualification juridique « pas arbitre, mais tiers de la preuve ».

**Fragile :**
- beaucoup de textes ne sont pas relus en source primaire (statuts R et U) ;
- les modèles économiques sont stylisés ;
- l'échantillon de 362 fichiers est biaisé ;
- aucune preuve de volonté de payer.

**Non fait :**
- l'index de pièges ;
- le contrôle croisé des résumés d'entraînement ;
- les tests sur de vrais logs et de vrais modèles ;
- une gouvernance validée par avocat.

## 11. Sources principales

**Droit**
- AI Act : https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689
- Omnibus 2026/1744 : https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32026R1744
- Règlement d'exécution 2026/1755 : https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32026R1755
- Modèle de résumé des données d'entraînement : https://digital-strategy.ec.europa.eu/en/faqs/template-general-purpose-ai-model-providers-summarise-their-training-content
- Premières mesures d'exécution : https://www.matheson.com/insights/the-european-commissions-first-use-of-ai-act-enforcement-powers/
- Décret 2026-741 : https://www.jonesday.com/en/insights/2026/08/decree-2026741-france-takes-first-step-in-modernizing-arbitration-law
- Décision 24-D-03 de l'Autorité de la concurrence : https://www.autoritedelaconcurrence.fr/sites/default/files/integral_texts/2024-03/24d03vf.pdf
- Loi sur les droits voisins : https://siecledigital.fr/2026/11/05/google-meta-et-les-autres-plateformes-bientot-davantage-contraints-de-remunerer-la-presse/
- Médiation Google DMA (CEDR) : https://www.cedr.com/mediation-services/schemes/platform-to-business-services/the-google-search-mediation-scheme
- Résolution du Parlement européen : https://communia-association.org/2026/03/10/parliament-adopts-ini-report-on-ai-and-copyright-no-clear-path-forward/
- Étude sur un registre européen : https://www.pinsentmasons.com/out-law/news/ai-opt-out-registry-content-creators-backed-new-study
- Online News Act (Canada) : https://laws-lois.justice.gc.ca/eng/acts/O-9.3/
- Perpres 32/2024 (Indonésie) : https://peraturan.go.id/id/perpres-no-32-tahun-2024
- News Media Bargaining Charge Act 2026 (Australie) : https://www.legislation.gov.au/Details/C2026A00078
- Licence IA de STIM : https://www.cisac.org/Newsroom/society-news/stim-launches-worlds-first-collective-ai-music-licence

**Jurisprudence**
- Kneschke c. LAION : https://cm.twobirds.com/en/insights/2025/germany/higher-regional-court-hamburg-confirms-ai-training-was-permitted-(kneschke-v,-d-,-laion)
- GEMA c. OpenAI : https://www.taylorwessing.com/de/insights-and-events/insights/2025/11/gema-v-openai

**Science**
- Duan et al. : https://arxiv.org/abs/2402.07841
- Das, Zhang, Tramèr : https://arxiv.org/abs/2406.16201
- Zhang et al., SaTML 2025 : https://arxiv.org/abs/2409.19798
- Maini et al. : https://arxiv.org/abs/2406.06443
- Meeus et al. : https://arxiv.org/abs/2402.09363
- Rastogi et al. (STAMP) : https://proceedings.mlr.press/v267/rastogi25a.html
- Kim et al., IMC 2025 : https://arxiv.org/abs/2505.21733
- Liu et al., IMC 2025 : https://arxiv.org/abs/2411.15091

**Économie**
- Farber, 1980 : https://econpapers.repec.org/RePEc:sae:jocore:v:24:y:1980:i:4:p:683-705
- Ashenfelter et al., 1992 : https://www.econometricsociety.org/publications/econometrica/1992/11/01/experimental-comparison-dispute-rates-alternative-arbitration

**Standards**
- RFC 9162 (Certificate Transparency 2.0) : https://www.rfc-editor.org/rfc/rfc9162
- RFC 3161 : https://www.rfc-editor.org/rfc/rfc3161
