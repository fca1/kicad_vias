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

## 18 octobre 2026 — Rappel au centre et liste des fantômes

Le trait doit atteindre le centre même si le vernis est ouvert. L'ancien retrait
radial et le contrôle de masque expliquaient son arrêt avant le via. Désormais,
les traits reçoivent une association UUID vers leur via dans le registre. Leur
ouverture est exemptée à la génération et à la fusion ; les autres vias restent
protégés. Au centre, relâcher les marges des obstacles fixes en conservant leurs
contours réels. Preuve : un texte voisin bloquait la marge du départ sans contact
physique ; test ajouté. Une pastille/inscription superposée ne doit jamais être
retirée avec l'exception. Anciennes entrées du registre sans association compatibles.

L'utilisateur demande aussi Label imprimé booléen. Ajouter true/false, garder X/Y
à 0,1 mm et le titre seul. Reconnaître l'ancien tableau à quatre colonnes pour
permettre sa mise à jour ; la séparation des faces reste contrôlée.

Clarification utilisateur : il refuse la proposition E2.1.1. Dans chaque case,
E2.1 visible est suivi de E2.2 et E2.3 fantômes par distance croissante au via
portant E2.1, puis d'un prochain visible (E2.4). Garder une seule suite par case.
Rattacher les fantômes au visible le plus proche de leur case ; maintenir l'ordre
spatial des groupes visibles, trier les fantômes par distance précise. Réserver
l'encombrement des suffixes avant placement pour que le renommage n'élargisse pas
un texte au-delà de son ovale ; synchroniser les textes dessinés et le tableau.
Si une case ne possède aucun visible, conserver le repli vers un visible adjacent,
le préfixe de case réel et l'ordre par référence/distance. Ce cas existe sur la
copie réelle : interdire ce repli ferait échouer toute la génération.

28 tests natifs passent : centres Top/Bottom après sauvegarde/fusion, protection
des autres ouvertures et obstacles superposés, assouplissement local sans collision
réelle, numérotation où ordre spatial et distance diffèrent, cases adjacentes,
true/false dans le tableau. Validation finale sur copie IPC antérieure : centres,
numéros dessinés et tableau, ordre des fantômes et fusion vérifiés. Les sorties
et données de carte restent privées dans .local. Le rechargement à chaud dépend
encore du canal IPC actuellement détenu par le gestionnaire ; ne pas le déclarer
réussi sans réponse RAS_OK.

## 19 octobre 2026 — Annulation ULP : couches Fusion 360

Diagnostic avant code : le fichier fourni contient L.name=="tPlace" et LAYER
tPlace ; l'extraction Fusion de la même carte contient SilkscreenTop et
SilkscreenBottom, pas tPlace. Le diagnostic local des couches confirme ces noms.
L'ULP et la carte comptent 88 composants. Cause de couche établie, pas simple
hypothèse tirée d'un message générique. Autorisation explicite reçue pour corriger
plugin et livrable existant, tester, mémoire, committer, pousser main et réinstaller.

Une première proposition de compatibilité de noms a été abandonnée après rappel
utilisateur : tous ses projets utilisent Fusion 360 depuis toujours. Enregistrer
ce rappel globalement dans .codex/AGENTS.md ; ne plus présenter une ancienne
version d'EAGLE comme son environnement. Cibler SilkscreenTop/SilkscreenBottom,
résoudre le nom réel à l'exécution puis l'utiliser dans LAYER. Les références aux
noms erronés ne restent que dans l'outil de réparation de nos propres exports.

Séparer erreur d'implantation, nombre de composants, absence ou ambiguïté de
couche. Ne pas remplacer une erreur d'implantation par le message générique de
couche. Avant correction du livrable utilisateur, sauvegarder ses octets exacts.
Refuser toute structure inconnue ou déjà corrigée. Garder toutes les coordonnées,
les références et les 1 353 commandes de traits du fichier fourni à l'identique.
L'ULP corrigé reste additif et soumis à confirmation d'application dans Fusion.

30 tests réussis (4,002 s). Essai sur copie du livrable et comparaison avec
l'extraction Fusion récente : SilkscreenTop résolue une fois, 88 composants,
1 353 traits inchangés, sauvegarde exacte. L'exécution réelle dans Fusion après
correction n'est pas encore confirmée. Aucun fichier de carte n'est publié.

