# Couches Fusion 360 et règle globale — 19 octobre 2026

Source : extraits des messages disponibles dans le chat courant, dans leur ordre.
Les parties antérieures absentes ne sont pas reconstituées. Les métadonnées de
l'interface et journaux d'outils sont exclus ; l'ULP et la carte restent locaux.
La commande utilisateur ci-dessous sert à identifier le livrable à corriger.

## Utilisateur

pour le script fusion quelle couche a tu utilisée ?

## Assistant

Le script Fusion place les labels et leurs dessins sur la sérigraphie :

- **Top → `tPlace`**
- **Bottom → `bPlace`**

Cela inclut les ovales, traits de rappel et la grille.

## Utilisateur

le script donne une erreur sur les couches en fusion (annulation)

## Assistant

Je vais examiner le contrôle des couches dans l’ULP généré et la correspondance attendue par Fusion avant de corriger le plugin.

## Assistant — question asynchrone

Quel est le texte exact de l’erreur d’annulation dans Fusion ? Si possible, indiquez aussi le chemin du fichier .ulp lancé et la face choisie (Top ou Bottom).

## Utilisateur — réponse asynchrone

RUN 'C:\Users\frant\Downloads\ESTELEC\cube_pcb1\Kicad_Via_top_mcu9p_eu\labels_vias.ulp';

## Assistant

La cause est confirmée dans le fichier que vous avez lancé : l’ULP exige une couche nommée `tPlace`, alors que l’extraction Fusion de cette carte contient **`SilkscreenTop` (21)** et **`SilkscreenBottom` (22)**. Le contrôle trouve donc zéro couche correspondante et annule.

Ma réponse précédente utilisait les anciens noms EAGLE et ne correspondait pas à votre carte Fusion. Je propose de reconnaître les deux conventions, d’utiliser le nom réellement trouvé et de distinguer une erreur de couche d’une erreur de carte.

## Assistant — question asynchrone

Puis-je corriger cette compatibilité dans le plugin et dans votre ULP déjà généré, puis tester, mettre à jour la mémoire, committer, pousser sur main et réinstaller ?

## Assistant

Je demande cet accord parce que [les règles du dépôt](C:/Users/frant/Documents/ChatGPT/Kicad_Via/AGENTS.md) imposent, avant une modification de code, de « décrire les changements envisagés et obtenir l’accord explicite préalable de l’utilisateur ».

## Utilisateur — réponse asynchrone

Oui, corrige et réinstalle

## Assistant

Je vais corriger le générateur et votre fichier `labels_vias.ulp` existant, avec une sauvegarde de l’original. L’ULP cherchera `SilkscreenTop` ou `tPlace` pour Top, et `SilkscreenBottom` ou `bPlace` pour Bottom, puis utilisera le nom trouvé. Les contrôles d’implantation resteront en place.

## Assistant

La correction passe les **30 tests**. Je vérifie maintenant une copie de votre ULP pour confirmer que seuls la détection des couches et leurs messages d’erreur changent, en conservant les composants et tous les traits exportés.

## Utilisateur

retiens pour tous les projets que l'on travaille avec fusion360 et pas une vielle version de eagle (c'était toujours comme cela, je ne vois pas pourquoi tu evoques les vielles versions de eagle)

## Assistant

Entendu. **Fusion 360 est la référence pour tous vos projets**, et cela l’était déjà. J’ai repris à tort les noms `tPlace`/`bPlace`.

Je vais inscrire cette règle dans les consignes globales. Le correctif ciblera les couches actuelles de Fusion 360 : **SilkscreenTop** et **SilkscreenBottom**.

## Assistant

La règle est enregistrée dans les consignes globales. Le correctif cible désormais les couches de **Fusion 360**.

Sur la copie de votre ULP, j’ai vérifié la détection de `SilkscreenTop`, les **88 composants** et la conservation des **1 353 traits**. Je passe à l’installation, puis à la correction du fichier que vous lancez.
