# Signalement du 19 octobre 2026 — Top et Bottom

Extrait utilisateur disponible dans le chat, pas une transcription intégrale.

> je viens de faire un test sur TOP, il indique une erreur dans kicad, sur un manque de place et ne fais rien, j'ai essayé egalement en bottom ou les labels sont affichés en miroir

Diagnostic en lecture seule : geometry.prepare recherche des positions à 1,5–10 mm,
par pas radial de 0,5 mm et angles de 15 degrés, avec trait direct ou un coude.
Après échec, seul un voisin déjà imprimé à 3 mm au maximum permet le masquage
si l'option est active. Sinon ValueError interrompt generate avant mutation.
text_item applique explicitement SetMirrored(side=='Bottom'), y compris sur
la couche utilisateur. Le repère géographique Bottom inverse aussi X.

Limites : message exact et via bloquant non disponibles ; carte du nouvel essai
non examinée. Aucun journal trouvé dans les dossiers locaux KiCad vérifiés.
Le point de vue du PCB lors de l'observation Bottom reste à préciser.
Question posée sur repère/net de l'erreur et vue de dessus ou retournée.
Aucune modification de code, installation ou publication pour ce signalement.

## Suite autorisée et réalisée

> Pour Top, il ne faut pas tout bloquer si un via manque de place : garde les autres labels et mets celui-là en fantôme dans la liste. Corrige cela, mets à jour la mémoire, commit, push sur main et réinstalle.  Pour bottom, un flip vizw montre des labels inversés sur la couche user

La capture identifie C1.2 comme accès bloquant. Aucun PCB courant n'a été
modifié ni enregistré pendant cette correction.
Cause Bottom confirmée dans pcb_painter.cpp (branche KiCad 10.0, draw texte,
IsFlippedX / IsSideSpecific) : la vue conserve l'orientation des textes non
liés à une face. Vérification native : User.1 IsSideSpecific=False,
B.SilkS=True. Le miroir forcé du plugin expliquait le symptôme.
Source : https://github.com/KiCad/kicad-source-mirror/blob/10.0/pcbnew/pcb_painter.cpp

Correction : aperçu User sans miroir ; miroir Bottom lors de la fusion,
restauré en cas d'échec, et sur une copie temporaire du texte lors de l'export.
Les anciens aperçus doivent être régénérés. Pas de validation visuelle de la
carte ouverte ; comportement couvert par tests natifs et code du moteur KiCad.

Échec de placement : fantôme systématique, indépendamment de la distance ou
l'ancienne option ; suppression du contrôle devenu inutile dans le dialogue.
Ancrage après tous les placements, classement par distance conservé. Si aucun
visible n'existe : ordre spatial, voisin vide, groupe vide identifié par son UUID.
31 tests réussis (4,686 s), incluant résultat partiel, aucun visible,
régénération, aperçu Bottom, fusion et export miroir sans mutation de l'aperçu.
