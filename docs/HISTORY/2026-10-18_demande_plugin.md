# Demande Kicad_Via — extraits disponibles du chat

Collecte : 18 octobre 2026. Date de chaque message antérieur : inconnue.
Origine : messages utilisateur du chat courant transmis au contexte de travail.
Identifiant global du chat et export original : non fournis.

**Portée : extraits des demandes utilisateur, dans leur ordre ; pas une transcription
intégrale.** Les réponses assistant intermédiaires et journaux d'outils des étapes
antérieures ne sont pas disponibles en texte intégral et ne sont pas reconstitués.
Les messages de configuration d'environnement et les consignes d'autres projets
sont hors périmètre. Les réponses asynchrones ci-dessous incluent la question
citée par le client, sans que cela reconstitue l'ensemble du dialogue.
Pour compléter les échanges manquants, fournir l'export original de ce chat ;
la liste complète des autres conversations n'est pas connue.

## Extrait 1 — utilisateur

```text
sur kicad, j'ai un PCB courant. Je voudrais savoir c'est quoi Backdrill mode
```

## Extrait 2 — utilisateur

```text
Je veux savoir sur kicad si le via est recouvert de vernis ou non
```

## Extrait 3 — utilisateur

```text
la version tourne en ce moment
```

## Extrait 4 — utilisateur

```text
Je voudrais améliorer la sérigraphie en rajoutant quelque chose. Les vias qui sont visibles, les vias qui ne sont pas sous un composant, par exemple, sont avec un vernis découvert me permettant de placer une pointe de test. Par contre, ce que j'aimerais, c'est que chaque via ait sur le top screen, top silk, un petit label avec un numéro, type AN, me permettant de connaître pour ce via sur quel net il est. Et ainsi, avec un tableau de correspondance et en sachant où est le via sur X, Y, de me permettre de retrouver le via sur le PCB. Évidemment, ça ne sert à rien pour un net d'avoir plusieurs vias avec plusieurs numéros. Il faut choisir le via le plus simple, celui qui est le plus découvert, un seul. Et s'il y en a plusieurs, il n'y a que celui-là qui compte, les autres on n'affiche rien. Est-ce que tu peux me synthétiser la chose ?
```

## Extrait 5 — utilisateur

```text
Les nets sans via accessibles n'ont pas besoin d'être dans une liste séparée. Et il me faut effectivement une demande de repérage. Ça pourrait être aussi une grille, toutes les centimètres, en pointillés, qui me permettent de retrouver plus facilement les coordonnées du via.
```

## Extrait 6 — utilisateur

```text
On va même prendre un pas de 20 mm au lieu de 10 mm, ça permettra d'alléger ces pointillés. Et tu peux y aller, go !
```

## Extrait 7 — utilisateur

```text
<send_user_message_question_reply>
[{"questionItemId":"[\"request_user_input_async\",\"call_cc3d4dc1a8b946509e71a2879cd763bc\",0]","question":"Le PCB est encore « Unsaved » et mes commandes ne permettent pas d’en récupérer une copie depuis l’éditeur. Pouvez-vous l’enregistrer en .kicad_pcb (Ctrl+Maj+S), puis m’indiquer le chemin ? Je pourrai alors ajouter les repères sur une copie fidèle de votre carte.","answer":"utilise au maximum ipc"}]
</send_user_message_question_reply>
```

## Extrait 8 — utilisateur

```text
<send_user_message_question_reply>
[{"questionItemId":"[\"request_user_input_async\",\"call_16464e44235f482ca51a3792f3e937fd\",0]","question":"J’ai confirmé que le canal IPC appartient au gestionnaire KiCad (PID 30900), pas à l’éditeur PCB (PID 33708). Pour accéder à votre carte en mémoire par IPC, fermez uniquement le gestionnaire KiCad en laissant le PCB ouvert, puis dans les préférences de l’éditeur, désactivez/réactivez le serveur API IPC. Dites-moi quand c’est fait ; aucune sauvegarde de la carte n’est nécessaire pour cet essai.","answer":"API enabled mais je n'ai pas trouvé IPC"}]
</send_user_message_question_reply>
```

## Extrait 9 — utilisateur

```text
<send_user_message_question_reply>
[{"questionItemId":"[\"request_user_input_async\",\"call_d17f0cae6e3c43d3a9c30d239689a18d\",0]","question":"Dans l’éditeur PCB, décochez « API enabled », validez les préférences, puis rouvrez-les, recochez cette même option et validez. Cela devrait démarrer le canal IPC de l’éditeur. Prévenez-moi ensuite.","answer":"ok"}]
</send_user_message_question_reply>
```

## Extrait 10 — utilisateur

```text
Lorsque les vias sont très proches les uns des autres, il est inutile de mettre un label. Par exemple, si tu as A10, A11 et A10 et A11 sont vraiment à côté l'un de l'autre, on a bien compris qu'A11, on le trouvera facilement. Il ne faut évidemment pas que les labels empiètent sur d'autres choses, donc quitte à mettre un petit trait pour dire où est le label du via. Et voilà.
```