Livrable utilisateur effectivement réparé après installation du commit 7cdb491,
au même chemin. Sauvegarde originale exacte vérifiée ; références/composants et
1 353 commandes de traits conservés. Le manifeste de réparation reste dans .local,
avec chemin de sauvegarde et empreintes avant/après. L'utilisateur peut relancer
sa même commande RUN. Pas de lancement ni d'application automatique à Fusion.

## 19 octobre 2026 — Nouveau signalement Top / Bottom, diagnostic ouvert

L'utilisateur signale une annulation pour manque de place sur Top et des textes
Bottom en miroir. Le code confirme une annulation globale si un placement échoue
sans voisin déjà imprimé à moins de 3 mm ; recherche bornée à 10 mm. Le miroir
Bottom est explicitement programmé pour la lecture depuis le dessous.
Le via bloquant, son obstacle et le point de vue Bottom ne sont pas établis.
Message exact et orientation de vue demandés. Aucun correctif décidé ou appliqué.
Source : [extrait et diagnostic](HISTORY/2026-10-19_blocage_top_miroir_bottom.md).

## 19 octobre 2026 — Placement partiel et lecture Bottom corrigés

Autorisation explicite après signalement C1.2 : corriger, mémoire, commit,
push main, réinstaller. Le manque de place ne bloque plus la génération :
chaque accès sans ovale/rappel libre reste en fantôme (Label imprimé=false),
sans condition de proximité. Numérotation après tous les placements ; distance
au visible de la case conservée. Sans aucun visible : ordre spatial stable,
voisin vide, groupe vide reconnu pour permettre la régénération.
L'ancienne case de masquage dans le dialogue est supprimée ; les paramètres
Python historiques restent acceptés sans conditionner ce repli obligatoire.

Cause Bottom établie dans le moteur KiCad 10.0 et par IsSideSpecific natif :
Flip View conserve le miroir des textes User. Aperçu User désormais non miroir,
miroir physique appliqué au transfert B.SilkS et sur copie pour l'export Fusion.
Ne pas appliquer un second miroir à l'aperçu ; régénérer les anciens objets.
31 tests natifs réussis, dont génération partielle, tout fantôme/régénération,
orientation Bottom et export préservant la carte. Aucun PCB utilisateur enregistré.
La vérification visuelle du résultat dans l'éditeur ouvert reste côté utilisateur.
Source : [échange et preuves](HISTORY/2026-10-19_blocage_top_miroir_bottom.md).

## 19 octobre 2026 — Analyse des performances, sans changement de code

L'utilisateur confirme le fonctionnement et demande pourquoi la génération est
lente. Mesures sur la capture antérieure privée placement_prioritaire, avec
le code 5eb1bce ; pas sur la carte actuellement ouverte. Options Top par défaut,
18 accès, 16 labels. Génération complète sur copie en mémoire, registre copié
et sortie temporaire isolés : 7,720 s, dont prepare 7,509 s ; tableau 0,00073 s,
registre 0,00165 s. Le chargement de la carte est hors chronométrage.

Mesure des unions géométriques par appelant : leader_obstacles 18 appels/2,630 s,
route_occupied 18/1,435 s, occupied après label 16/1,267 s, occupied pour les
lettres/chiffres de grille 12/0,975 s. Ces quatre postes coûtent 6,308 s,
soit environ 82 % du temps total. Toutes unions : environ 6,74 s (87 %).
Profil cProfile séparé : 7,793 s ; 1 648 positions candidates, 6 042 buffers,
3 069 intersects. Les prédicats intersects eux-mêmes coûtent seulement 0,034 s
cumulée ; number_unprinted environ 0,0001 s. Ce sont les reconstructions de
l'ensemble des obstacles, plus que les recherches de collision, qui dominent.
Bottom de cette capture possède zéro accès admissible : ses 0,74 s ne sont
pas comparables à la génération Bottom courante de l'utilisateur.

Cause confirmée dans geometry.py : union de fixed.difference(local), solid et
toutes les autres ouvertures pour chaque via ; nouvelle union avec protections ;
réunion de toute la géométrie occupied après chaque label et texte de grille.
Run exécute ce travail synchroniquement dans le callback wx, avec BusyCursor
mais sans progression : cela ajoute une impression de blocage, non chronométrée.

Pistes proposées, non implémentées : garder séparés obstacles fixes, ouvertures
et protections ajoutées ; index spatial pour tester uniquement les obstacles
proches, exception du via locale ; éviter les unions globales répétées et
préparer les géométries réutilisées. Préserver ordre, marges, centres des rappels,
numérotation et résultats avant de comparer les temps. Aucun facteur de gain
promis sans prototype mesuré. Une progression améliorerait le retour visuel,
sans accélérer le calcul. Pas de réduction du nombre de candidats en première
intention. Données de mesure privées dans .local/performance_analysis.json et
profile_Top.prof ; aucun PCB original modifié. Aucun commit ou déploiement demandé
pour cette analyse. Documentation uniquement actualisée.

