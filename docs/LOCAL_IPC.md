# Pilotage local de Kicad_Via

Le dialogue nightly démarre un serveur HTTP JSON sur 127.0.0.1 et un port
aléatoire. Il utilise le même Session que les boutons et un verrou commun.
Un verrou OS interdit deux serveurs locaux sur le même socket KiCad.
Ce protocole appartient au plugin ; KiCad ne relaie pas ces commandes.

Les descripteurs sont dans %LOCALAPPDATA%/Kicad_Via/control/*.json. Choisir
explicitement celui dont target et socket correspondent à la carte voulue.
Le fichier contient un jeton privé : ne pas le publier. Windows utilise les
permissions du profil utilisateur ; chmod 0600 est appliqué sur les plateformes
qui le prennent en charge. Une page web (Origin) est refusée.

Client Python, depuis le dossier parent du paquet installé :

```python
from Kicad_Via.local_ipc import call
s = call(descriptor, 'status')
layer = s['layers']['Top'][0]['id']
call(descriptor, 'generate', {'side':'Top', 'layer':layer, 'size':0.65,
                             'grid':True, 'output':chemin_md_absolu})
call(descriptor, 'merge', {'side':'Top', 'layer':layer})
r = call(descriptor, 'export', {'side':'Top', 'source':chemin_brd_absolu,
                                'destination':dossier_absolu})
```

export prépare l’ULP et renvoie command (RUN), path et strokes. Il ne lance pas
Fusion et ne modifie pas le presse-papiers. Les sélections de couches utilisent
les identifiants IPC renvoyés par status, pas les numéros du fichier PCB.
Les paramètres Top et Bottom sont indépendants. Les couches doivent toujours
être renommées manuellement au préalable, selon le compromis temporaire.

Mode sans dialogue : définir explicitement KICAD_API_SOCKET, et le jeton KiCad
si fourni par son lanceur, puis exécuter avec le Python de l’environnement plugin :
`python -m Kicad_Via.local_ipc --serve`.
Le processus affiche uniquement le chemin du descripteur, pas son jeton.
Client CLI : `python -m Kicad_Via.local_ipc --descriptor CHEMIN --command status`.
Les autres commandes acceptent --params avec un objet JSON.

Le protocole POST /v1 requiert Authorization: Bearer, Content-Type application/json,
instance, command, et board pour les mutations. call ajoute ces identifiants depuis
le descripteur. status permet d’identifier la cible et l’état busy. Changer de carte
ou d’ensemble de vias impose une nouvelle session. Les erreurs de paramètres sont
400 ; authentification 403 ; conflit de cible/opération 409. Il n’y a aucune relance
automatique après timeout : une réponse perdue peut correspondre à une opération
terminée. Vérifier la carte et le tableau avant de recommencer. Fermer proprement
supprime le descripteur ; après crash, un ancien fichier peut rester mais le verrou
OS est libéré. Le client ne cherche jamais un autre serveur en cas d’échec.

L’interface concerne le chemin externe IPC de la nightly. Le lanceur natif KiCad10
reste inchangé. Les limites géométriques de IPC_MIGRATION.md restent applicables.
