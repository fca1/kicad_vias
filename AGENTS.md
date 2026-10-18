# Kicad_Via

Documentation et commentaires en français. L'utilisateur autorise la création
du plugin de repérage Top/Bottom, labels en drapeaux et tableau de sortie.
Toute nouvelle portée de modification de code doit être décrite et autorisée.
Pour un bug : établir cause et preuves avant correction, distinguer les limites.

Après **chaque commit**, installer automatiquement le plugin depuis ce commit.
Le hook `.githooks/post-commit` appelle `tools/install_plugin.py`. Vérifier son
manifeste SHA-256 et ne jamais installer des fichiers de travail non committés.
Ne pas redémarrer KiCad ni enregistrer une carte utilisateur automatiquement.

Ne jamais effacer le contenu étranger d'une couche. Les seuls objets remplaçables
sont ceux dont les UUID sont enregistrés dans le registre local Kicad_Via,
avec concordance des objets et des membres du groupe sur la carte.
Les listes Top et Bottom ont des numérotations indépendantes.
Mettre à jour docs/STATUS.md et docs/DECISIONS.md à la fin d'une tâche.
