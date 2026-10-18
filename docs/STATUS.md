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
