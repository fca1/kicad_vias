# Kicad_Via

Plugin natif de l'éditeur PCB **KiCad 10.0**, avec bouton de bandeau représentant
un via et son drapeau. Génération de repères d'accès de test, puis fusion
facultative sur la sérigraphie. Le routage et le masque de soudure sont conservés.

## Utilisation

Cliquer sur le bouton **Kicad_Via** et choisir :

- **Top ou Bottom**, avec deux listes et deux numérotations indépendantes.
- Hauteur du texte : **0,65 mm par défaut**, réglable de 0,4 à 2 mm.
- Couche utilisateur : seules les couches libres ou contenant les objets
  déjà identifiés comme appartenant au plugin sont proposées. La génération
  la renomme obligatoirement **Kicad_Via_TOP** ou **Kicad_Via_BOTTOM**.
- Nom et emplacement du tableau **.nd** (ou .md), à l'aide du sélecteur.
- Grille en pointillés de 20 mm et allègement des labels proches, activés par défaut.

**Générer / remplacer** retient un seul via découvert et accessible par net,
en privilégiant les accès dégagés. Le label est dans un ovale, avec un trait
vers son via. Si un repère imprimé est à moins de 3 mm, le label voisin peut
être omis : le tableau conserve cet accès.
Une génération remplace uniquement les UUID précédemment gérés par le plugin.

**Fusionner vers F.SilkS** (Top) ou **B.SilkS** (Bottom) déplace les objets,
en conservant leurs ajustements manuels. Le plugin vérifie les collisions
avec la sérigraphie et les ouvertures de masque de destination. Les inscriptions
étrangères ne sont jamais remplacées. Les anciennes inscriptions fusionnées
par le plugin sont remplacées lors d'une nouvelle fusion de la même face.

## Convention

**C2-1** = colonne C, ligne 2, premier accès de la case de 20 × 20 mm.
Le suffixe suit les positions dans la case, pas l'ordre alphabétique des nets.
Les colonnes continuent après Z : AA, AB…

La grille est vue de la face sélectionnée : X à droite, Y vers le haut ;
origine au coin inférieur gauche de l'enveloppe Edge.Cuts de cette vue.
Pour Bottom, X est inversé et les textes sont miroités dans le fichier KiCad
afin d'être lisibles depuis le dessous. Un repère C2-1 peut exister sur chaque
face : son tableau Top ou Bottom l'identifie sans ambiguïté.

Le tableau comporte cinq colonnes : **Repère, Net, Case, X (mm), Y (mm)**.
Les coordonnées de la vue choisie sont arrondies au millimètre, sans décimales.
La face figure dans le titre ; les données techniques restent internes au plugin.
Un fichier existant n'est réécrit que s'il est déjà un tableau Kicad_Via de la
même face. Une liste Bottom n'écrase pas une liste Top.

## Installation et suivi

Le dépôt est dans `C:/Users/frant/Documents/ChatGPT/Kicad_Via`.
Installation : `D:/kicad/bin/python.exe tools/install_plugin.py --commit HEAD`.
Le hook post-commit appelle cette installation **après chaque commit**, depuis
une archive Git du commit. Le paquet installé est vérifié SHA-256 et sa version
affiche le commit. Sauvegardes et manifestes : `.local/install_*/`.

Destination : `Documents/KiCad/10.0/3rdparty/plugins/Kicad_Via`.
Recharger les plugins dans les préférences de l'éditeur pour recharger une
version déjà importée, sans redémarrer ni enregistrer la carte.
Python natif KiCad requis avec wxPython et Shapely, présents sur l'installation
auditée (KiCad 10.0.7, wxPython 4.3.1, Shapely 2.2.0).

L'API native est nécessaire au renommage des couches, non exposé par IPC
dans la version installée. IPC sert aux captures de la carte ouverte et au
rechargement des plugins pendant la mise au point ; aucun export manuel requis.

La propriété des objets est conservée dans
`%LOCALAPPDATA%/Kicad_Via/ownership`, par UUID de groupe et de graphismes.
Elle survit à l'enregistrement et à la réouverture sur ce poste, même si la
carte est enregistrée sous un autre nom. Pour transférer les reprises sur un
autre poste, copier aussi ce registre. Sans registre, une couche occupée est
refusée ; son seul nom ne donne jamais l'autorisation d'effacer son contenu.
Un groupe peut être dissocié pour déplacer ses objets ; leurs UUID restent connus.
La suppression d'un objet ou son regroupement avec des objets étrangers est
signalé et bloque son remplacement. Annuler une fusion est reconnu par la couche
effective des objets. Annuler une action PCB n'annule pas le tableau externe.

## Contrôles et limites

Tests : `D:/kicad/bin/python.exe -m unittest discover -s tests -v`.
Validation sur cas synthétiques Top/Bottom et copie du PCB utilisateur.
Accessibilité estimée à partir des empreintes 2D, avec marges : aucun modèle
3D de pointe ni essai de fabrication ne sont qualifiés. Les vias sous le
vernis de la face demandée sont exclus ; le plugin ne modifie pas le vernis.
Une carte sans accès disponible reste inchangée.

Références : [API IPC et plugins KiCad](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/),
[API native Python](https://docs.kicad.org/doxygen-python-10.0/namespaces.html).

## Mémoire du projet

Dépôt : [fca1/kicad_vias](https://github.com/fca1/kicad_vias).
La description initiale du dépôt distant est conservée : « Plugin permettant de creer des labels pour le debug de carte hardware ».

Pour reprendre le travail, lire [le contexte](docs/PROJECT_CONTEXT.md),
[les décisions](docs/DECISIONS.md) puis [l’état](docs/STATUS.md).
Les sources et limites des échanges archivés sont décrites dans
[l’historique](docs/HISTORY/2026-10-18_demande_plugin.md).
Après clonage, activer le hook local avec `git config core.hooksPath .githooks`
(chemin Python KiCad du poste actuel : `D:/kicad/bin/python.exe`).