## 19 octobre 2026 — Optimisation mesurée et placement préservé

Demande explicite : optimiser sans changer le placement, mesurer, mémoire epi-git,
commit, push main et réinstaller. Cause déjà mesurée : unions globales répétées.
CollisionIndex conserve les géométries séparées, filtre leurs boîtes par STRtree
puis applique intersects exact sur des géométries préparées. Les nouvelles
protections sont ajoutées séparément. La différence locale autour du via,
les marges, les candidats, leur ordre et la numérotation restent identiques.
Le contrôle de fusion vers Silk conserve sa géométrie précédente.

Validation : 33 tests natifs réussis (4,648 s), dont équivalence à l'union sur
contacts de frontières, obstacles chevauchants, ensembles vides et ajouts.
Comparaison directe avec geometry.py au commit 5eb1bce : mêmes lignes de tableau,
positions, textes, miroirs, tailles, traits, arcs, grille, protections géométriques
et associations traits/vias ; seuls les UUID nouvellement créés sont ignorés.
Six cas synthétiques Top/Bottom aux tailles 0,4/0,65/1,2 mm sont identiques.
Sur la capture réelle antérieure : Top 18 accès, 16 labels, 2 fantômes,
comparaison identique avec grille à 0,65 mm et sans grille à 0,4 mm.
Bottom sur cette capture n'a aucun accès admissible : ne pas en extrapoler
un gain Bottom utilisateur. Aucun original ni carte ouverte modifié.

Mesures à trois répétitions alternées avant/après, médianes : calcul Top avec
grille 7,393 -> 1,021 s (x7,24) ; Top 0,4 mm sans grille 6,269 -> 0,972 s.
Génération complète Top par service.generate sur copie, registre et tableau
isolés : 7,676 -> 1,241 s (x6,18, -83,8 %). Tableau identique octet pour octet.
Chargement du PCB et interface graphique exclus du chronométrage. Pas de garantie
de facteur constant sur toute carte. La boucle wx reste synchrone.

Outil reproductible : tools/benchmark_placement.py ; référence Git explicite,
lecture de copie PCB, signature exacte et médianes, aucune sauvegarde de carte.
Rapports privés : .local/benchmark_placement.json et benchmark_complete.json.
Installation par hook depuis l'archive du commit ; manifeste et SHA vérifiés
après commit dans .local/last_install.json. Recharger le plugin dans l'éditeur
pour utiliser le code nouveau ; aucun rechargement à chaud prétendu sans preuve.
Source : [analyse et autorisation](HISTORY/2026-10-19_performances.md).

## 19 octobre 2026 — Audit du rechargement et trajectoire IPC

Demande : recharger par IPC sans fermer la carte et privilégier IPC pour préparer
l'abandon de l'API native actuelle. Version répondant : KiCad 10.0.7.
Premier appel common.API.pluginsReload refusé Busy ; après fermeture des boîtes
par l'utilisateur, réponse RAS_OK. Cela ne prouve PAS le rechargement Kicad_Via.
Audit source KiCad branche 10.0 : COMMON_CONTROL::ReloadPlugins appelle seulement
API_PLUGIN_MANAGER::ReloadPlugins ; le bouton des préférences Action Plugins
appelle aussi SCRIPTING_TOOL::ReloadPlugins. Correction des affirmations
antérieures : cette action IPC ne recharge pas le plugin natif SWIG actuel.
Aucun PCB fermé ou enregistré. Le rechargement natif reste à faire par le bouton
des préférences de l'éditeur, sans fermer la carte.

Le plugin n'utilise pas IPC au maximum : aucun import kipy dans le paquet ;
action, service, geometry et fusion dépendent de pcbnew. IPC sert aux opérations
externes de mise au point. Le renommage de couches était une limite observée,
mais ne justifie pas à lui seul tous ces couplages. Orientation à préparer :
modèle de données indépendant, calcul Shapely indépendant de pcbnew, adaptateur
KiCad pour lectures/écritures groupées et transactions, plugin IPC externe avec
plugin.json ; inventaire précis des capacités sur chaque version, repli natif
borné aux fonctions manquantes. Aucune migration de code entreprise ici.
Ne pas supposer la disponibilité future de chaque méthode ni une date de retrait.

