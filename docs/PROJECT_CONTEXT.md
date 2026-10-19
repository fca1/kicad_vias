# Contexte — Kicad_Via

Mémoire initialisée le 18 octobre 2026 avec la compétence epi-git, dans le dépôt
Kicad_Via, distinct du dépôt Autodesk depuis lequel la conversation a commencé.
Distant : https://github.com/fca1/kicad_vias ; visibilité publique vérifiée par
GitHub CLI. Son commit initial `8327aae` ne contient qu'un README ; son historique
est conservé par fusion, sans réécriture. La PR nº 1 issue de `codex/kicad-via` est intégrée à `main` le 18 octobre 2026.

## But et exigences autorisées

Repérer des accès de test via sur un PCB KiCad ouvert. Un seul via découvert et
accessible par net et par face ; ignorer les nets sans accès disponible. Top et
Bottom ont des listes indépendantes. L'accessibilité est estimée à partir des
masques effectifs et des enveloppes 2D des composants, sans qualification 3D.

Dialogue : face, hauteur du label, couche utilisateur libre ou déjà gérée,
choix du tableau .nd/.md, grille et allègement des labels proches. Renommer la
couche Kicad_Via_TOP/BOTTOM, garder la possibilité d'ajustement manuel puis de
fusion vers F.SilkS/B.SilkS. Préserver tout contenu étranger, routage et masque.
Bouton avec icône via/drapeau dans le bandeau. Installer après chaque commit.

Repères par cases de 20 mm : C2.1, colonne C, ligne 2, accès 1 ; A…Z puis AA…
Origine au coin inférieur gauche de l'enveloppe Edge.Cuts vue de la face choisie,
X vers la droite, Y vers le haut ; Bottom inverse X. Ovale et trait de rappel ;
placement évitant composants, ouvertures de masque et sérigraphie. Depuis la
correction autorisée du 18 octobre 2026, chercher d'abord un ovale et son rappel
libres pour chaque accès. Le masquage de proximité n'est permis qu'après échec
des placements, si l'option est active et qu'un accès imprimé est à moins de
3 mm. L'accès masqué reste au tableau ; sans ce repli, la génération est refusée.
Taille par défaut 0,65 mm, plage 0,4–2 mm.

Première correction du 18 octobre 2026 (remplacée ensuite) : réduire le tableau à Repère, Net,
Case, X (mm), Y (mm), sans décimales. Conserver les coordonnées de la grille
vue de la face, retirer coordonnées natives, diamètres, perçage, présence du
label, voisin, écarts et UUID de l'affichage. Ces données restent internes.

Dernière correction du 18 octobre 2026 : supprimer Case, passer les coordonnées
au dixième de millimètre et ne garder que Top ou Bottom comme titre. Le tableau
comportait alors Repère, Net, X (mm), Y (mm), sans commentaire ni marqueur technique.
Reconnaître l'ancien format pour le remplacer, tout en refusant l'autre face et
les fichiers étrangers. Les coordonnées précises restent dans le registre.

## Architecture vérifiée dans le code

- `plugin/Kicad_Via/action.py` : ActionPlugin natif, dialogue wxPython et bandeau.
- `model.py` : options et coordonnées ; `geometry.py` : sélection et placement.
- `service.py` : propriété UUID, génération, fusion et tableau à quatre colonnes.
- Registre local `%LOCALAPPDATA%/Kicad_Via/ownership` : nécessaire pour reprendre
  les objets après réouverture ou sur un autre poste. Pas de simple adoption par nom.
- `tools/install_plugin.py` : archive du commit, sauvegarde et vérification SHA-256.
- `tools/adopt_previous.py` : migration bornée sur preuves de l'ancien repérage.
- `tests/test_plugin.py` : 30 tests natifs, dont interface réelle wxPython.

KiCad audité : 10.0.7 sous Windows, Python natif avec wxPython 4.3.1 et Shapely
2.2.0. Utiliser IPC au maximum pour lecture de la carte en mémoire et rechargement ;
le renommage des couches a nécessité l'API native sur cette version.
Une installation fraîche ne configure pas automatiquement le hook local Git.
La portabilité vers d'autres versions et systèmes n'est pas vérifiée.

## Évolution du 18 octobre 2026 — transfert graphique Fusion

