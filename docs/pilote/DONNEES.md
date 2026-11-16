# Données personnelles, confidentialité, concurrence

> **BROUILLON**, à faire valider par un délégué à la protection des données ou un avocat.

## 1. Données traitées

| Donnée | Où | Personnelle ? | Traitement |
|---|---|---|---|
| Logs d'accès (IP, horodatage, chemin, `Referer`, `User-Agent`) | Chez l'éditeur | Oui : IP de visiteurs humains | Analysés localement par `novarys logs`. Les lignes humaines ne servent qu'à compter l'hôte du `Referer` ; aucune IP humaine n'est conservée en sortie |
| IP de robots d'entreprises (plages publiées) | Chez l'éditeur | En général non (personnes morales) | Comparées aux plages publiées ; non publiées |
| Rapport mensuel par éditeur | Éditeur → opérateur | Non (agrégats) | Confidentiel entre l'éditeur et l'opérateur |
| Journal public | Public | Non | Empreintes seules : contenu d'un robots.txt (déjà public), rapport, identifiant d'éditeur haché |
| Agrégats | Public | Non | Au moins 5 éditeurs par cellule, règle de dominance à 70 % |

## 2. Rôles au sens du RGPD

- **Mode local (défaut du pilote).** L'éditeur est seul responsable du traitement de ses logs. L'opérateur ne reçoit aucune donnée personnelle.
- **Mode hébergé (hors pilote).** L'opérateur serait sous-traitant (art. 28 RGPD), avec un contrat écrit, des instructions documentées, un hébergement dans l'UE, la confidentialité du personnel, un registre (art. 30) et une assistance aux droits des personnes.
- **Base légale côté éditeur, à confirmer** : intérêt légitime (sécurité et défense de ses droits, art. 6(1)(f)), avec une information dans sa politique de confidentialité.

## 3. Minimisation et conservation

- Seules les lignes d'agents identifiés sont examinées en détail. La sortie ne contient que des comptages et au plus 5 exemples de chemins exclus, sans IP.
- La durée de conservation des logs reste celle que l'éditeur pratique déjà. Les rapports et le journal ne contiennent pas de données personnelles.

## 4. Droit de la concurrence

- **Interdit dans le pilote :** échange de prix, de tarifs, de conditions contractuelles ou d'intentions de négociation entre éditeurs concurrents (art. 101 TFUE, art. L.420-1 C. com.).
- **Garde-fous techniques :** aucune donnée tarifaire collectée, seuils k = 5 et dominance à 70 %, rapports individuels non communiqués aux autres participants.
- **Réunions :** les réunions du comité de méthode sont limitées à la méthode, avec un ordre du jour et un compte rendu écrits.

## 5. Sécurité

- Le registre de preuves et le journal public sont en écriture seule, chaînés et vérifiables.
- Les secrets des canaris (option expérimentale) restent chez l'éditeur ; seul leur engagement est public.