Sources consultées :
- https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/
- https://github.com/KiCad/kicad-source-mirror/blob/10.0/common/tool/common_control.cpp
- https://github.com/KiCad/kicad-source-mirror/blob/10.0/pcbnew/dialogs/panel_pcbnew_action_plugins.cpp

## 19 octobre 2026 — Moteur indépendant et sorties Markdown

Autorisation : préparer IPC sans changer le résultat, tests, mémoire, commit,
push main et installation ; remplacer .nd par .md. Réalisé : board_data fournit
le contrat neutre, placement calcule sans pcbnew/wx/kipy, native_adapter capture,
mesure et matérialise le plan. geometry reste une façade de compatibilité.
Le paquet s'importe hors KiCad ; les appels natifs sont aux frontières de carte,
police et application des modifications, plus dans le moteur de placement.
Le plugin est encore natif : le transport IPC complet reste à implémenter et
valider, notamment renommage, contours, métriques, transactions et propriété.
Inventaire de l'interface kipy effectué sans modifier le document ouvert.

36 tests réussis (4,673 s). Test pur avec interdiction d'import des API/GUI ;
parité des métriques aux coordonnées fractionnaires ; anciens .nd conservés et
contrôle d'écrasement .md. Comparaisons exactes à d0d1477 sur copie réelle Top
avec/sans grille et six cas synthétiques Top/Bottom (0,4/0,65/1,2 mm), tous
identiques. Calcul réel Top ~1,03 s ; 18 accès/16 labels. Aucun PCB original
modifié. Les tableaux futurs et chemins mémorisés utilisent .md, sans effacer
les .nd existants. Registre mis à jour avec le nouveau chemin à la génération.

Détails et limites : [architecture IPC](IPC_MIGRATION.md).
Sources : [échange](HISTORY/2026-10-19_preparation_ipc.md), code, tests,
.local/benchmark_ipc.json (rapport privé). Installation exacte depuis commit
par le hook ; SHA et empreintes dans .local/last_install.json. Rechargement
natif via préférences, pas common.API.pluginsReload.


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


## 19 octobre 2026 — Adaptateur IPC opérationnel sur KiCad 10

Demande explicite : poursuivre IPC sans changer le placement, mémoire epi-git,
commit, push main et réinstallation. Réalisé : écritures de dessins par lots,
lecture de contrôle, couches actives/visibles, transactions, coordinateur réseau
hors GUI et contrôle de chaque statut IPC. Les noms de couches et la création
finale des groupes restent natifs, comme la capture/métrique exacte et Fusion.
Voir docs/IPC_MIGRATION.md pour les limites, notamment le groupe créé après
push et donc hors undo IPC. Il s'agit d'un hybride KiCad 10, pas encore d'un
plugin autonome compatible KiCad 11.

Validation : 47 tests réussis ; comparaison stricte au placement d0d1477 sur
copie réelle (18 accès/16 labels) ; créations Top/Bottom, remplacement, fusion
Bottom et annulation IPC réels sur carte synthétique séparée. Géométrie relue
exacte : 400 dessins Top et 411 Bottom. Groupe natif validé sur copie relue ;
parcours GUI complet à tester après rechargement. Aucune écriture sur le PCB
utilisateur. Dépendances IPC épinglées et installation depuis archive Git.

Question nightly ajoutée : le code master officiel du 19 octobre corrige la
résolution des membres de groupe dans la transaction, expose l'enveloppe
Edge.Cuts et FocusOnItems. Analyse de code uniquement, aucune nightly installée
ou testée. SWIG déjà retiré des nightlies : prévoir un lanceur externe et finir
les replis. Le correctif Markdown fb30f9f du travail parallèle est préservé et
inclus dans le push de main. Publication/installation effectives à vérifier
avec HEAD, origin/main et .local/last_install.json après le commit.
Source : échange courant partiel et code/tests ; aucune transcription complète
supplémentaire accessible. Historique : 2026-10-19_adaptateur_ipc.md.


## 19 octobre 2026 — Vérification de la nightly installée

