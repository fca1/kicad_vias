# Décisions — 18 octobre 2026

Demande utilisateur : plugin neuf Kicad_Via, petit dialogue Top/Bottom, taille
des labels, choix du tableau .nd, couches libres et renommées, fusion, bouton
avec logo via/label. Numérotation géographique par cases de 20 mm, ovale et
rappel vers chaque via imprimé. Top et Bottom ont des listes indépendantes.
Chaque commit doit entraîner une installation depuis ce commit : hook configuré.

Convention retenue : C2-1 = colonne C, ligne 2, accès 1. Vue de la face choisie,
origine enveloppe Edge.Cuts coin inférieur gauche, X droite/Y haut ; Bottom
inverse X et les textes. Défaut texte 0,65 mm, plage 0,4–2 mm. Grille 20 mm.
Allègement à moins de 3 mm d'un label imprimé ; accès maintenus au tableau.

Plugin Python natif pour le renommage des couches absent d'IPC 10.0.7.
Lecture des contours, masques effectifs et enveloppes d'empreintes native.
Collisions de sérigraphie à partir des traits réels, pas des boîtes de texte :
le cas TP506/MEAS_LED2 a démontré l'excès conservateur de ces boîtes.

Ne pas utiliser BOARD.GetProperties comme registre durable : sur le PCB réel
associé à un projet, SaveBoard vide la propriété créée (constaté avant/après),
alors que le cas synthétique sans projet la conserve. Stockage local indexé
par UUID ; carte et projet non enrichis d'objets techniques. Les fichiers de
propriété sont conservés comme historique, l'état effectif des objets permet
de reconnaître une annulation/rétablissement de fusion. Registre manquant :
couche occupée refusée. Aucune reconnaissance heuristique par nom de couche.

Migration bornée de l'ancien repérage de ce chat : outil adopt_previous.py,
avec preuve JSON, copie antérieure, liste des UUID, géométries et groupe exacts.
Seul le registre est initialisé ; aucune modification de la carte à l'adoption.
Ne pas confondre cette migration spécifique avec une adoption générale de
n'importe quel texte trouvé sur une couche.

Installation initiale b8cce99 depuis archive, bouton observé dans le bandeau.
Cas de reprise supplémentaire reproduit : après fusion, une couche vide gardait
le nom Kicad_Via_TOP et empêchait d'en choisir une autre. Correction limitée à
une ancienne couche source connue du registre et restée vide ; nom rendu puis
réservé sur la nouvelle couche. Sérigraphie fusionnée conservée jusqu'à la
fusion suivante. Test natif de ce cas réussi. Dernière suite : 17 tests.

## 18 octobre 2026 — GitHub et mémoire epi-git

Dépôt fourni par l'utilisateur : fca1/kicad_vias, public, initialement README seul.
Conserver le commit distant 8327aae par fusion avec l'historique local ; publier
sur codex/kicad-via et ouvrir une PR. Ne pas publier les fichiers PCB, tableaux
utilisateur, registre UUID ni répertoire .local. Ajouter PROJECT_CONTEXT et les
extraits disponibles dans HISTORY ; les étapes condensées ne deviennent pas une
transcription intégrale. Un export original reste nécessaire pour l'exhaustivité.

## 18 octobre 2026 — Tableau simplifié à la demande de l'utilisateur

L'ancien export associait coordonnées de vue et coordonnées natives, et exposait
les métadonnées du moteur. Ce format était implémenté dans stage_output, confirmé
par lecture du code ; il dépassait le besoin exprimé de repérage visuel.
L'utilisateur demande de retirer ces informations. Garder uniquement Repère, Net,
Case, X (mm), Y (mm), arrondis sans décimales. Garder les coordonnées de la grille
physique vue depuis Top ou Bottom. Les valeurs précises et UUID restent dans le
registre interne, indispensable à la reprise sûre des objets. La case continue
d'être calculée avant arrondi ; un point proche d'une limite peut donc s'afficher
sur cette limite sans changer de case.
