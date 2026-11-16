# NOVARYS OMNISEARCH — rapport de recherche, décision et construction

*16 novembre 2026. Aide à la décision, pas un avis juridique.*

## 0. Verdict

1. **Le suivi de visibilité dans les moteurs IA (« GEO/AEO ») est saturé.** Environ 604 M$ y ont été levés et les prix d'entrée sont tombés à 50–99 $/mois (HubSpot, Semrush). Les leviers « page » vendus par ces outils ont des preuves scientifiques faibles ou contredites. En faire un clone serait une erreur : **NO-GO**.
2. **L'opportunité réelle est ailleurs : la conformité des droits d'usage IA.** Il s'agit de dire, prouver et faire respecter ce que les IA peuvent faire d'un site, avec un effet juridique mesuré par marché. Personne ne combine aujourd'hui quatre fonctions :
   - compilation multi-protocoles d'une intention unique ;
   - audit de l'effet juridique dans plusieurs juridictions ;
   - vérification de l'interprétation par les vrais parseurs des crawlers ;
   - preuve horodatée.

   Les quatre preuves ont été évaluées au §5 : trois sont solides, la preuve commerciale ne l'est qu'indirectement. **GO limité :** un moteur gratuit et open-core, construit et testé ici. Les briques payantes attendent une validation client, qui nécessite votre autorisation.
3. **Résultats mesurés :**
   - 100 % de conformité à la suite de tests de référence de Google, contre 90,1 % pour le parseur Python standard et 91,5 % pour celui de Scrapy ;
   - une étude originale sur 998 497 domaines et 30 marchés ;
   - 40 tests automatisés passent.

## 1. OBSERVER — méthode et limites

**Quatre équipes de recherche ont travaillé en parallèle :** droit sur 30 marchés, marché et concurrence, science/standards/brevets, registre des agents IA.

**Les limites, déclarées d'emblée :**
- Le réseau du conteneur bloquait la plupart des sites primaires (EUR-Lex, gov.uk, sites des fournisseurs). Une grande partie des faits vient donc de résumés de moteur de recherche des pages citées. Ils sont étiquetés *reported*, et *unverified* quand ils n'ont pas pu être recoupés.
- La recherche de brevets n'a pas pu être faite.
- Sept marchés ne sont pas couverts juridiquement : Mexique, Indonésie, Arabie saoudite, Turquie, Émirats, Argentine, Afrique du Sud.

**Les données mesurées par moi-même** proviennent de deux jeux de données publics sur GitHub :
- le recensement robots.txt « AI-Crawler Blocking Index » de Crawlora (Tranco top 1M, 20 juin 2026, CC BY 4.0) ;
- l'étude « robots.txt AI allow-list » de G. Abdullah (Tranco top 10k, 6 novembre 2026), dont les résultats sont sous CC BY 4.0 et dont les fichiers bruts ne sont pas redistribués ici.

## 2. COMPRENDRE — le modèle du monde

La recherche se déplace des liens vers des réponses générées. Les chiffres :
- Pew (juillet 2025) : avec une AI Overview, 8 % de clics contre 15 % sans.
- Ahrefs (février 2026) : −58 % de CTR en position 1.
- SparkToro (2026) : 68 % de recherches sans clic.
- Reuters Institute/Chartbeat : −33 % de trafic Google vers les éditeurs en un an.

Trois marchés se sont formés :

