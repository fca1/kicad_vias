# Migration IPC — état du 19 octobre 2026

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

## Adaptateur hybride livré

`ipc_adapter.py` gère la lecture des objets, la vérification du document, les
écritures par lots, les couches actives/visibles et les transactions IPC.
Le pipe Windows doit appartenir au PID exact du lanceur. Les statuts par objet
sont contrôlés explicitement : kipy 0.8 ne remonte pas leurs échecs dans ses
méthodes CRUD. Aucun retry de mutation n'est effectué après une réponse ambiguë.

`ipc_jobs.py` prépare les opérations avec les mêmes contrôles d'appartenance
que le service natif. `ipc_native.py` convertit les objets préparés en messages
IPC, en conservant UUID, coordonnées entières, alignement, taille et miroir.
La fusion conserve le message IPC courant et ne change que couche et miroir.
`ipc_controller.py` rend la main au callback natif, puis appelle IPC dans un fil
séparé. Un filtre d'événements bloque les éditions pendant l'opération sans
 désactiver la frame : IsEnabled=false ferait refuser IPC par KiCad.
Les appels natifs de modification restent sur le fil GUI.

Le registre et le tableau sont restaurés si l'échec intervient avant validation
et si drop_commit réussit. Si push/drop donne un résultat ambigu, le registre
est conservé et l'erreur signalée : aucune réussite n'est inventée.
Les dépendances sont épinglées dans ipc-requirements.txt et installées avant
le paquet par tools/install_plugin.py, depuis l'archive du commit à déployer.

## Replis natifs encore nécessaires ou non remplacés à parité

- Capture géométrique exacte : enveloppes, ouvertures de masque, contours PCB.
  Les lectures simples IPC existent ; elles ne remplacent pas automatiquement
  ces contours calculés et les règles effectives. La parité de remplacement
  reste à démontrer avant de modifier les obstacles du moteur.
- Métriques exactes de texte et traits de police pour Fusion. IPC expose aussi
  des métriques et formes de texte ; leur parité avec ce pipeline reste à tester.
- Renommage des couches : pas de setter dans l'interface inspectée.
- Groupe après création des dessins : sur KiCad 10.0.7, Deserialize cherche les
  membres dans BOARD, alors que les créations sont encore dans COMMIT. L'essai
  réel a confirmé 400 dessins exacts mais aucun groupe créé. Le groupe est donc
  finalisé en natif après push ; cela couvre également les groupes vides.
  **Cette finalisation et le renommage ne font pas partie de l'undo IPC.**
  Si elle échoue, les dessins déjà validés et leur registre sont conservés et
  une erreur explicite demande vérification. Aucun rollback fictif après push.

Le lanceur reste un ActionPlugin SWIG KiCad 10. Aucun plugin externe complet
ni compatibilité KiCad 11 ne sont annoncés à ce stade.

## KiCad 11 / nightly : comparaison du code, pas essai installé

Source officielle auditée : master 7d2afb0e9239a70e39150a30f1139b930820ae4a,
19 octobre 2026. Dans pcbnew/pcb_group.cpp, DeserializeGroup consulte désormais
COMMIT::ResolveItem ; api_handler_board.cpp lui passe le commit et finalise
les membres dans un second passage. Ce changement cible directement la limite
observée sur KiCad 10 ; le repli pourra être retiré après validation réelle.

GetBoardBoundingBox propose notamment BBBM_BOARD_EDGES_ONLY pour l'origine de
la grille ; FocusOnItems permettrait de cadrer un via depuis sa ligne de tableau.
Ces fonctions ne sont pas activées dans ce commit. Le retrait SWIG des nightlies
est annoncé officiellement depuis le 22 mars 2026 : il faut un lanceur IPC externe
et remplacer tous les replis avant de revendiquer KiCad 11.

Références :
- https://github.com/KiCad/kicad-source-mirror/blob/7d2afb0e9239a70e39150a30f1139b930820ae4a/pcbnew/pcb_group.cpp
- https://github.com/KiCad/kicad-source-mirror/blob/7d2afb0e9239a70e39150a30f1139b930820ae4a/pcbnew/api/api_handler_board.cpp
- https://github.com/KiCad/kicad-source-mirror/blob/7d2afb0e9239a70e39150a30f1139b930820ae4a/api/proto/board/board_commands.proto
- https://groups.google.com/a/kicad.org/g/devlist/c/pGF2lh6j-sc

## Validation de l'adaptateur

47 tests automatiques réussis, dont statuts IPC refusés, création partielle,
publication en échec, annulation, refus d'un autre document, finalisation en
échec, groupes vides, activation de couche sans dessin et conservation des
attributs manuels à la fusion. Dans un éditeur KiCad 10.0.7 distinct sur une
carte synthétique : 400 dessins Top puis 411 Bottom relus sans aucune différence
de message géométrique ; remplacement Bottom et fusion B.SilkS exacts ; échec
injecté et drop réels avec carte sérialisée identique avant/après. Finalisation
native du groupe vérifiée sur la copie relue. Le coordinateur GUI complet reste
à essayer depuis le bouton après rechargement du plugin installé.

Comparaison au commit d0d1477 sur la copie réelle : placement strictement
identique, 18 accès/16 labels Top ; calcul environ 1,02 s, passage unique sans
prétention de mesure statistique. Aucun essai d'écriture sur la carte utilisateur.

## Vérifications de la première extraction (historique)

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
