# Méthode de mesure `novarys-metering/0.1` — spécification

> **BROUILLON** soumis à la revue du comité de méthode ([GOUVERNANCE.md](GOUVERNANCE.md)). Les termes DOIT, NE DOIT PAS et DEVRAIT ont le sens de la RFC 2119. Implémentation de référence : `novarys/logs.py` et `novarys/metering.py`.

## 1. Objet

Mesurer de façon reproductible l'usage du site d'un éditeur par les agents des fournisseurs d'IA et les visites que ces fournisseurs renvoient. La méthode ne qualifie juridiquement aucun fait.

## 2. Entrées

1. **Journaux d'accès** au format *combined* (Apache/nginx) : IP, horodatage avec fuseau, méthode, chemin, statut, `Referer`, `User-Agent`. Les lignes illisibles DOIVENT être comptées dans `lines` et exclues de `parsed`.
2. **Instantanés de signaux** (robots.txt, TDMRep), enregistrés dans le registre de preuves local (`novarys snapshot`) **avant** la période mesurée. Une requête sans instantané en vigueur à sa date DOIT être comptée en `not_assessable`.
3. **Fichiers de plages IP publiés par les fournisseurs.** Leur date de récupération et leur empreinte SHA-256 DEVRAIENT être consignées dans le registre de preuves.
4. **Le registre des agents** (`novarys/data/agents.json`), dont la version DOIT figurer dans le rapport.

## 3. Identification et vérification

- **Identification.** Un agent est reconnu à son jeton dans le `User-Agent` (jeton le plus long, frontières de mot).
- **Vérification.** Une requête est `verified` si son IP appartient aux plages publiées de l'agent, `spoofed` si des plages existent et que l'IP n'y figure pas, `unverifiable` en l'absence de plages.
- **Exclusion.** Les requêtes `spoofed` NE DOIVENT PAS être comptées dans les totaux ni dans les accès à des chemins exclus.

## 4. Métriques (par fournisseur et par période)

| Métrique | Définition |
|---|---|
| `requests_not_spoofed` | Requêtes des agents déclarés du fournisseur, moins les requêtes usurpées |
| `requests_verified` | Requêtes dont l'IP est dans les plages publiées |
| `disallowed_fetches_verified` | Requêtes vérifiées vers un chemin exclu par le robots.txt **en vigueur à la date de la requête**, interprété selon la RFC 9309 (sémantique de l'implémentation de référence de Google, 142/142 de sa suite de tests) |
| `not_assessable` | Requêtes sans instantané en vigueur à leur date |
| `referrals` | Visites humaines dont l'hôte du `Referer` est un assistant du fournisseur (liste dans `ai_referrers`) |
| `crawl_to_referral` | Requêtes non usurpées des agents d'entraînement, de réponse et à usage mixte, divisées par `referrals` (nul si aucune visite renvoyée) |

**Période :** mois civil UTC, sauf convention contraire du comité.

## 5. Rapport par éditeur

- Le rapport est un JSON canonique (clés triées) produit par `novarys meter report`.
- L'éditeur DOIT engager son rapport dans le journal public (`novarys meter commit`). Seule l'empreinte du rapport et celle de l'identifiant de l'éditeur y sont publiées.
- Le rapport lui-même n'est transmis qu'à l'opérateur.

## 6. Agrégation et protection de la confidentialité

Les règles d'agrégat (`novarys meter aggregate`) :

1. **Seuil de nombre.** Une cellule (fournisseur) n'est publiée que si au moins **k = 5** éditeurs y contribuent.
2. **Règle de dominance.** Le total des requêtes n'est pas publié si un seul éditeur en représente plus de **70 %**.
3. **Pas de valeur individuelle.** Le ratio crawl / visite est publié en quartiles (p25, médiane, p75), et seulement si au moins 5 éditeurs ont des visites renvoyées.
4. **Pas de prix.** Aucune donnée de prix, de tarif ou de contrat n'est collectée ni publiée.

## 7. Reproductibilité et contrôle

- Le même rapport recalculé à partir des mêmes entrées DOIT avoir la même empreinte.
- **Contrôle par l'éditeur.** Tout participant peut vérifier l'inclusion de son rapport (`novarys check`).
- **Contrôle par tous.** Chacun peut vérifier qu'aucune entrée du journal n'a été réécrite (preuve de cohérence).
- **Tête d'arbre.** L'opérateur publie au moins chaque semaine une tête d'arbre et sa requête d'horodatage RFC 3161 (`novarys tlog head`, `novarys tlog tsq`).

## 8. Limites connues (v0.1)

- Les agents qui ne s'identifient pas (navigateurs automatisés, faux user-agents hors plages publiées) échappent à l'identification. Ils ne sont **pas** comptés comme accès d'IA.
- Les fournisseurs sans plages publiées n'ont que des requêtes `unverifiable`.
- Les visites renvoyées sans `Referer` (applications, confidentialité) sont sous-comptées : le ratio crawl / visite est donc un majorant.
- Les sites derrière un CDN doivent fournir l'IP client réelle (en-tête de confiance du CDN), faute de quoi la vérification échoue.

## 9. Gestion des versions

- **Toute modification d'une définition** crée une nouvelle version (`novarys-metering/0.2`, etc.), approuvée par le comité. Les agrégats de versions différentes NE DOIVENT PAS être combinés.
- **Le registre des agents** évolue indépendamment, et sa version est citée dans chaque rapport.
