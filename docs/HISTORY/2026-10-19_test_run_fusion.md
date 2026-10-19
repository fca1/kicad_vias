# Test RUN Fusion — extrait disponible

Source : demande utilisateur directement visible dans ce chat, 19 octobre 2026.
Ce fichier ne constitue pas une transcription des échanges antérieurs.

Utilisateur :
> Teste maintenant l’export vers Fusion 360 jusqu’à l’exécution du RUN sur une copie de la carte, pour vérifier que les labels et leurs dessins sont bien transférés sur les bonnes couches Top et Bottom.

État constaté : copie privée préparée et alignement vérifié ; ouverture demandée
à l’utilisateur après échec du contrôle graphique. Aucun RUN exécuté à ce stade.
Voir STATUS.md. Aucun changement de code ni déploiement pour cet essai.

Utilisateur :
> go

## 19 octobre 2026 — RUN Top et Bottom exécutés : défaut de résolution des couches

Sur la copie locale ouverte dans Fusion 360, les deux ULP générés ont été
exécutés par RUN. Top refuse « Couche de serigraphie Fusion 360 absente :
SilkscreenTop » ; Bottom refuse de même SilkscreenBottom. Les exports BRD
avant/après par la passerelle Fusion sont identiques octet par octet : aucun
dessin ajouté, original intact. Le transfert n’est donc pas validé.

Cause confirmée dans fusion_protocol.layer_code : comparaison stricte du nom
L.name avec SilkscreenTop/SilkscreenBottom. Ces noms ne sont pas exposés par
cette carte active, dont l’export contient les couches 21 tPlace et 22 bPlace.
Ne pas généraliser les noms constatés lors de précédents essais à toutes les
cartes Fusion. Le choix du correctif doit encore vérifier la résolution dans
le moteur ULP actif, puis être validé par transfert et comparaison géométrique.

Jeu réel : capture KiCad de parité, 18 accès Top / 12 labels, export 732 traits.
Cas Bottom : vernis ouvert uniquement sur une copie KiCad de test, 22 accès /
22 labels, export 1992 traits. Génération par backend natif sur fichiers privés ;
ce test ne valide pas à lui seul le parcours IPC nightly. Aucun code modifié.

Utilisateur :
> Oui, corrige la résolution des couches, refais le test complet Top et Bottom sur la copie, puis mets à jour la mémoire epi-git, commit, push sur main et réinstalle.

## 19 octobre 2026 — Résolution Fusion corrigée et RUN validés

Autorisation explicite : corriger les couches, tester Top/Bottom sur la copie,
actualiser la mémoire, commit, push main et réinstallation. Le relevé ULP
B.layers du PCB actif confirme 21 tPlace et 22 bPlace dans Fusion 360.
Le résolveur commun accepte SilkscreenTop/tPlace ou SilkscreenBottom/bPlace,
utilise le nom réellement présent et refuse zéro ou plusieurs correspondances.
La copie du résolveur dans le backend natif a été supprimée pour éviter une
divergence avec IPC ; le réparateur d’anciens livrables importe le même code.

Validation réelle : les deux RUN corrigés et leur confirmation Ajouter ont été
exécutés sur la copie. Export avant/après par la passerelle Fusion : 732 traits
Top deviennent 744 segments sur 21 ; 1992 traits Bottom deviennent 2015 segments
sur 22. Le nombre de segments diffère, mais la géométrie réunie, comparée par
épaisseur, présente un écart de Hausdorff maximal de 0,000002122 mm. Épaisseurs
0,104 et 0,12 mm conservées. Le miroir Bottom est conservé dans les coordonnées
comparées. Tous les autres objets XML sont strictement identiques après retrait
des seuls nouveaux traits des couches 21/22. Original inchangé ; copie laissée
ouverte sans sauvegarde cloud. Exports de preuve privés dans .local.

62 tests automatiques réussis. Limite : essai réel sur une carte exposant
tPlace/bPlace ; les alias SilkscreenTop/Bottom restent couverts dans le code
généré, pas par un second document Fusion dans cette séance. Le cas Bottom
utilise des vias démasqués uniquement dans la copie de test KiCad.
