# Analyse de lenteur — extrait disponible

Utilisateur :
> le code fonctionne bien, mais je le trouve assez lent pour générer les labels, analyse le pourquoi

Portée : ce message et les mesures locales de cette tâche ; pas une transcription
intégrale des échanges précédents. Analyse autorisée, aucune optimisation appliquée.

## 19 octobre 2026 — Analyse des performances, sans changement de code

L'utilisateur confirme le fonctionnement et demande pourquoi la génération est
lente. Mesures sur la capture antérieure privée placement_prioritaire, avec
le code 5eb1bce ; pas sur la carte actuellement ouverte. Options Top par défaut,
18 accès, 16 labels. Génération complète sur copie en mémoire, registre copié
et sortie temporaire isolés : 7,720 s, dont prepare 7,509 s ; tableau 0,00073 s,
registre 0,00165 s. Le chargement de la carte est hors chronométrage.

Mesure des unions géométriques par appelant : leader_obstacles 18 appels/2,630 s,
route_occupied 18/1,435 s, occupied après label 16/1,267 s, occupied pour les
lettres/chiffres de grille 12/0,975 s. Ces quatre postes coûtent 6,308 s,
soit environ 82 % du temps total. Toutes unions : environ 6,74 s (87 %).
Profil cProfile séparé : 7,793 s ; 1 648 positions candidates, 6 042 buffers,
3 069 intersects. Les prédicats intersects eux-mêmes coûtent seulement 0,034 s
cumulée ; number_unprinted environ 0,0001 s. Ce sont les reconstructions de
l'ensemble des obstacles, plus que les recherches de collision, qui dominent.
Bottom de cette capture possède zéro accès admissible : ses 0,74 s ne sont
pas comparables à la génération Bottom courante de l'utilisateur.

Cause confirmée dans geometry.py : union de fixed.difference(local), solid et
toutes les autres ouvertures pour chaque via ; nouvelle union avec protections ;
réunion de toute la géométrie occupied après chaque label et texte de grille.
Run exécute ce travail synchroniquement dans le callback wx, avec BusyCursor
mais sans progression : cela ajoute une impression de blocage, non chronométrée.

Pistes proposées, non implémentées : garder séparés obstacles fixes, ouvertures
et protections ajoutées ; index spatial pour tester uniquement les obstacles
proches, exception du via locale ; éviter les unions globales répétées et
préparer les géométries réutilisées. Préserver ordre, marges, centres des rappels,
numérotation et résultats avant de comparer les temps. Aucun facteur de gain
promis sans prototype mesuré. Une progression améliorerait le retour visuel,
sans accélérer le calcul. Pas de réduction du nombre de candidats en première
intention. Données de mesure privées dans .local/performance_analysis.json et
profile_Top.prof ; aucun PCB original modifié. Aucun commit ou déploiement demandé
pour cette analyse. Documentation uniquement actualisée.

## Autorisation de l'optimisation

Utilisateur :
> Oui, optimise ces calculs sans changer le résultat du placement, mesure le gain, puis mets à jour la mémoire epi-git, commit, push sur main et réinstalle le plugin.


## 19 octobre 2026 — Optimisation mesurée et placement préservé

Demande explicite : optimiser sans changer le placement, mesurer, mémoire epi-git,
commit, push main et réinstaller. Cause déjà mesurée : unions globales répétées.
CollisionIndex conserve les géométries séparées, filtre leurs boîtes par STRtree
puis applique intersects exact sur des géométries préparées. Les nouvelles
protections sont ajoutées séparément. La différence locale autour du via,
les marges, les candidats, leur ordre et la numérotation restent identiques.
Le contrôle de fusion vers Silk conserve sa géométrie précédente.

Validation : 33 tests natifs réussis (4,648 s), dont équivalence à l'union sur
contacts de frontières, obstacles chevauchants, ensembles vides et ajouts.
Comparaison directe avec geometry.py au commit 5eb1bce : mêmes lignes de tableau,
positions, textes, miroirs, tailles, traits, arcs, grille, protections géométriques
et associations traits/vias ; seuls les UUID nouvellement créés sont ignorés.
Six cas synthétiques Top/Bottom aux tailles 0,4/0,65/1,2 mm sont identiques.
Sur la capture réelle antérieure : Top 18 accès, 16 labels, 2 fantômes,
comparaison identique avec grille à 0,65 mm et sans grille à 0,4 mm.
Bottom sur cette capture n'a aucun accès admissible : ne pas en extrapoler
un gain Bottom utilisateur. Aucun original ni carte ouverte modifié.

Mesures à trois répétitions alternées avant/après, médianes : calcul Top avec
grille 7,393 -> 1,021 s (x7,24) ; Top 0,4 mm sans grille 6,269 -> 0,972 s.
Génération complète Top par service.generate sur copie, registre et tableau
isolés : 7,676 -> 1,241 s (x6,18, -83,8 %). Tableau identique octet pour octet.
Chargement du PCB et interface graphique exclus du chronométrage. Pas de garantie
de facteur constant sur toute carte. La boucle wx reste synchrone.

Outil reproductible : tools/benchmark_placement.py ; référence Git explicite,
lecture de copie PCB, signature exacte et médianes, aucune sauvegarde de carte.
Rapports privés : .local/benchmark_placement.json et benchmark_complete.json.
Installation par hook depuis l'archive du commit ; manifeste et SHA vérifiés
après commit dans .local/last_install.json. Recharger le plugin dans l'éditeur
pour utiliser le code nouveau ; aucun rechargement à chaud prétendu sans preuve.
Source : [analyse et autorisation](HISTORY/2026-10-19_performances.md).
