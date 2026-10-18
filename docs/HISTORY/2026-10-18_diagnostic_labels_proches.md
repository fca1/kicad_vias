# Diagnostic des labels absents — 18 octobre 2026

Source : question et capture visibles dans le chat courant. Portée : extrait de
cet échange d'analyse ; pas de transcription complète des échanges antérieurs.
La capture n'est pas copiée dans Git. Les nets et coordonnées vérifiés restent
locaux. Voir STATUS pour le diagnostic puis la correction autorisée ci-dessous.

## Utilisateur

Pourquoi tu n'as pas mis d'autres label sur l'exemple donné ici

## Assistant

Je vais vérifier les règles de sélection et d’allègement des labels pour expliquer ce cas, en distinguant ce que montre l’image de ce qu’il faut confirmer sur la carte.

## Assistant

J’ai vérifié le repérage : **deux règles se cumulent** sur les trois vias alignés :

- **À gauche** : `E2-1` est affiché.
- **Au milieu** : un autre via du même net a été choisi ailleurs, sous `C2-2`.
- **À droite** : le représentant de ce net est `E2-2`, mais son label est masqué car trop proche de `E2-1` — environ **1,7 mm**.

L’allègement est donc trop agressif ici : **la proximité ne suffit pas à identifier des nets différents**. Désactiver « Alléger les labels proches » rétablira `E2-2`, mais le via central restera représenté ailleurs.

## Utilisateur

Par exemple, les vias du dessus, il y avait de la place

## Assistant

Oui, vous avez raison : il y a de la place au-dessus. Le plugin ne cherche pas à y déplacer les labels : dès qu’un via est à moins de **3 mm** d’un autre repère, il masque son label, même si une zone libre existe à côté.

Il faudrait **chercher d’abord une place pour un label déporté avec son trait de rappel**, puis envisager de le masquer seulement si aucun placement lisible n’est possible.

## Utilisateur

Oui, modifie le plugin pour chercher d'abord une place libre avec un label déporté et son trait vers le via, avant de le masquer. Puis mets à jour la mémoire epi-git, commit, push sur main et réinstalle.

## Assistant

Je vais modifier la règle confirmée : le plugin cherchera d’abord une place libre pour chaque label et son trait de rappel. Le masquage par proximité ne servira qu’en dernier recours. Je vérifierai ce cas avant de mettre à jour la mémoire epi-git, puis de committer, pousser sur `main` et réinstaller.

## Assistant

La correction passe les **24 tests**. Un via proche garde désormais son label dès qu’un placement libre est trouvé. Le repli reste vérifié : si aucun placement n’est possible, le label ne peut être masqué qu’avec l’option activée et un voisin effectivement imprimé à moins de 3 mm.

## Assistant

Sur une copie récente de votre carte, on passe de **14 à 16 labels pour 18 accès** : **E2.2** est bien rétabli, ainsi que **F2.4**. La génération puis la fusion en sérigraphie réussissent sur cette copie. Je finalise la mémoire epi-git avant la publication et la réinstallation.
