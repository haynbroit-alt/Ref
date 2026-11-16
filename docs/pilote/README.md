# Dossier de pilote — NOVARYS, tiers neutre de la preuve et de la mesure

> **BROUILLON, NON ENVOYÉ.** Aucun de ces documents n'a été communiqué à quiconque. Toute prise de contact, signature, dépense ou publication suppose l'accord explicite du titulaire du projet.

| Document | Rôle |
|---|---|
| [PROPOSITION.md](PROPOSITION.md) | Proposition de pilote de 12 semaines : objectifs, participants, critères de succès et d'abandon |
| [METHODE-MESURE.md](METHODE-MESURE.md) | Spécification normative de la méthode `novarys-metering/0.1` |
| [GOUVERNANCE.md](GOUVERNANCE.md) | Charte de neutralité et comité de méthode paritaire |
| [DONNEES.md](DONNEES.md) | Données personnelles, confidentialité, garde-fous de droit de la concurrence |
| [RUNBOOK.md](RUNBOOK.md) | Commandes exactes pour les éditeurs participants et l'opérateur |
| [MESSAGES.md](MESSAGES.md) | Projets de messages (FR, EN), à relire avant tout envoi |

Le mode d'emploi est **répété de bout en bout** sur des données synthétiques par `examples/pilot_demo.py`, et testé par `tests/test_pilot_demo.py`. Le scénario couvre 6 éditeurs, avec des robots vérifiés, des robots usurpés et des visites renvoyées par des IA. La mesure retrouve la vérité injectée : environ 10 % d'accès à un répertoire exclu, contre 10,15 % mesurés.