Demande explicite : remplacer le tiret par un point, ajouter le parcours RUN et
presse-papiers du projet kicad_plugin_fusion2kicad, puis fusionner PR nº 1 vers
main et réinstaller le commit fusionné. Implémentation autonome dans `fusion.py`,
avec dialogue secondaire dans `action.py`. Les traits natifs de la police KiCad
conservent positions, rotations et miroir ; les arcs sont discrétisés à 5 µm.
BRD/FBRD choisi pour calculer X_fusion=X_KiCad-dx et Y_fusion=sy-Y_KiCad ; chaque
origine composant est contrôlée. L'ULP vérifie composants, positions, angles,
miroirs, empreintes et couche tPlace/bPlace avant de proposer une copie additive.
Aucune application automatique à Fusion. Copier uniquement sur clic utilisateur.
Exécution ULP dans Fusion non qualifiée à ce stade ; préparation et géométrie
vérifiées sur copies. Voir [historique de la demande](HISTORY/2026-10-18_fusion_labels.md).

Le parcours de référence a été lu dans le dépôt local `script_krt_fusion`, fichiers
`plugin/passerelle_fusion/action.py`, `service.py` et
`tools/kicad_routage_vers_fusion.py` le 18 octobre 2026 ; ce n'est pas une copie
complète du convertisseur, ni une dépendance au plugin installé. Le dépôt public
correspondant est https://github.com/fca1/kicad_plugin_fusion2kicad.

## Évolution du 18 octobre 2026 — placement avant masquage

Cause confirmée dans geometry.prepare : la sélection d'un voisin proche précédait
la recherche et l'instruction `if neighbor is None` empêchait toute tentative de
placement pour les accès concernés. La capture et le registre local ont révélé
le cas ; la copie IPC de la carte a permis de comparer avant/après. La proximité
est maintenant consultée uniquement après épuisement de la recherche de placement.
Le choix d'un seul via par net reste identique ; cette correction ne crée pas
un repère supplémentaire sur chaque via du même net. La recherche reste bornée
aux placements existants (1,5–10 mm, angles de 15°, rappel direct ou à un coude).

28 tests natifs passent, dont deux accès proches tous deux imprimés quand la place
existe, et repli sans placement possible (option, rayon et voisin imprimé requis).
Sur copie récente : 18 accès, 14 puis 16 labels ; E2.2 et F2.4 rétablis. Génération
et fusion sur copie vérifiées ; la carte originale n'est pas modifiée par ces essais.
Historique : [diagnostic et autorisation](HISTORY/2026-10-18_diagnostic_labels_proches.md).

## Évolution du 18 octobre 2026 — trait centré et numéros des fantômes

Demande utilisateur : prolonger le rappel jusqu'au centre du via, y compris dans
son ouverture de masque. Causes de l'ancien arrêt confirmées dans le code :
retrait radial explicite et obstacle de masque appliqué aussi à la fusion.
Le plan associe maintenant chaque segment de rappel au UUID du via désigné,
conservé dans `leader_vias` du registre. Génération et fusion utilisent la même
exception locale. Les obstacles fixes réels sont réintroduits après assouplissement
de leurs marges au centre : ne pas supprimer une pastille ou une inscription
superposée en soustrayant naïvement un disque à l'union globale. La copie réelle
a révélé un texte assez proche pour bloquer sa marge sans contact physique ;
ce cas est testé. Les anciens registres sans `leader_vias` restent lisibles.

Autre demande : colonne booléenne Label imprimé et numéros des fantômes par
distance. Clarification explicite de l'utilisateur : E2.1 visible, puis E2.2,
E2.3 non visibles, puis nouveau visible E2.4, dans la même case. Pas de E2.1.1.
Modèle `number_unprinted` : groupes visibles dans leur ordre spatial, rattachement
des fantômes au visible le plus proche de leur case, puis tri par distance entre
centres précis ; une seule suite entière par case. Le tableau est regroupé de
la même façon et ajoute true/false. Les noms dessinés sont mis à jour après ce
classement, avec ovales dimensionnés pour tous les suffixes possibles de la case.
Cas limite sans aucun visible dans une case : garder le préfixe de cette case,
prendre la référence visible la plus proche à l'extérieur et trier ses fantômes
par référence puis distance. Ce repli existant évite de refuser toute la génération
au bord des cases. Ni choix de via par net ni positions des accès ne sont modifiés.

