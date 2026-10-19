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
- Grille en pointillés de 20 mm, activée par défaut.

**Générer / remplacer** retient un seul via découvert et accessible par net,
en privilégiant les accès dégagés. Le label est dans un ovale, avec un trait
jusqu'au **centre du via**, même si ce centre est découvert de vernis. Les autres
vias, pastilles, composants et inscriptions restent protégés. Seule la marge
supplémentaire des obstacles fixes est relâchée au voisinage immédiat du centre ;
leurs contours réels restent contrôlés. Le plugin cherche d'abord une place libre pour chaque label,
y compris si son via est proche d'un autre. Il essaie les positions déportées
entre 1,5 et 10 mm et un rappel direct ou avec un coude, sans collision.
Si tous ces placements échouent, le via reste dans le tableau avec
**Label imprimé = false**. Les autres labels sont conservés, sans condition de
proximité. Si aucun label ne peut être placé, le tableau contient tous les accès
comme fantômes, classés spatialement sans référence visible inventée.
Une génération remplace uniquement les UUID précédemment gérés par le plugin.

**Fusionner vers F.SilkS** (Top) ou **B.SilkS** (Bottom) déplace les objets,
en conservant leurs ajustements manuels. Le plugin vérifie les collisions
avec la sérigraphie et les ouvertures de masque de destination. Les inscriptions
étrangères ne sont jamais remplacées. Les anciennes inscriptions fusionnées
par le plugin sont remplacées lors d'une nouvelle fusion de la même face.

## Convention

**C2.1** = colonne C, ligne 2, premier accès de la case de 20 × 20 mm.
Dans chaque case, les groupes de labels visibles suivent leur ordre spatial.
Chaque visible est suivi de ses vias sans label, du plus proche au plus éloigné
de son via : **E2.1 affiché, E2.2 masqué, E2.3 masqué, E2.4 affiché**, etc.
Les fantômes sont rattachés au visible le plus proche de leur case ; une seule
suite de numéros est partagée, sans sous-numéros. Le tableau suit ce même ordre.
Les distances sont mesurées entre centres de vias, avant arrondi, et non depuis
la position déportée de l'ovale. Si toute une case est masquée près d'une frontière,
le voisin visible peut être dans la case adjacente ; le préfixe géographique réel
est conservé et ses fantômes sont ordonnés par référence puis par distance.
Les colonnes continuent après Z : AA, AB…

La grille est vue de la face sélectionnée : X à droite, Y vers le haut ;
origine au coin inférieur gauche de l'enveloppe Edge.Cuts de cette vue.
Pour Bottom, X est inversé et les textes sont miroités dans le fichier KiCad
afin d'être lisibles depuis le dessous. Un repère C2.1 peut exister sur chaque
face : son tableau Top ou Bottom l'identifie sans ambiguïté.

Le tableau comporte cinq colonnes : **Repère, Net, Label imprimé, X (mm), Y (mm)**.
**Label imprimé** vaut `true` si le repère est dessiné, `false` sinon.
Les coordonnées de la vue choisie sont arrondies au dixième de millimètre.
Seul **Top** ou **Bottom** figure au-dessus du tableau, sans autre commentaire.
La case se lit dans le repère (A3.1 = case A3) ; les données techniques restent internes.
Un fichier existant n'est réécrit que s'il est déjà un tableau Kicad_Via de la
même face. Une liste Bottom n'écrase pas une liste Top.

## Copier les labels et dessins vers Fusion

1. **Générer / remplacer** le repérage pour obtenir les nouveaux noms **A3.1**
   (les objets déjà présents ne sont pas renommés au chargement du plugin).
2. Cliquer **Copier vers Fusion…**, choisir le BRD/FBRD source correspondant à
   la carte et le dossier de sortie, puis **Préparer pour Fusion**.
3. Cliquer **Copier la commande RUN**, coller cette commande dans le PCB cible
   Fusion et la lancer. L'ULP contrôle les composants de la cible avant de proposer
   l'ajout sur **SilkscreenTop** (Top) ou **SilkscreenBottom** (Bottom) dans Fusion 360.

Le même parcours que [kicad_plugin_fusion2kicad](https://github.com/fca1/kicad_plugin_fusion2kicad)
est repris : fichier ULP local, commande RUN visible et copie sur clic uniquement.
Aucune connexion à Fusion, aucun changement du PCB pendant la préparation.
Le BRD/FBRD fournit le repère natif ; l'alignement est vérifié sur les origines
composants (tolérance 0,01 mm). Au moins deux origines distinctes sont requises.
Les coordonnées entières du tableau ne sont pas utilisées pour dessiner.

L'export prend l'aperçu courant de la face, sinon son dernier repérage fusionné.
Il conserve les ajustements manuels des objets reconnus par UUID. Les lettres,
ovales, traits de rappel et grille sont copiés comme traits graphiques, avec la
police vectorielle KiCad et son miroir. Les arcs sont discrétisés à 5 µm d'erreur
de corde maximale. Les textes à contours et dessins autres que segments/arcs
sont refusés. Les labels deviennent des traits, pas des textes Fusion éditables.

Un dossier neuf conserve chaque livraison. La copie est **additive** : lancer
une seule fois pour éviter les doublons ; elle ne remplace aucune ancienne
sérigraphie Fusion et ne touche pas aux pistes, vias, pads ou nets. Les contrôles
portent sur l'implantation source et cible, pas sur l'ensemble de leurs règles.
La génération est testée ; l'application de l'ULP corrigé dans Fusion 360 reste
à valider. Les noms de couches sont contrôlés avant de créer le SCR ; le nom réel
trouvé est utilisé par `LAYER`. Une absence de couche, une ambiguïté et un nombre
de composants incorrect sont signalés séparément. Les contrôles d'implantation
restent actifs. Fusion 360 est le logiciel cible ; BRD/ULP/SCR ne désignent pas
une ancienne version d'un autre produit.
Références Autodesk : [RUN](https://help.autodesk.com/cloudhelp/ENU/Fusion-ECAD/files/ECD-CLI-R.htm),
[UL_BOARD](https://help.autodesk.com/cloudhelp/ENU/Fusion-ECAD/files/ECD-ULP-BOARD.htm),
[couches Fusion 360 et commande LAYER](https://help.autodesk.com/cloudhelp/ENU/Fusion-ECAD/files/ECD-CLI-L.htm).

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

Les textes Bottom de la couche utilisateur restent lisibles avec **Flip View**.
Le miroir physique est appliqué au transfert vers B.SilkS et à l'export Fusion,
sans modifier l'aperçu lors de l'export. Régénérer les anciens aperçus pour
actualiser leur orientation.
