# Contexte — Kicad_Via

Mémoire initialisée le 18 octobre 2026 avec la compétence epi-git, dans le dépôt
Kicad_Via, distinct du dépôt Autodesk depuis lequel la conversation a commencé.
Distant : https://github.com/fca1/kicad_vias ; visibilité publique vérifiée par
GitHub CLI. Son commit initial `8327aae` ne contient qu'un README ; son historique
est conservé par fusion, sans réécriture. Travail sur `codex/kicad-via`.

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
placement évitant composants, ouvertures de masque et sérigraphie. À moins de
3 mm d'un label déjà imprimé, le label voisin peut être omis ; son accès reste
au tableau. Taille par défaut 0,65 mm, plage 0,4–2 mm.

Correction utilisateur du 18 octobre 2026 : réduire le tableau à Repère, Net,
Case, X (mm), Y (mm), sans décimales. Conserver les coordonnées de la grille
vue de la face, retirer coordonnées natives, diamètres, perçage, présence du
label, voisin, écarts et UUID de l'affichage. Ces données restent internes.

## Architecture vérifiée dans le code

- `plugin/Kicad_Via/action.py` : ActionPlugin natif, dialogue wxPython et bandeau.
- `model.py` : options et coordonnées ; `geometry.py` : sélection et placement.
- `service.py` : propriété UUID, génération, fusion et tableau à cinq colonnes.
- Registre local `%LOCALAPPDATA%/Kicad_Via/ownership` : nécessaire pour reprendre
  les objets après réouverture ou sur un autre poste. Pas de simple adoption par nom.
- `tools/install_plugin.py` : archive du commit, sauvegarde et vérification SHA-256.
- `tools/adopt_previous.py` : migration bornée sur preuves de l'ancien repérage.
- `tests/test_plugin.py` : 23 tests natifs, dont interface réelle wxPython.

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