Demande : recharger puis tester depuis le bouton sur la carte de test ;
l'utilisateur précise explicitement « Utiliser une nightly 10.99 ».
Installation trouvée : 10.99.0.2520.g89476220a8, distincte de KiCad 10.0.7.
Éditeur nightly lancé et version visible vérifiée. Kicad_Via absent de son
répertoire de plugins. Le paquet ffdeaa9 ne possède pas de plugin.json et son
lanceur action.py hérite de pcbnew.ActionPlugin : le parcours du bouton n'est
pas disponible dans le système de plugins IPC de cette nightly.
Ne pas confondre cette build installée avec master 7d2afb0 examiné précédemment.
Les DLL Python présentes dans le dossier ne suffisent pas à prouver la présence
de l'ancienne interface : aucun pcbnew.py trouvé dans l'installation.
Aucun rechargement réussi, aucune génération ni écriture de carte dans 10.99.
Le parcours complet demandé reste non validé. Étape nécessaire : porter le
lanceur et l'interface vers un processus IPC externe, remplacer les replis
natifs, puis vérifier leur parité sur cette build précise avant test du bouton.


## 19 octobre 2026 — Portage externe nightly autorisé

L'utilisateur autorise l'adaptation (« go »), puis accepte explicitement le
renommage manuel initial des couches comme compromis temporaire. Réalisé en
code : manifeste et bouton IPC, dialogue Tkinter, service/capture/métriques/
matérialisation externes, fusion et export Fusion IPC. Le moteur est inchangé.
54 tests réussis ; parité exacte du plan sur copie réelle et six cas synthétiques.
Essais réels API génération/fusion Top et Bottom réussis sur carte synthétique.
Les limites de géométrie et la finalisation des groupes propre à la build 2520
sont détaillées dans IPC_MIGRATION.md. Le test depuis le bouton est encore à
faire après le commit d'installation ; aucun résultat GUI réussi n'est annoncé.


Validation du bouton nightly : premier chargement refusé car le caractère _ dans
l’identifiant technique est interdit par API_PLUGIN::IsValidIdentifier dans
89476220a8. Identifiant corrigé en com.github.fca1.kicad-via, nom affiché inchangé.
Test de régression ajouté ; validation graphique encore en cours.


## 19 octobre 2026 — Installation et validation graphique en cours

55 tests passent après correction du manifeste. Les commits 86f06a4 puis
 d869773 ont été installés par archive Git sur 10.0 et 10.99 avec contrôle SHA-256.
Le rechargement IPC retourne RAS_OK dans la nightly 10.99.0-2520 ; le bouton
via/label apparaît désormais dans la barre d’outils de la carte synthétique.
L’environnement Python 3.12 créé par KiCad était incomplet (pip seul) : les
requirements du paquet committé ont été installés avec son propre Python ;
les imports externes ont été vérifiés, puis les plugins rechargés.
La cause de cet arrêt initial de préparation de l’environnement reste inconnue.

Le parcours graphique n’est pas encore validé : aucune fenêtre externe observée
après les tentatives de clic, puis l’outil signale une interaction utilisateur.
Ne pas assimiler ces tentatives à un lancement réussi. Une disponibilité de la
fenêtre a été demandée ; prochaine étape : bouton, génération et fusion sur la
carte synthétique. Les validations API Top/Bottom restent acquises.
Aucune sauvegarde ni fermeture de la carte utilisateur. Le renommage manuel
initial des couches est accepté uniquement comme compromis temporaire.


## 19 octobre 2026 — Parcours graphique confirmé avec l’utilisateur

Le clic manuel sur le bouton ouvre Kicad_Via — IPC et la connexion affiche la
carte synthétique attendue. L’utilisateur a exécuté génération puis fusion Top,
puis Bottom ; relecture IPC indépendante effectuée après chaque confirmation.
Top : 3 accès/3 labels, 400 objets sur F.SilkS, groupe complet, textes non miroirs.
Bottom : 4 accès/4 labels, 411 objets sur B.SilkS, groupe complet, textes miroirs.
Aucun aperçu résiduel pour les deux faces ; tableaux Markdown distincts présents,
avec les cinq colonnes prévues et les coordonnées au dixième. Cette validation
remplace l’état graphique « à vérifier » des entrées précédentes. Les clics
ont été faits par l’utilisateur, les clics automatisés restant sans effet.
L’export vers Fusion n’a pas été exécuté dans ce parcours graphique.

Question suivante : exposer une interface de commande du plugin lui-même.
Le plugin actuel est client IPC de KiCad ; il n’expose pas de serveur de commandes.
La documentation officielle décrit le lancement des actions déclarées dans
plugin.json, pas un routage général des requêtes vers les plugins vivants.
Une entrée locale dédiée (état, génération, fusion, export) est une proposition,
non implémentée et non autorisée à ce stade. Elle réutiliserait le service existant.
Référence : https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/
