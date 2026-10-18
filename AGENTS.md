# Kicad_Via

Lire `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md` et `docs/STATUS.md` pour
reprendre le projet ; les échanges disponibles et leurs limites sont dans `docs/HISTORY/`.
Rédiger la documentation et les commentaires en français.

L'utilisateur a autorisé le plugin Top/Bottom, ses drapeaux, son tableau et sa
simplification finale à Repère, Net, X/Y au dixième de mm, titre Top/Bottom seul. Le 18 octobre 2026, il
ajoute les noms A3.1, l'export graphique ULP/RUN avec copie presse-papiers sur
clic et autorise la fusion de la PR nº 1 vers main avec réinstallation exacte.
Avant toute nouvelle
création, modification ou suppression de code, tests, scripts ou configuration
exécutable, décrire les changements envisagés et obtenir l'accord explicite
préalable de l'utilisateur. Une demande d'analyse ou de documentation ne donne
pas cet accord. Commenter les parties non triviales en expliquant leur raison.
Pour un bug : établir la cause et ses preuves avant correction, distinguer les
hypothèses et les limites ; ne pas corriger sur le seul symptôme.

Avant chaque déploiement, committer les changements à déployer et vérifier que
l'installation porte sur ce commit. Ne jamais déployer des fichiers non committés.
Après **chaque commit**, le hook `.githooks/post-commit` installe automatiquement
avec `tools/install_plugin.py`. Vérifier le manifeste SHA-256. Après clonage,
activer le hook : `git config core.hooksPath .githooks` (Python natif KiCad requis).
Tests : `D:/kicad/bin/python.exe -m unittest discover -s tests -v`.
Ne pas redémarrer KiCad ni enregistrer une carte utilisateur automatiquement.

Ne jamais effacer le contenu étranger d'une couche. Seuls sont remplaçables les
UUID du registre local Kicad_Via, concordant avec les objets et membres du groupe.
Les listes et numérotations Top/Bottom sont indépendantes.

À la fin de chaque tâche liée au projet, actualiser les fichiers pertinents de
`docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/STATUS.md` et `docs/HISTORY/`
à partir des sources effectivement disponibles ; consigner les corrections et
distinguer demandes et réalisations. Ne pas supposer l'accès aux autres chats.
Le dépôt GitHub est public : ne pas y publier de PCB, registres locaux ou échanges
confidentiels sans vérifier le périmètre de partage autorisé.
