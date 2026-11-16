# Mode d'emploi du pilote

Ces commandes sont exactement celles qu'exécute `examples/pilot_demo.py`. La démonstration est testée par `tests/test_pilot_demo.py`.

## Éditeur participant

**Une fois :**
```bash
pip install -e .                      # Python ≥ 3.10, aucune dépendance
novarys audit --robots robots.txt --jurisdiction EU,FR    # état initial, facultatif
# récupérer les fichiers de plages IP publiés par les fournisseurs (gptbot.json, etc.)
# et les consigner :
novarys snapshot ledger/ --url https://openai.com/gptbot.json --file gptbot.json --kind ip-ranges
```

**Chaque jour** (cron), *avant* la période mesurée :
```bash
novarys snapshot ledger/ --url https://www.mon-site.fr/robots.txt --file /var/www/robots.txt --tlog public-log/
```

**Chaque mois :**
```bash
novarys logs access.log --ledger ledger/ --url https://www.mon-site.fr/robots.txt \
  --ranges GPTBot=gptbot.json --ranges ClaudeBot=claudebot.json --json > logs.json
novarys meter report logs.json --publisher <identifiant> --period 2026-12 -o meter.json
novarys meter commit meter.json --tlog public-log/ -o meter-commit-proof.json
# transmettre meter.json à l'opérateur ; garder la preuve
```

Deux points d'attention :
- `--url` doit être l'URL utilisée dans `snapshot`. Sinon la commande refuse de tourner, au lieu d'annoncer à tort zéro accès interdit.
- Une requête faite alors qu'aucun instantané n'était en vigueur est comptée `not_assessable`, et non comme conforme.

## Opérateur

```bash
novarys meter aggregate meter-*.json -o aggregate.json     # k ≥ 5, dominance 70 %
novarys tlog head public-log/                              # tête d'arbre à publier (hebdomadaire)
novarys tlog tsq public-log/ -o tree-head.tsq              # à envoyer à une autorité d'horodatage
novarys tlog consistency public-log/ --index <taille précédente> -o cons.json
```

## N'importe quelle partie (éditeur, fournisseur, tiers)

```bash
novarys check meter-commit-proof.json          # inclusion d'un rapport
novarys check cons.json                         # le journal n'a pas été réécrit
novarys constat ledger/ --url https://www.mon-site.fr/robots.txt --as-of 2026-12-15T00:00:00+00:00 \
  --tlog public-log/ --logs-json logs.json --jurisdiction EU,FR -o constat.json --md constat.md
novarys constat-verify constat.json
```
