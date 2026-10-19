# Préparation de la migration IPC

## Réalisé le 19 octobre 2026

Le placement est désormais indépendant de pcbnew, wx et kipy. Le paquet peut
être importé dans un processus externe sans charger l'API native.

- `board_data.py` : ViaData, BoardSnapshot et TextMetrics, sans objets SWIG.
  Les coordonnées sont en mm ; les métriques de texte portent aussi le pas
  entier pour reproduire exactement la conversion des positions.
- `placement.py` : sélection des accès, index de collisions, recherche des
  positions, rappels, grille, fantômes et numérotation. `choose(snapshot, opt)`
  sélectionne ; `layout(snapshot, chosen, metrics, opt)` retourne un plan de
  textes, lignes et capsules. Les identifiants de vias sont des chaînes opaques.
- `native_adapter.py` : capture des contours et accès, métriques exactes de la
  police KiCad, puis construction des objets du plan hors carte. Aucun appel
  natif n'est effectué par le moteur pendant le placement.
- `geometry.py` : façade de compatibilité pour les appels précédents.

L'application effective à la carte, le registre des UUID, le rollback et
l'historique natif restent gérés par service et l'ActionPlugin existants.
L'export Fusion conserve le rendu natif des traits de police. Le natif est
concentré aux frontières avec KiCad ; il n'est plus nécessaire au calcul.

## Capacités et limites vérifiées

La bibliothèque kipy disponible expose get_items, create_items, update_items,
remove_items, begin_commit/push_commit/drop_commit, groupes, get_layer_name,
get_item_bounding_box et get_pad_shapes_as_polygons. Cela permet une future
implémentation IPC de lecture/écriture ; aucune absence globale n'est présumée.

L'interface Board inspectée ne fournit pas d'équivalents directs à SetLayerName,
GetBoundingHull, GetBoardPolygonOutlines et TransformTextToPolySet. Cela décrit
cette interface disponible, pas une impossibilité définitive de reconstruction
ou des prochaines versions. Les métriques peuvent aussi nécessiter des requêtes
par lots ou un calcul de police validé, plutôt que des objets temporaires.

Le plugin livré reste un ActionPlugin natif. Aucun plugin IPC fictif ou hybride
n'est annoncé : appeler synchroniquement le serveur IPC depuis le callback GUI
n'est pas un remplacement approprié du moteur devenu externe. Une migration du
transport doit conserver les contrôles d'appartenance, les UUID et l'annulation.

## Étape suivante

Implémenter un adaptateur IPC externe qui fournit le même snapshot et les mêmes
métriques, puis applique les dessins par lots dans une transaction. Vérifier la
parité des contours, métriques et masques sur la version cible avant bascule.
Prévoir plugin.json et la vie du processus externe, puis supprimer le backend
natif quand la couverture et les tests de parité le permettent. Ne pas annoncer
une date de retrait de SWIG ou la disponibilité d'une méthode non vérifiée.

## Vérifications

36 tests natifs passent, dont un sous-processus qui interdit tout import de
pcbnew, wx ou kipy et exécute réellement le moteur. Les métriques traduites
sont comparées aux boîtes natives à coordonnées positives/négatives fractionnaires.
Comparaison à d0d1477 : mêmes dessins, lignes de tableau, protections et
associations via/trait sur la copie réelle et six cas synthétiques Top/Bottom
à 0,4, 0,65 et 1,2 mm. Les UUID de nouveaux objets, aléatoires, sont exclus.
La copie réelle donne encore 18 accès/16 labels ; environ 1,03 s pour le calcul
Top avec grille, sans régression observée. Ce passage unique n'est pas une
nouvelle estimation statistique du gain. La carte ouverte n'a pas été modifiée.

## Markdown

Le sélecteur et les noms par défaut utilisent .md. Les chemins mémorisés .nd
et les noms sans extension sont normalisés en .md ; les anciens fichiers .nd
sont conservés. Le contrôle anti-écrasement s'applique à la destination .md.
Les documents historiques gardent leurs références .nd comme traces de l'époque.