| Marché | Acteurs | État |
|---|---|---|
| Visibilité dans les réponses IA | Profound (1,8 Md$ de valorisation, septembre 2026), Peec AI (20 M$ d'ARR), Scrunch (racheté par Sitecore), Semrush (racheté par Adobe), Ahrefs, HubSpot | Saturé ; la mesure elle-même est peu fiable (les listes de marques se répètent < 1 % du temps selon SparkToro/Gumshoe) |
| Contrôle et monétisation des crawlers | Cloudflare (Content Signals sur 3,8 M de domaines), TollBit (3 000+ éditeurs), Dark Visitors (29 $/mois), RSL Collective (1 500+ organisations), Microsoft Publisher Content Marketplace | Fragmenté ; Cloudflare ne vaut que pour les sites derrière son réseau |
| Licences de contenu | News Corp–OpenAI (≈ 250 M$ sur 5 ans), Amazon–NYT (20–25 M$/an), Bartz c. Anthropic (règlement de 1,5 Md$) | Le marché des contrats existe, celui des preuves non |

## 3. CONFRONTER — les hypothèses testées contre les faits

| Hypothèse de départ | Verdict | Preuve |
|---|---|---|
| Un « score GEO » de page fait gagner des citations IA | **Rejetée** | C-SEO Bench (NeurIPS 2025) : méthodes « largement inefficaces », jeu à somme nulle. AutoGEO (ICLR 2026) : les règles ne se transfèrent pas d'un moteur à l'autre. Les effets du schema et des FAQ disparaissent à effets fixes domaine. L'effet de +40 % de GEO (KDD 2024) a été obtenu sur un moteur simulé |
| Un vérificateur robots.txt suffit | **Rejetée** | Il en existe des gratuits (Abdullah, Dark Visitors). Le vrai problème est l'effet juridique et l'interprétation |
| Les sites expriment correctement leur refus d'entraînement | **Fausse** (données ci-dessous) | §4, D1 |
| robots.txt est lu de la même façon par tous | **Fausse** | §4, D3 |

## 4. HYPOTHÈSES — découvertes avec preuves

**D1. L'intention d'opt-out est mal implémentée, surtout là où elle a un effet légal.**

Mesure NOVARYS sur 998 497 domaines (`studies/results/market_gap.md`), restreinte aux sites qui bloquent au moins un crawler d'entraînement majeur sans bloquer tous les robots :

| Périmètre | Sites avec opt-out | Incomplet | Incomplet strict¹ | CCBot oublié | ClaudeBot oublié |
|---|---:|---:|---:|---:|---:|
| Tranco top 1M | 80 598 | 36,5 % | 33,6 % | 15,7 % | 22,4 % |
| 8 marchés UE (DE, FR, IT, ES, NL, PL, BE, SE) | 7 042 | **57,4 %** | **53,5 %** | 25,4 % | 33,8 % |
| .com/.us | 36 561 | 35,2 % | 32,1 % | 14,0 % | 21,2 % |
| Allemagne / France | 2 054 / 976 | 59,0 % / 55,3 % | 55,5 % / 53,4 % | 25,5 % / 22,5 % | 35,5 % / 37,4 % |
| Japon / Corée du Sud | 576 / 275 | 66,7 % / 76,0 % | – | 43,9 % / 49,5 % | 34,2 % / 51,6 % |

¹ Seuls les crawlers dont l'unique usage documenté est l'entraînement sont comptés : GPTBot, CCBot, ClaudeBot, meta-externalagent et Bytespider. En laisser un ouvert ne rapporte aucune visibilité, ce qui écarte l'hypothèse d'un choix délibéré.

À cela s'ajoutent **2 138 sites** qui ne bloquent que les jetons obsolètes d'Anthropic (`anthropic-ai`, `claude-web`). Ils croient avoir bloqué Anthropic, mais `ClaudeBot` passe.

**Pourquoi c'est juridiquement grave.** Le tribunal d'Amsterdam (30 octobre 2024, ECLI:NL:RBAMS:2024:6563) a jugé qu'un robots.txt bloquant des bots nommés n'est pas une réserve générale contre les autres. Le code de pratique GPAI ne rend obligatoire que robots.txt (RFC 9309), et les amendes de l'AI Act (art. 53(1)(c)) sont applicables depuis le 2 août 2026. Un site européen sur deux qui croit avoir réservé ses droits ne l'a donc fait que partiellement.

*Réserves :* le ccTLD n'est qu'un indicateur approximatif du marché ; seuls les blocages `Disallow: /` sur des groupes nommés sont mesurés ; la réserve peut aussi figurer dans les CGU.

**D2. Les contradictions juridiques transfrontalières sont structurelles** (sources au §14) :
1. Le même opt-out est opposable dans l'UE (art. 4(3) DSM) et au Vietnam (décret 134/2026, art. 37b, *reported*). Il est sans effet au Japon (art. 30-4, pas d'opt-out) et à Singapour (s244 ; la s187 annule les clauses contractuelles contraires).
2. « Lisible par machine » n'a pas de définition stable. Hambourg (LAION) et Amsterdam ne disent pas la même chose, et la liste des protocoles de la Commission est toujours en attente après une consultation close en janvier 2026.
3. On ne peut pas sortir des AI Overviews sans quitter Google Search : Google-Extended ne les couvre pas. Le Royaume-Uni l'impose désormais (exigence de la CMA du 3 juin 2026). L'UE n'a qu'une enquête art. 102 ouverte en décembre 2025.
4. Entraînement et mémorisation sont traités différemment. Munich (GEMA c. OpenAI, 11 novembre 2025) y voit une reproduction ; la High Court britannique (Getty c. Stability) a jugé que les poids ne sont pas une copie ; aux États-Unis, l'entraînement est du fair use (Bartz, Kadrey) mais pas pour un outil concurrent non génératif (Thomson Reuters c. Ross, 3e circuit, 29 septembre 2026).
5. La responsabilité glisse de l'entraînement vers la récupération en temps réel (RAG) : conclusions de l'avocat général dans *Like Company c. Google* (C-250/25, 3 novembre 2026), lignes directrices japonaises sur le RAG.
6. L'étiquetage des contenus générés par IA est incohérent entre la Chine (texte inclus, depuis le 1er septembre 2025), l'Inde (audiovisuel, depuis le 20 février 2026), l'UE (art. 50(4), depuis le 2 août 2026) et la Corée (22 janvier 2026).

