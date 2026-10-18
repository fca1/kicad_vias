# État courant — placement avant masquage — 18 octobre 2026

Correction autorisée et réalisée sur main : chercher un ovale libre et son trait
vers le via avant d'envisager le masquage. Le voisin à moins de 3 mm ne déclenche
plus d'omission anticipée. Repli seulement après échec de recherche, avec option
active et voisin imprimé ; sinon refus explicite de la génération.
L'interface et le README décrivent cette priorité. Un seul accès par net reste retenu.

24 tests natifs réussis (3,780 s), incluant placement de deux labels proches,
repli par obstacle, refus sans option ou sans voisin assez proche. Comparaison
sur copie fraîche IPC : 18 accès, 14 puis 16 labels ; E2.2 et F2.4 rétablis.
Génération et fusion en sérigraphie réussies sur copie. Aucun changement appliqué
à la carte ouverte par ces validations. Pour l'appliquer : Générer / remplacer.

Mémoire epi-git actualisée : contexte, décisions, état et historique du diagnostic,
proposition puis accord explicite. Couverture des échanges antérieurs toujours
partielle, export original non fourni. Commit et push main autorisés ; installation
post-commit depuis son archive, avec SHA et empreintes dans .local/last_install.json.
Le rechargement IPC dépend de l'absence de dialogue modal ouvert dans KiCad.
L'exécution du RUN dans Fusion reste à valider par l'utilisateur.

## Publication et installation vérifiées

Commit fonctionnel ef54dc3 publié sur main et installé : dix fichiers vérifiés
SHA-256, HEAD et référence distante identiques, arbre propre. La présente mise à
jour documentaire est également installée par le hook depuis son propre commit ;
consulter .local/last_install.json pour le SHA final exact.

Le rechargement à chaud n'est pas confirmé : IPC renvoie « no handler available »
pour RunAction ; le gestionnaire et l'éditeur ont été relancés entre les opérations
et le canal courant ne publie plus cette action. L'interface de l'éditeur est
accessible mais les tentatives de sélection du menu n'ont pas ouvert le rechargement.
L'installation sur disque est vérifiée ; recharger les plugins depuis KiCad avant
Générer / remplacer si l'éditeur garde une version déjà chargée. Aucun redémarrage
ni enregistrement automatique du PCB n'a été effectué.

## État précédent et diagnostic initial (historique)

## Analyse du groupe illustré E2-1 — 18 octobre 2026

Question utilisateur : pourquoi les autres vias visibles ne portent-ils pas de
label ? Diagnostic par lecture de geometry.prepare et du registre local du
repérage fusionné, confronté à la copie IPC de validation. Deux règles se
cumulent : un seul via représentatif par net, puis omission du label si un
représentant imprimé est à moins de 3 mm. Le groupe comporte des nets distincts :
un voisin a son représentant choisi ailleurs, un autre a un représentant proche
dont le label est omis. Les deux explications sont établies pour ce repérage ;
la capture utilisateur ne fournit pas à elle seule les nets ni l'échelle.
Au stade du diagnostic, aucune modification de code n’était encore demandée ni réalisée. Une simple
désactivation de l'allègement ne change pas le choix du représentant par net.
Les détails du PCB et la capture restent locaux, hors publication Git.

# État courant — tableau final — 18 octobre 2026

PR nº 1 fusionnée et reconnue MERGED par GitHub, commit main `3c0a07c`.
Installation de ce commit vérifiée : dix fichiers SHA-256, référence distante
identique. Nouvelle correction demandée ensuite sur main : tableau à quatre
colonnes Repère, Net, X (mm), Y (mm), arrondi à 0,1 mm, titre Top ou Bottom seul.
Case, commentaires et marqueur technique ne figurent plus dans le fichier.
23 tests réussis après ce changement (3,530 s), dont séparation Top/Bottom,
réécriture du format, refus des fichiers étrangers et préparation Fusion.

La présente mise à jour est committée sur main ; l'installation automatique
reste liée à ce commit (SHA exact et empreintes dans .local/last_install.json).
Le rechargement IPC nécessite de fermer le sélecteur et les options KiCad s'ils
sont encore ouverts. Les labels existants sont à régénérer pour devenir A3.1.
L'exécution du RUN dans Fusion reste la prochaine validation utilisateur.
Mémoire epi-git actualisée ; historique antérieur toujours partiel.

## État avant la dernière correction du tableau

# État — repères A3.1 et préparation Fusion — 18 octobre 2026

Changements intégrés sur main par le commit de fusion de la PR nº 1 : point à la place du tiret, bouton Copier
vers Fusion, dialogue source BRD/FBRD et sortie, préparation ULP puis copie de
RUN sur clic. Copie graphique Top/Bottom, labels vectorisés, ovales, rappels et
grille, avec alignement source contrôlé. Aucun lancement automatique de Fusion.

23 tests natifs réussis (3,358 s). Vérification sur copie IPC du PCB courant :
18 accès, 14 labels et 1 242 traits ; repères C1.1, C1.2, C2.1… La correction
de reprise aperçu ancien + source fusionnée vide est reproduite et couverte.
Les métadonnées et tableaux de validation restent privés dans .local.

Commit fonctionnel `cc278c7` : installé et contrôlé, dix fichiers vérifiés SHA-256.
La fusion conserve le commit initial distant et tout l'historique de la PR. Cette
mémoire est finalisée dans le commit de fusion ; le hook post-commit installe
ce commit exact. Son SHA complet et les empreintes sont conservés dans
`.local/last_install.json`, et sa version s'affiche dans le dialogue du plugin.
La référence publiée est main ; PR : https://github.com/fca1/kicad_vias/pull/1.

