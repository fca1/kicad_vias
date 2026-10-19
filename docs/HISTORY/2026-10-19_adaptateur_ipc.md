# Extrait accessible — migration IPC, 19 octobre 2026

Portée : messages utilisateur pertinents accessibles dans le chat courant.
Ce fichier n'est pas la transcription intégrale de la conversation. Les détails
de réalisation sont dans IPC_MIGRATION.md ; aucun PCB ni chemin de carte privée
n'est publié. Les anciennes étapes reprises par résumé ne sont pas retranscrites.

Utilisateur :
> Continue la migration vers IPC : implémente l’adaptateur pour les fonctions disponibles, garde le natif uniquement pour les manques, vérifie que le placement reste identique, puis mémoire epi-git, commit, push main et réinstallation.

Utilisateur, en réponse à la demande d'ouverture d'une carte synthétique distincte :
> ok

Utilisateur :
> est ce que la version nightly de kicad corrige certaines choses au niveau de l'ipc qui serait utile pour la future version de ce plugin avec kicad11 futur ?


Suite accessible :

Utilisateur :
> Recharge le plugin dans KiCad 99 , puis teste le parcours complet depuis le bouton sur la carte de test pour vérifier que tout fonctionne.

Utilisateur, après clarification de la version :
> Utiliser une nightly 10.99

Résultat du diagnostic : voir STATUS.md, section vérification de la nightly.
Aucun parcours réussi ne doit être déduit du simple lancement de l'éditeur.


Suite accessible — autorisation et compromis :

Utilisateur :
> go

Utilisateur, après proposition de renommage manuel initial :
> explique encore, UpdateBoardStackup va t'il evoluer ?

Assistant (résumé, pas transcription) : commande déclarée mais non implémentée,
ticket officiel 25384, pas de date vérifiée ni garantie pour les noms User.

Utilisateur :
> ok

Utilisateur :
> compromis temporaire


Assistant (résumé de réalisation) : bouton visible après correction de
l’identifiant interdit ; 55 tests passent. Validation graphique suspendue
après détection d’interaction utilisateur, attente de disponibilité de la fenêtre.
