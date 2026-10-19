# Préparation IPC — extrait utilisateur disponible

> Oui, prépare la migration vers IPC en séparant le moteur de placement des accès KiCad, sans changer le résultat. Garde l’API native seulement où nécessaire, teste, mets à jour la mémoire epi-git, commit, push sur main et réinstalle. Change aussi les extensions .nd par .md

Portée : demande courante et preuves locales, pas transcription complète du chat.

## 19 octobre 2026 — Moteur indépendant et sorties Markdown

Autorisation : préparer IPC sans changer le résultat, tests, mémoire, commit,
push main et installation ; remplacer .nd par .md. Réalisé : board_data fournit
le contrat neutre, placement calcule sans pcbnew/wx/kipy, native_adapter capture,
mesure et matérialise le plan. geometry reste une façade de compatibilité.
Le paquet s'importe hors KiCad ; les appels natifs sont aux frontières de carte,
police et application des modifications, plus dans le moteur de placement.
Le plugin est encore natif : le transport IPC complet reste à implémenter et
valider, notamment renommage, contours, métriques, transactions et propriété.
Inventaire de l'interface kipy effectué sans modifier le document ouvert.

36 tests réussis (4,673 s). Test pur avec interdiction d'import des API/GUI ;
parité des métriques aux coordonnées fractionnaires ; anciens .nd conservés et
contrôle d'écrasement .md. Comparaisons exactes à d0d1477 sur copie réelle Top
avec/sans grille et six cas synthétiques Top/Bottom (0,4/0,65/1,2 mm), tous
identiques. Calcul réel Top ~1,03 s ; 18 accès/16 labels. Aucun PCB original
modifié. Les tableaux futurs et chemins mémorisés utilisent .md, sans effacer
les .nd existants. Registre mis à jour avec le nouveau chemin à la génération.

Détails et limites : [architecture IPC](../IPC_MIGRATION.md).
Sources : [échange](2026-10-19_preparation_ipc.md), code, tests,
.local/benchmark_ipc.json (rapport privé). Installation exacte depuis commit
par le hook ; SHA et empreintes dans .local/last_install.json. Rechargement
natif via préférences, pas common.API.pluginsReload.