La carte originale n'a pas été modifiée par les validations sur copies. Les
anciens labels KiCad doivent être régénérés via le bouton pour devenir A3.1.
Reprise réelle depuis l'ancien aperçu User.1 vérifiée après correction : 18 accès,
14 labels, 1 242 traits ; User.2 vide retrouve son nom d'origine.

Prochaine action utilisateur : Générer / remplacer, Copier vers Fusion…, choisir
le BRD/FBRD correspondant, Préparer pour Fusion puis Copier la commande RUN.
Exécuter cette commande dans le PCB cible Fusion et contrôler le résultat.
L'exécution de cet ULP dans Fusion reste non qualifiée ; aucune application
réelle à Fusion ni validation de fabrication n'est revendiquée.

Historique de demande : HISTORY/2026-10-18_fusion_labels.md. Couverture toujours
partielle pour les échanges antérieurs ; export original du chat non fourni.

## État précédent (historique)

# État courant — 18 octobre 2026

Branche `codex/kicad-via`, distant public `fca1/kicad_vias`. Le README initial
8327aae est conservé par fusion avec l'historique local b8cce99/f83bc54.
Mémoire epi-git : AGENTS enrichi, PROJECT_CONTEXT créé, décisions complétées,
extraits des demandes et limites de couverture dans HISTORY. Export intégral
du chat manquant ; liste exhaustive des autres conversations non disponible.

Dernière correction demandée : sortie limitée à Repère, Net, Case, X (mm),
Y (mm). Coordonnées de la grille de la face, arrondies au millimètre ; métadonnées
retirées de l'affichage et conservées dans le registre interne. La sélection
et le placement des vias ne changent pas. 17 tests natifs relancés : réussis
le 18 octobre 2026 après cette modification (2,826 s).

Réalisé et vérifié : commit fonctionnel `6e8abaa`, installation par le hook avec
neuf fichiers contrôlés SHA-256 ; contrôle direct du rendu à cinq colonnes,
arrondis et échappement des noms pour Top/Bottom. Tableau existant simplifié :
18 accès conservés, sauvegarde privée dans `.local/` avant remplacement.
Aucune génération ni sauvegarde du PCB original pendant cette mise à jour.

Rechargement IPC initialement refusé car le sélecteur de fichier et le dialogue
Kicad_Via étaient ouverts (observés par Computer Use). Fermeture de ces deux
boîtes par Échap, puis `common.API.pluginsReload` : RAS_OK. Aucun redémarrage.
La mise à jour documentaire suivante réinstalle aussi son propre commit ; la
version exacte installée et ses empreintes sont dans `.local/last_install.json`.

Branche publiée et [PR nº 1](https://github.com/fca1/kicad_vias/pull/1) ouverte,
contrôlée fusionnable. La fusion vers main reste à effectuer après revue.
Mémoire accessible sur cette branche ; les PCB, sorties et registres locaux
ne sont pas suivis. Aucun autre changement de comportement en attente identifié.
Prochaine action : revue de la PR ; compléter l'historique si un export du chat
est fourni. Les preuves ci-dessous restent un historique des étapes antérieures.

## État précédent conservé comme preuve historique

# État — 18 octobre 2026

Implémentation préparée et vérifiée : moteur de placement, gestion des couches,
regroupement, génération/remplacement et fusion Top/Bottom, tableau .nd/.md,
dialogue natif 660 × 404 pixels, icônes clair/sombre et installation post-commit.

17 tests natifs réussis : coordonnées et colonnes au-delà de Z, propriété des
couches, contenu étranger, changement de couche, échec d'export avec rollback,
persistance, séparation Top/Bottom, masques/corps, ovale/rappel, proximité,
fusion/remplacement et refus de collisions après déplacement manuel.
Test wx réel des options Top/Bottom, tailles, sorties séparées et bouton de
fusion ; changement de couche après fusion également couvert.

Copie native du PCB courant obtenue par IPC : 117 vias, ancien repérage User.1
conservé. Génération sur User.2 libre, renommée Kicad_Via_TOP : 18 accès,
14 labels. Enregistrement puis fusion F.SilkS sur la copie réussis ; aperçu
SVG natif rasterisé examiné. Carte utilisateur non modifiée par ces essais.
Boîte d'options affichée et examinée via Computer Use ; contrôles lisibles.

Premier commit b8cce99 installé automatiquement par le hook : neuf fichiers
vérifiés SHA-256, manifeste dans .local/last_install.json. Rechargement des
plugins par IPC, common.API.pluginsReload : RAS_OK. Bouton via/label visible
dans le bandeau de l'éditeur courant, vérifié par capture Computer Use.

L'ancien repérage de ce chat est repris dans le registre local après concordance
exacte des 288 UUID, de la géométrie et du groupe avec verification_ipc.json
du dépôt Autodesk. Cette adoption ne modifie pas le PCB. Le bouton pourra donc
proposer User.1 et remplacer uniquement ces anciens objets, sans imposer une
autre couche. Reprise testée avec le module réellement installé sur une copie :
18 accès, 14 drapeaux, sauvegarde et relecture du registre réussies.

La carte utilisateur conserve son repérage précédent ; la génération avec les
nouveaux drapeaux est laissée au bouton Générer / remplacer. Aucun redémarrage,
enregistrement de l'original, push ni publication distante effectué.

Second commit : correction vérifiée du changement de couche après fusion,
normalisation LF, tests et cet état ; installation automatique par le hook.
Le commit exact réellement installé est enregistré dans .local/last_install.json
et affiché dans le titre du dialogue. Le rechargement IPC est relancé ensuite.
