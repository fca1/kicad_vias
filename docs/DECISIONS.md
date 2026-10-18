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

## 18 octobre 2026 — Résultats de publication et de mise à jour

PR nº 1 ouverte : https://github.com/fca1/kicad_vias/pull/1, branche publiée
codex/kicad-via ; pas de fusion automatique vers main. Le tableau existant a
été simplifié avec sauvegarde privée, 18 accès conservés. Contrôle Top/Bottom
du rendu et de l'arrondi réussi. Les 17 tests restent réussis.
Le refus IPC « busy » venait de deux dialogues ouverts ; fermeture sans
application puis rechargement RAS_OK. Aucun correctif de code pour ce refus.

## 18 octobre 2026 — Noms courts et copie vers Fusion

Demande et autorisation explicites : A3-1 devient A3.1 ; préparer le transfert
des labels et dessins par RUN, avec copie presse-papiers, comme la passerelle
fusion2kicad ; fusionner la PR nº 1 puis réinstaller depuis le commit fusionné.
Le point remplace le tiret dans la géométrie, l'aide et le tableau nouvellement
généré. Le moteur mesure la largeur native du texte pour ajuster aussi l'ovale.
Les repères existants sont mis à jour par Générer / remplacer, pas au chargement.

Exporter uniquement les objets UUID gérés de la face : aperçu prioritaire,
sinon fusionné, avec leurs déplacements manuels. Vectoriser la police par
GetEffectiveTextShape pour éviter les différences de métriques de police ; les
textes Fusion ne sont donc pas éditables comme textes. Arcs discrétisés à 5 µm.
Reprendre l'interaction de la passerelle (préparer, copier RUN, lancer dans Fusion)
sans dépendance de code au convertisseur. Le BRD/FBRD sert à vérifier le repère
des composants ; pas de déduction à partir des coordonnées arrondies du tableau.
Contrôles d'implantation exécutés par l'ULP avant création du SCR et confirmation
d'ajout. Transfert additif ; pas de suppression de sérigraphie cible. Un second
lancement peut créer des doublons. Exécution dans Fusion non vérifiée.

Diagnostic confirmé sur copie IPC : présence simultanée de l'ancien aperçu User.1
et du repérage fusionné, dont la couche User.2 vide garde Kicad_Via_TOP. Le code
ne libérait que la source de l'aperçu et refusait ce nom réservé ailleurs.
Correction : rendre son nom précédent à la source fusionnée uniquement si son
UUID de registre est connu, qu'elle est vide et garde le nom attendu. Les objets
fusionnés restent présents ; rollback restaure aussi le nom si échec. Cas reproduit
et couvert par test natif, en plus des refus de contenu étranger existants.

Validation : 23 tests réussis ; préparation Top/Bottom et après fusion, miroir des
traits, erreur d'arc, FBRD, refus de mauvais alignement, conservation de la carte,
dialogue et copie sur clic. Copie réelle : 18 accès, 14 labels, 1 242 traits pour
Fusion. Tous fichiers de validation et sorties de la carte restent dans .local.

## 18 octobre 2026 — Intégration sur main autorisée

La demande utilisateur autorise explicitement la fusion de PR nº 1 et la
réinstallation depuis le commit fusionné. Commit fonctionnel cc278c7 publié,
installé avec dix empreintes vérifiées ; PR mise à jour sur son contenu final.
Fusion locale sans squash et sans réécriture vers main, avec la mémoire finale
incluse dans ce commit de fusion. Installation post-commit depuis son archive,
puis publication main et contrôle de correspondance avec le manifeste installé.
Les empreintes exactes sont dans .local/last_install.json, privé. L'exécution
manuelle de RUN dans Fusion reste la prochaine validation utilisateur.

## 18 octobre 2026 — Dernier allègement du tableau

Après fusion de PR nº 1 sur main au commit 3c0a07c, l'utilisateur retire la
colonne Case (déjà contenue dans A3.1), demande un arrondi à 0,1 mm et seulement
Top ou Bottom en titre. Le format final est Repère, Net, X (mm), Y (mm), avec
une décimale. Supprimer aussi le marqueur et les paragraphes techniques de
l'en-tête ; reconnaître le nouveau titre avec son schéma complet et l'ancien
marqueur pour permettre la migration, en conservant le refus de l'autre face.
23 tests réussis après ce changement, dont régénération et séparation des fichiers.

## 18 octobre 2026 — Priorité au placement du label avant masquage

Autorisation explicite après diagnostic et proposition : modifier, actualiser la
mémoire epi-git, committer, pousser main et réinstaller. Cause établie : le voisin
à moins de 3 mm était recherché avant le placement et court-circuitait toute
recherche d'ovale/rappel, même si une zone libre existait. Déplacer ce choix de
repli après la recherche complète, sans changer la sélection d'un seul via par net.
Le voisin de repli doit effectivement être imprimé ; l'option doit être active.
Sans voisin admissible ou avec l'option désactivée, échec explicite et carte intacte.
Le libellé de l'option précise désormais qu'il s'agit d'un dernier recours.

24 tests passent. Le cas de deux accès proches en espace libre conserve les deux
labels et leurs rappels ; un obstacle interdisant tout départ de rappel vérifie
le masquage conditionnel, le refus sans option et le refus avec un rayon insuffisant.
Sur copie fraîche de la carte obtenue par IPC, 18 accès, 14 puis 16 labels : E2.2
et F2.4 rétablis, génération et fusion réussies sur copie. La recherche reste
bornée à 1,5–10 mm et aux routes directes/à un coude ; aucune garantie de placement
global optimal ni qualification physique 3D. Carte et registres utilisateur
préservés ; copies, diagnostics détaillés et sorties restent dans .local.

Publication et installation du correctif ef54dc3 vérifiées : dix empreintes,
main distant identique. Le rechargement IPC a échoué avec « no handler available »
pour RunAction sur le canal courant ; ne pas confondre installation vérifiée et
rechargement en mémoire. Laisser à l'utilisateur le rechargement depuis KiCad,
sans redémarrer ni enregistrer la carte. La mise à jour documentaire finale
reste elle aussi soumise à l'installation automatique depuis son commit.