28 tests réussis et validation sur la copie IPC antérieure de la carte : centres,
texte dessiné et tableau cohérents, ordre et booléens, sauvegarde puis fusion.
Aucun enregistrement automatique de l'original. Pour actualiser les repères déjà
créés, utiliser Générer / remplacer après rechargement du plugin.
Source : [échange et clarification](HISTORY/2026-10-18_centres_et_fantomes.md).

## Correction du 19 octobre 2026 — couches Fusion 360

Cause confirmée : l'ULP fourni cherchait exactement tPlace alors que l'extraction
courante Fusion contient SilkscreenTop (21) et SilkscreenBottom (22), sans tPlace.
Le contrôle trouvait zéro couche puis annulait ; le message regroupait en outre
les erreurs de couche et de nombre de composants. La carte a 88 composants,
comme l'ULP. Ne pas imputer cette annulation à une autre carte sans preuve.

Autorisation utilisateur obtenue après présentation de ces preuves : corriger
plugin et ULP existant, tester, mémoire epi-git, commit, push main et réinstallation.
Le générateur cible uniquement les couches actuelles Fusion 360. L'ULP conserve
le nom de couche résolu à l'exécution pour LAYER, refuse absence/ambiguïté, et
préserve les erreurs de composants précédemment constatées. La fonction
repair_legacy_ulp répare les exports erronés connus du plugin avec sauvegarde
exacte et publication atomique ; elle n'ajoute pas une cible produit historique.

30 tests réussis, dont Top/Bottom, absence de l'ancien nom dans les nouveaux ULP,
réparation sans modifier composants/traits, sauvegarde exacte, refus de fichier
étranger ou déjà corrigé. Copie du fichier fourni vérifiée : 88 composants,
1 353 commandes de traits inchangées ; SilkscreenTop détectée une fois dans
l'extraction Fusion récente. L'application du script corrigé dans Fusion reste
à valider par son exécution manuelle ; aucun PCB Fusion n'a été appliqué par l'agent.

Rappel global demandé le 19 octobre : Fusion 360 a toujours été l'environnement
utilisateur. Règle ajoutée à `%USERPROFILE%/.codex/AGENTS.md`, puis reprise dans
les nouvelles consignes utilisateur de ce chat. Les formats BRD/ULP/SCR et la
racine XML `eagle` ne prouvent pas l'usage d'un ancien logiciel.
Sources : ULP fourni (lecture locale, non publié), extraction Fusion du 19 octobre
2026 à 00:06:11 UTC, diagnostic local des couches déjà disponible, documentation
Autodesk LAYER actuelle, tests et [échange](HISTORY/2026-10-19_couches_fusion360.md).

## Sources et couverture

1. Code et tests locaux ; commits `b8cce99`, `f83bc54` ; README, décisions et état
   déjà présents. Relus le 18 octobre 2026 ; preuves historiques distinctes d'un
   nouveau contrôle. Les essais sur copie ne prouvent pas la fabrication.
2. Extraits exacts des demandes utilisateur visibles dans ce chat, conservés dans
   [HISTORY](HISTORY/2026-10-18_demande_plugin.md). Dates individuelles antérieures
   inconnues ; collecte le 18 octobre 2026. Pas de transcription intégrale.
3. Contexte condensé disponible pour les étapes intermédiaires : source de reprise,
   pas un verbatim. Non transformé en messages assistant inventés.
4. README distant au commit `8327aae`, lu par Git le 18 octobre 2026.
5. Compétence locale epi-git, lue depuis le chemin fourni par l'utilisateur.

Les réponses assistant intermédiaires et journaux complets des étapes antérieures
ne sont pas disponibles mot pour mot. Pour compléter cet historique, demander
l'export original du chat. La liste exhaustive des autres conversations n'est pas
visible ; aucune affirmation d'exhaustivité. Les consignes d'autres projets et
leurs données ne sont pas archivées ici. `.local/`, PCB, sorties utilisateur et
registres de propriété restent hors Git. Voir [STATUS](STATUS.md) et
[DECISIONS](DECISIONS.md) pour les résultats et leurs limites.

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
