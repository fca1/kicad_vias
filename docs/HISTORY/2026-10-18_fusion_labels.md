# Point dans les repères, RUN Fusion et fusion de PR

Date : 18 octobre 2026. Source : échange courant, séquence disponible de cette
demande. Messages utilisateur et commentaires assistant reproduits ci-dessous.
Ce fichier complète l'archive partielle précédente, sans reconstituer les étapes
absentes ni les journaux d'outils. Résultats techniques : STATUS et DECISIONS.

## Utilisateur

Tu peux merger la PR sur main et réinstaller le plugin depuis ce commit, en mettant à jour la mémoire epi-git. Mais auparavent, modifie le - en . exemple A3-1 devien A3.1 (qui diminue la taille). Comme sur le projet kicad_plugin_fusion2kicad, ajoute le necessaire dans le plugin (avec la copie dans le presse papier) pour pouvoir intégrer via le "run", la copie de ces labels avec les dessins vers fusion

## Assistant

Je vais remplacer les repères comme **A3-1** par **A3.1**, puis examiner le mécanisme « Run » et presse-papiers de **kicad_plugin_fusion2kicad** pour reprendre son fonctionnement. Ensuite, je mettrai à jour la mémoire epi-git, fusionnerai la PR sur `main` et réinstallerai depuis le commit fusionné.

## Assistant

Le projet de référence prépare un fichier ULP et propose de copier sa commande `RUN`, à exécuter manuellement dans Fusion. Je vais ajouter ce même parcours à Kicad_Via.

L’export reprendra les labels, ovales, traits de rappel et pointillés de la face choisie. Pour conserver leur aspect, les lettres seront converties en traits. Le fichier BRD/FBRD source servira à vérifier l’alignement entre KiCad et Fusion avant de préparer la copie.

## Assistant

Les nouveaux repères utilisent **A3.1**, et le bouton **Copier vers Fusion…** est ajouté. Les tests existants passent. Je vérifie maintenant l’export Top/Bottom, la conservation du dessin et le refus d’un BRD dont l’implantation ne correspond pas à KiCad, avant la fusion sur `main`.

## Assistant

La préparation réussit sur une copie de votre carte : **18 accès, 14 labels et 1 242 traits** pour Fusion.

J’ai aussi identifié pourquoi la régénération pouvait être refusée dans l’état actuel : l’ancien repérage User.1 coexiste avec une version fusionnée, dont la couche User.2, vide, conserve le nom réservé. Je vais libérer ce nom uniquement si la couche est vide et reconnue par le registre du plugin, afin de permettre la régénération en `A3.1`.
