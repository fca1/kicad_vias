# Correction du rendu des noms de nets


## 19 octobre 2026 — Noms de nets littéraux dans le tableau Markdown

Demande autorisée : corriger le plugin et le tableau dont I1.2 affichait seulement
un tilde dans Markdown Panel. Cause reproduite avec Markdig 0.9.3 et son pipeline
UseAdvancedExtensions : ~{CMD_RESET} devient <td>~</td>, les accolades étant
interprétées comme des attributs. Le nom source et les nets CAO sont intacts.
Correction dans stage_output : protéger la ponctuation ASCII des cellules Net
comme texte littéral Markdown. Les autres colonnes, coordonnées, entêtes et
identifiants gardent leur représentation. Pas de changement de placement.

Validation : 37 tests natifs réussis, dont une régression Top/Bottom pour reset,
pipes, antislashs, accents graves, balises HTML, entités et emphase. Vérification
réelle avec la DLL Markdig installée : 31 noms du tableau courant et dix cas
spéciaux rendus intégralement dans cinq colonnes. Tableau utilisateur réparé,
sauvegarde privée préalable dans .local ; aucun PCB modifié. Les fichiers privés
et les chemins de la carte ne font pas partie du commit public.

Travail parallèle signalé par l'utilisateur : migration IPC dans le chat
« kicad_vias ». Autorisation explicite de coordonner les deux chats reçue.
Message de coordination envoyé, correction limitée à l'échappement de stage_output,
nouveau test distinct et présente documentation. Les fichiers ipc_adapter.py et
ipc_native.py du travail parallèle sont exclus de notre commit ciblé. Aucun push
initié ici ; le chat de migration est informé pour sa publication finale.
Installation par le hook post-commit, vérification exacte dans .local/last_install.json.
Le rechargement dans l'éditeur ouvert reste à effectuer ; aucun redémarrage imposé.