**D3. Le même fichier est lu différemment selon le parseur du crawler.**
- J'ai vérifié dans le code de référence de Google qu'une ligne non standard (`Crawl-delay`) ne sépare pas les groupes. Un fichier comme `User-agent: CCBot / Crawl-delay: 1 / User-agent: X / Disallow: /` bloque donc entièrement CCBot selon Google et RFC 9309, mais pas selon le parseur Python standard ni selon l'étude d'Abdullah.
- Sur 385 fichiers du top 10k, les trois parseurs (Google, urllib, Protego) divergent sur l'accès à la racine pour un agent IA dans 31 fichiers. Ils divergent sur au moins un chemin dans 116 fichiers (Protego) et 146 fichiers (urllib).
- Conséquence juridique : la question « le crawler a-t-il violé la réserve ? » dépend du parseur. Une réserve robuste doit donc être non ambiguë pour tous les parseurs, et c'est ce que le compilateur garantit.

**D4. Les règles vont changer plusieurs fois dans les mois qui viennent.**

| Date | Changement |
|---|---|
| 2 déc. 2026 | Marquage art. 50(2) de l'AI Act |
| 3 déc. 2026 | Contrôles CMA au niveau du répertoire (*reported*) |
| 1er févr. 2027 | Microsoft respecte `__usage_ai-training` |
| 1er mars 2027 | Fin de NOARCHIVE/NOCACHE pour l'entraînement chez Microsoft ; transition vietnamienne |
| 3 mars 2027 | Contrôles CMA au niveau de la page |
| 2027 | Google adopte le jeton partagé |

Chaque changement rend obsolètes des configurations existantes, comme `anthropic-ai` l'est devenu. C'est la base d'un besoin récurrent, donc d'un abonnement.

