# CLAUDE.md — NOVARYS OMNISEARCH

## Règle de délégation

| Étape | Qui | Exemples |
|---|---|---|
| **Collecte** | Sous-agents **Haiku** ou **Sonnet** | recherches web, lecture de sources, extraction de textes juridiques, relevés de prix, récupération de jeux de données |
| **Réfléchir** | **Opus** | synthèse, confrontation des sources, hypothèses, conception des tests, analyse des résultats |
| **Décider** | **Opus** | GO / NO-GO, choix des leviers, arbitrages, ce qui est construit ou abandonné |

- Pour la collecte simple, utiliser Haiku : lookups, listes, extraction mécanique.
- Pour la collecte qui demande du jugement de pertinence, utiliser Sonnet : tri de sources, résumé de textes juridiques.
- Un sous-agent rapporte des faits sourcés, avec URL, date, article et statut de vérification. Il ne tranche pas.
- Opus vérifie ce qui est rapporté avant de s'en servir pour décider.
