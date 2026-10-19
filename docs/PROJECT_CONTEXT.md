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