## Extrait 11 — utilisateur

```text
Il faudrait peut-être changer de couche pour pouvoir modifier très facilement ce que l'on fait avec une couche qui ne soit pas directement dans le top skill. Et puis cela nous permettrait de pouvoir recommencer quelque chose après plus facilement, quitte à merger après.
```

## Extrait 12 — utilisateur

```text
On va transformer cela en plugin neuf que l'on va appeler Kicad underscore Via et qui nous permet de choisir plusieurs options dans une petite boîte. La première chose, c'est si c'est bottom ou top, si on veut la taille du label également, et si on veut faire un merge d'une couche utilisateur vers le F silk. Quand on choisit une couche utilisateur, il faut toujours que cette couche soit renommée et qu'elle soit bien évidemment libre. Elle ne peut que contenir les labels via d'avant. À chaque commit que l'on fera, tu referas bien sûr une installation de ce plugin. Il faut également qu'il soit sur le bandeau en haut avec un petit logo qui montre ce qu'il fait. On peut dessiner un via avec un label par exemple. Il est aussi intéressant dans le nommage des labels de pouvoir avoir en A, B, C, D, E, F, etc. Cela correspond aux abscisses et 1, 2, 3, 4, 5, 6, 7 aux carrés des ordonnées, dans les 20 mm, ce qui nous permet par ce classement de trouver plus facilement et donc de ne pas faire comme là c'est fait, un petit peu en suivant les points les uns des autres. Donc trouver une convention. De plus, il est intéressant d'avoir ce petit flag, peut-être d'entourer le label avec un ovale et de rajouter un petit trait dessus, toujours qui va vers le via. Comme ça on voit bien de quel via on parle et ça permet de pouvoir l'éloigner avec une réduction de taille par rapport à ce que tu as en ce moment.
```

## Extrait 13 — utilisateur

```text
On peut recommencer la numérotation avec bottom par rapport à top, quand nécessaire, car il y aura deux listes bien séparées, une pour top et une pour bottom.
```

## Extrait 14 — utilisateur

```text
Il faut également pouvoir choisir le fichier .nd qui sortira sous forme de tableau indiquant le nécessaire pour les mètres par rapport au via, avec les coordonnées, pour faire le fichier de sortie.
```

## Extrait 15 — utilisateur

```text
voici le github attaché [https://github.com/fca1/kicad_vias.git](https://github.com/fca1/kicad_vias.git) avec [$epi-git](C:\Users\frant\\.codex\skills\epi-git\SKILL.md) à faire en meme temps
```

## Suite — assistant — 18 octobre 2026

Je vais relier **Kicad_Via** au dépôt GitHub indiqué et appliquer la compétence **epi-git** pour compléter sa mémoire. Je vérifierai le contenu et la visibilité du dépôt distant avant toute publication de l’historique.

## Suite — assistant — 18 octobre 2026

Le dépôt GitHub est public et contient seulement un README initial. Je vais conserver cet historique et préparer une PR avec le plugin et sa mémoire de projet. L’archive des échanges sera signalée comme partielle ; les fichiers PCB, données locales et consignes d’autres projets resteront hors publication.

## Suite — utilisateur — 18 octobre 2026

Je regarde le fichier de sortie. Il y a beaucoup trop de choses. Donc le repère, oui, le net, oui, la case, oui. Les coordonnées, il faut simplement les donner en millimètres, mais pas donner les décimales, ça sert à rien. Je vois pas pourquoi il y a une différence entre X qui cadre, Y qui cadre, par rapport à X, Y. On ne veut pas du diamètre du via, ni du perçage. On comprend pas trop l'label imprimé voisin, delta X voisin, delta voisin Y, c'est trop. et U idée via n'est pas intéressant du tout.

## Suite — assistant — 18 octobre 2026

Je vais réduire le tableau à cinq colonnes : **Repère, Net, Case, X (mm), Y (mm)**, avec des coordonnées arrondies au millimètre.

Les deux séries actuelles correspondent aux coordonnées internes KiCad et à celles de la grille vue depuis la face choisie. Je conserverai celles de la grille, pour retrouver les vias avec les repères imprimés.

## Suite — assistant — 18 octobre 2026

Le tableau est désormais limité aux cinq colonnes demandées, et les 17 tests passent. Je vais réinstaller cette version et mettre à jour le fichier de sortie existant, avec une sauvegarde de son ancien contenu.

## Suite — assistant — 18 octobre 2026

Le fichier existant a été simplifié : il conserve ses 18 accès, avec les coordonnées sans décimales. La [PR GitHub](https://github.com/fca1/kicad_vias/pull/1) contient le plugin et la mémoire **epi-git**.

KiCad refuse pour l’instant le rechargement IPC en se déclarant occupé. Je vais vérifier la fenêtre avec la compétence **computer-use** pour identifier ce qui le bloque.