**D5 (stratégique, hors périmètre aujourd'hui).** La décision DMA art. 6(11) du 16 juillet 2026 et les remèdes de *US c. Google* (en appel) ouvrent l'accès aux données de recherche de Google à des moteurs concurrents, chatbots compris. La Commission constate une adoption « quasi absente ». Il y a là une opportunité pour un futur moteur vertical, mais elle exige des capitaux et un statut de moteur de recherche : je ne la poursuis pas avec un budget de 0 €.

## 5. Les quatre preuves

| Preuve | Niveau | Éléments |
|---|---|---|
| **Technique** | **Fort, démontré ici** | 142/142 tests de référence Google ; auto-vérification du compilateur (39 agents × 2 dialectes) ; requête RFC 3161 validée par OpenSSL ; 40 tests ; aucune dépendance |
| **Juridique** | **Fort pour le besoin ; risques maîtrisables pour l'outil** | Art. 4(3) DSM, art. 53(1)(c) de l'AI Act (amendes depuis le 2 août 2026), Rb Amsterdam 2024, code GPAI mesure 1.3, CMA 3 juin 2026. Risques propres à l'outil au §9 |
| **Commerciale** | **Indirecte seulement** | Demande forte pour la catégorie : 93 155 sites du top 1M bloquent des IA ; 30 % des scrapes contournent robots.txt (TollBit, T4 2025) ; 70,6 % des sites qui bloquent ChatGPT-User restent cités (BuzzStream) ; procès ; contrats de licence. **Aucune preuve de disposition à payer pour NOVARYS** : il faudrait des entretiens clients, que je n'ai pas le droit de mener sans votre accord |
| **Économique** | **Plausible** | Coût marginal quasi nul (traitement local, fichiers de quelques Ko). Prix de référence : Dark Visitors 29 $/mois, Otterly 29–489 $, Peec 85–425 €, Conductor ≈ 49 k$/an. Les contrats de licence en jeu se chiffrent en millions par an |

## 6. DÉCIDER

**GO limité** sur le moteur gratuit et open-core : compilateur, auditeur, vérificateur de logs, registre de preuves, base de connaissances, études.

**NO-GO pour l'instant :**
- **Score GEO de page** : la science ne le soutient pas.
- **Pay-per-crawl ou place de marché** : Cloudflare, TollBit et Microsoft y sont déjà, et c'est une zone dense en brevets.
- **Infrastructure SaaS payante** : budget de 0 €.
- **Tout contact externe ou publication** : pas d'autorisation.

**Validation humaine requise (risque élevé) :**
- publier le code et l'étude ;
- entretiens clients ;
- choix de la licence open source ;
- dépôt de marque ;
- consultation d'avocats.

## 7. Ce qui a été construit et MESURÉ

| Module | Fichier | Résultat mesuré |
|---|---|---|
| Parseur RFC 9309 + extensions Google, sans regex (pas de backtracking catastrophique) | `novarys/robots.py` | 142/142 contre 128 (urllib) et 130 (Protego) |
| Comparaison de dialectes | `novarys/dialects.py` | 31/385 divergences de racine détectées |
| Compilateur d'intention | `novarys/compiler.py` | robots.txt, TDMRep, en-têtes, nginx, meta, RSL, déclarations FR/EN/DE, manifeste hashé ; auto-vérification PASS |
| Auditeur à effet juridique | `novarys/audit.py` | 15 types de constats (+ 4 contrôles de syntaxe), score à formule publique, effet par marché, visibilité par surface IA. Sa propre sortie compilée obtient 100/100 et zéro constat moyen ou plus |
| Vérificateur de logs | `novarys/logs.py` | crawler authentique ou usurpé selon les plages IP officielles, violations au regard du robots.txt en vigueur à la date de la requête, ratio crawl/référent ; aucune IP humaine en sortie |
| Registre de preuves | `novarys/evidence.py` | chaînage SHA-256, détection d'altération testée, requête d'horodatage RFC 3161 |
| Base de connaissances | `novarys/data/*.json` | 39 agents, 30 marchés + UE, statut de vérification par entrée |

**Sur les 385 fichiers réels du top 10k :**
- 162 ont au moins un constat grave ;
- sur les 168 fichiers qui expriment un opt-out, le score médian est de 60/100 et seuls 27 atteignent au moins 80.

Ces fichiers ont été sélectionnés par l'étude source pour ses constats : l'échantillon est biaisé.

## 8. Confrontation à la concurrence

| Capacité | NOVARYS | Cloudflare AI Crawl Control | Dark Visitors | TollBit | Vérificateur Abdullah | Profound / Peec |
|---|---|---|---|---|---|---|
| Une intention compilée vers tous les protocoles (robots, `__usage_ai-training`, AIPREF, TDMRep, RSL, en-têtes) | **Oui** | Partiel (managed robots + Content Signals) | robots.txt seul | – | – | – |
| Effet juridique par marché | **Oui (30 + UE)** | – | – | – | – | – |
| Robustesse multi-parseurs | **Oui** | – | – | – | 1 parseur | – |
| Détection de piège (groupe nommé qui annule les règles `*`) | Oui | – | – | – | **Oui** | – |
| Preuve horodatée et chaînée | **Oui** | – | – | – | – | – |
| Logs : vrai ou faux bot, violations | Oui (hors ligne) | Oui (au niveau du CDN, plus riche) | Oui (payant) | Oui | – | Partiel |
| Visibilité dans les réponses IA | Éligibilité seulement | – | – | – | – | **Oui (mesure)** |
| Blocage actif / monétisation | – (hors périmètre) | **Oui** | – | **Oui** | – | – |
| Indépendant du CDN, hors ligne, sans dépendance | **Oui** | Non | Non | Non | Oui | Non |

**Faiblesses de NOVARYS, sans fard :**
- pas de blocage actif ;
- pas de mesure de citations ;
- pas encore d'interface web ;
- registre à vérifier sur pièces pour 34 des 39 agents (23 *unverified*, 11 *reported*) ;
- aucun client.

## 9. Analyse juridique du produit lui-même

- **Consultation juridique.** En France, la consultation juridique rémunérée est réservée aux professions réglementées (loi n° 71-1130, art. 54 s.). L'outil doit rester une information générale et documentaire, avec un avertissement affiché partout. Les recommandations personnalisées passeront par des avocats partenaires dans les offres payantes. *À valider par un avocat.*
- **RGPD.**
  - En mode local, le client est seul responsable de traitement de ses logs, et l'outil ne produit que des agrégats de bots.
  - En SaaS, il faudra un contrat de sous-traitance (art. 28), de la minimisation et un hébergement dans l'UE.
- **Données et licences tierces.**
  - Crawlora (CC BY 4.0) et l'étude Abdullah (CC BY 4.0) sont cités avec attribution ; leurs fichiers robots.txt bruts ne sont pas redistribués.
  - Les tests Google sont sous Apache-2.0 ; l'avis figure dans `NOTICE`.
- **Collecte.** L'outil ne lit que les fichiers publics du site audité. Les études reposent sur des jeux de données publics existants ; aucun crawling de masse n'a été fait.
- **Brevets.** La recherche n'a pas été faite, faute d'accès. Risque estimé faible à modéré : l'outil s'appuie sur des standards publics (RFC 9309, TDMRep 2022, RFC 3161), qui constituent une antériorité solide. La zone dense est celle de l'empreinte comportementale de bots par machine learning et de la négociation de paiement, deux choses que l'outil évite. **Une recherche de liberté d'exploitation est à faire avant toute levée de fonds.**
- **Marque « NOVARYS ».** Non vérifiée (bases INPI, EUIPO et USPTO inaccessibles). **À rechercher avant tout usage commercial.**

## 10. Modèle économique (de 0 € à 1 M€)

| Offre | Prix | Contenu | Justification |
|---|---|---|---|
| **Libre** | 0 € | CLI open source : audit, compilation, logs et preuves en local, études publiques | Acquisition à coût nul ; l'étude sert de relais presse |
| **Pro** | 49 €/mois par site | Surveillance quotidienne de ses propres signaux, registre de preuves hébergé avec horodatage mensuel, alertes sur les changements de règles (D4), fichiers recompilés automatiquement | Ancrage entre Dark Visitors (29 $) et Otterly (189 $) |
| **Agence** | 390 €/mois (25 sites) | Multi-sites, rapports en marque blanche, analyse de logs hébergée | Les agences revendent la conformité |
| **Entreprise / groupe de presse** | 30–150 k€/an | Centaines de domaines, SSO, horodatage qualifié eIDAS, ingestion de logs à grande échelle, rapports de conformité des crawlers pour négocier des licences | Ordre de grandeur de Conductor (≈ 49 k$) et BrightEdge (≈ 103 k$, *unverified*) |
| **Stratégique** | 250 k€–1 M€ sur 3 ans | Observatoire sectoriel pour une société de gestion collective, un syndicat de presse ou un État : preuves pour les négociations de droits voisins (art. 15 DSM) ou les plaintes auprès de l'AI Office, accord de niveau de service sur le registre, déploiement sur site | Voir le calcul ci-dessous |

**Calcul pour l'offre stratégique.** Pour un collectif de 300 éditeurs, 1 M€ sur 3 ans revient à environ 1 100 € par éditeur et par an, soit le niveau de Pro + Agence. Cela représente environ 1 à 3 % des montants de licence en jeu (référence Amazon–NYT : 20–25 M$/an pour un seul éditeur). **Ce montant n'est justifié que si un tel acheteur le confirme lors d'un entretien.**

## 11. ANTICIPER — risques et opportunités

**Opportunités :**
- les dates du §4 (D4) ;
- la liste européenne des protocoles, qui pourrait consacrer TDMRep ;
- la loi française sur la présomption d'usage, en navette ;
- l'arrêt *Like Company* (CJUE).

**Risques :**
- **Cloudflare ajoute un audit juridique.** Parade : neutralité vis-à-vis du CDN et profondeur juridique.
- **Les fournisseurs convergent vers un jeton unique** (`__usage_ai-training`). C'est à double tranchant : la valeur se déplacerait vers la preuve et l'effet juridique.
- **Un tribunal juge robots.txt suffisant quel que soit le bot.** Cela affaiblirait D1 ; la preuve horodatée garderait sa valeur.

## 12. Plan de validation (soumis à votre autorisation)

1. **Publier le dépôt et l'étude des 30 marchés.** Il faut d'abord choisir une licence ; je recommande Apache-2.0 pour le cœur.
2. **Mener 20 entretiens** avec des éditeurs français, allemands et néerlandais, des agences SEO et une société de gestion collective. Objectif : au moins 5 lettres d'intention Pro et 1 pilote stratégique.
3. **Critère d'abandon :** moins de 3 personnes sur 20 prêtes à payer au moins 49 €/mois. Dans ce cas, garder l'open source plus du conseil, ou arrêter.
4. **Ouvrir l'accès réseau aux documentations des fournisseurs et aux sources juridiques primaires** pour passer les entrées *reported* et *unverified* en *verified*.
5. **Faire réaliser** une recherche de marque et une recherche de liberté d'exploitation par un conseil.

## 13. DREAMING — auto-audit

- **Ce qui est solide :** la conformité du parseur, les chiffres de l'étude D1 (reproductibles, scripts fournis) et la logique du compilateur.
- **Ce qui est fragile :**
  - beaucoup de faits juridiques et de marché viennent de résumés secondaires ;
  - la formule du score est la mienne et n'a été validée ni par un tribunal ni par des praticiens ;
  - le ccTLD est un indicateur approximatif ;
  - l'échantillon de 385 fichiers est biaisé ;
  - les dates de la CMA et du jeton `__usage_ai-training` sont *reported*.
- **Ce que je n'ai pas fait :** brevets, marque, interface web, test sur de vrais logs serveur (seulement sur des logs synthétiques), et validation client.
- **Prochaine révision du modèle du monde :** dès que les sources primaires seront accessibles, rejouer le registre et la base juridique, puis recalculer.

## 14. Sources principales

**Droit**
- Directive 2019/790 : https://eur-lex.europa.eu/eli/dir/2019/790/oj
- AI Act : https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- Code GPAI (10 juillet 2025) : https://www.editionmultimedia.fr/wp-content/uploads/2025/07/Code-of-Practice-for-GPAI-Copyright-10-07-25.pdf
- Consultation sur les protocoles : https://www.scl.org/european-commission-consults-on-protocols-for-reserving-rights-from-text-and-data-mining-under-the-ai-act-and-the-gpai-code-of-practice/
- Rb Amsterdam 2024 : https://cms.law/en/gbr/publication/artificial-intelligence-and-copyright-case-tracker/The-Netherlands-DPG-Media-B.V.-Mediahuis-Nederland-B.V.-Mediahuis-NRC-B.V.-v-Knowledge-Exchange-B.V.-trading-as-Howards-Home-30-October-2024
- GEMA c. OpenAI : https://www.lto.de/recht/nachrichten/n/42o1413924-lg-muenchen-i-gema-openai-chatgpt-songtexte-ki
- CJUE C-250/25 : https://curia.europa.eu/site/jcms/p1_1000088866/en/
- CMA : https://www.gov.uk/government/news/further-cma-action-to-secure-a-fairer-deal-for-businesses-and-improve-google-search-services-in-uk
- DMA art. 6(11) : https://digital-markets-act.ec.europa.eu/developer-portal/data-access/alphabet-specification-proceedings-sharing-google-search-data_en
- Japon : https://www.wipo.int/documents/d/office-japan/docs-en-tatsuhiro-ueno_general-understanding-on-ai-and-copyright-in-japan_set.pdf
- Vietnam : https://www.bakermckenzie.com/en/insight/publications/2026/05/vietnam-redefining-copyright-for-ai
- Inde : https://spicyip.com/2026/07/training-chatgpt-on-copyrighted-works-prima-facie-protected-under-indian-copyright-act-delhi-high-court-refuses-interim-injunction-against-openai.html
- Ross (3e circuit) : https://ipwatchdog.com/2026/09/30/third-circuit-affirms-revised-fair-use-ruling-against-ross-ai-legal-research-platform-in-sealed-opinion/
- Royaume-Uni : https://www.dlapiper.com/insights/publications/2026/03/tdm-and-training-ai-models-uk-government-publishes-report-and-impact-assessment
- Chine : https://www.covingtonblogs.com/2025/03/18/china-releases-new-labeling-requirements-for-ai-generated-content/
- Corée du Sud : https://www.cooley.com/news/insight/2026/2026-01-27-south-koreas-ai-basic-act-overview-and-key-takeaways

**Marché**
- Profound : https://www.tryprofound.com/newsroom/profound-raises-usd180m-series-d-at-usd1-8b-valuation-to-build-the-ai-platform-for-marketing-teams
- Peec AI : https://capital.com/en-eu/news/peec-ai-doubles-revenue-in-six-months-to-hit-20m
- Levées GEO : https://valueaddvc.com/blog/ai-search-optimization-startups-2026-geo-aeo-funding-investors
- Content Signals de Cloudflare : https://blog.cloudflare.com/content-signals-policy/
- TollBit : https://tollbit.com/bots/25q2
- Tarifs Dark Visitors : https://darkvisitors.com/pricing
- Pew : https://9to5google.com/2025/07/23/google-ai-overview-link-click-study/
- Ahrefs : https://ahrefs.com/blog/ai-overviews-reduce-clicks-update
- SparkToro : https://sparktoro.com/blog/in-2026-less-than-one-third-of-google-searches-still-send-a-click/
- BuzzStream : https://ppc.land/blocking-ai-crawlers-doesnt-stop-citations-new-data-shows-why/

**Science**
- GEO : https://arxiv.org/abs/2311.09735
- C-SEO Bench : https://arxiv.org/abs/2506.11097
- AutoGEO : https://arxiv.org/abs/2510.11438
- Consent in Crisis : https://arxiv.org/abs/2407.14933
- Kim et al., IMC 2025 : https://arxiv.org/abs/2505.21733
- Liu et al., IMC 2025 : https://arxiv.org/abs/2411.15091
- Nestaas et al., ICLR 2025 : https://arxiv.org/abs/2406.18382
- Étude llms.txt d'Ahrefs : https://ahrefs.com/blog/llmstxt-study/

**Standards**
- RFC 9309 : https://www.rfc-editor.org/rfc/rfc9309.html
- IETF AIPREF : https://datatracker.ietf.org/wg/aipref/
- Jeton d'entraînement : https://datatracker.ietf.org/doc/html/draft-kelley-aipref-training-preference-signal
- TDMRep : https://www.w3.org/community/tdmrep/
- RSL : https://rslstandard.org/rsl
- Préférences IA de Bing : https://www.bing.com/webmasters/help/new-ai-preferences-2t1cc16d
- Bots d'Anthropic : https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- Bots d'OpenAI : https://developers.openai.com/api/docs/bots
- Fonctions IA de Google : https://developers.google.com/search/docs/appearance/ai-features

**Données**
- Crawlora : https://github.com/Crawlora-org/ai-crawler-blocking-index-data
- Étude Abdullah : https://github.com/Ghaith-Abdullah/robots-ai-allowlist-study-2026
- Code de référence Google : https://github.com/google/robotstxt
