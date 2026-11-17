# Journal d'utilisation de l'IA

Outils utilisés : **Claude (Claude Code, modèle Claude Opus 5.5)**, en mode agent dans VS Code. L'agent lit les fichiers, génère le code et exécute les commandes (tests, vérificateur) sur ma machine.

Déposez dans ce dossier vos exports de conversation ou vos copier-coller (prompts + réponses).
→ Export complet de la session dans `IA/echanges.md` (48 échanges, identifiants E1…E48, mêmes numéros que le tableau ci-dessous). Le README renvoie à ce journal pour la démarche.

Principe : une seule demande globale au départ (« lis le kit, respecte les règles du TP, ne produis rien tant que je ne demande pas une étape précise »), puis **un prompt = une action mesurable**. Chaque résultat est contrôlé avant d'être gardé : comparaison à `attendu.json`, `outils/verifier.py`, tests unitaires, ou évaluation sur rescans simulés. La numérotation ci-dessous suit les étapes du travail.

| # | Ce que j'ai demandé (résumé du prompt) | Ce que l'IA a produit | Ce que j'en ai fait (accepté / corrigé / rejeté) et pourquoi |
|---|---|---|---|
| 1.1 | Lire le sujet, `verifier.py`, `scoring4.py`, `attendu.json` ; résumer le barème et les critères les plus rentables | Synthèse : A 40 / B 25 / Q 35, priorités F1 doublons (12 pts), classification (25 pts), exactitude par fichier lisible ; rappel que la sortie mal formée vaut zéro | **Accepté** — recoupé avec les sections 4 à 6 du sujet |
| 1.2 | Lister les cas particuliers du dossier d'exemple : fichiers système, zip, PDF multipages, illisibles, lignes orphelines | 93 fichiers, 1 zip, PDF multipages, 6 illisibles, lignes de bordereau sans fichier | **Accepté** — vérification manuelle de quelques entrées |
| 1.3 | Regarder dans `scoring4.py` comment le nom du bordereau est comparé aux chemins : avec ou sans extension ? | Comparaison sur le nom **avec** extension, insensible à la casse ; `relevé R1.jpg` et `relevé R1.pdf` sont deux entrées distinctes | **Accepté** — constat structurant pour la suite |
| 1.4 | Extraire toutes les formes distinctes de bâtiment, niveau et date du bordereau | Tableau des formes rencontrées | **Accepté** — recoupé avec le tableau du § 4 du sujet |
| 2.1 | Écrire `tri/inventaire.py` : parcours trié, PDF multipages via pypdfium2, JPG/PNG, zip comme sous-dossier, fichiers système ignorés | Module complet | **Accepté** — exécution sur l'exemple |
| 2.2 | Comment signaler un fichier illisible sans planter ? Contrôle de la signature binaire face à l'extension | Lecture des premiers octets, comparaison avec la signature attendue, statut `illisible`, `pages = 0` | **Accepté** — test sur les 6 illisibles de l'exemple |
| 2.3 | Comparer l'inventaire produit à `attendu.json` : chemins, pages, illisibles | Script de comparaison, 93 fichiers identiques, 0 écart | **Accepté** — résultats affichés |
| 2.4 | Ajouter des tests sur fichiers cassés fabriqués : vide, texte renommé `.png`, PDF corrompu, JPEG tronqué, zip corrompu | 5 tests unitaires | **Accepté** — tous verts |
| 3.1 | Écrire `tri/normalisation.py` : découpage en mots sans accents, règles ordonnées pour les niveaux, dates françaises | Module complet | **Accepté** — testé sur les formes citées dans le sujet |
| 3.2 | Écrire `tri/bordereau.py` : CSV Windows-1252 séparateur `;`, colonnes du sujet, comparaison de noms sans tenir compte de la casse | Module complet | **Accepté** — 74 lignes lues |
| 3.3 | Comparer les valeurs normalisées à `attendu.json` sur les 74 lignes | 0 écart | **Accepté** — écarts affichés (aucun) |
| 3.4 | Gérer les fautes de frappe sur les bâtiments par appariement approximatif | `difflib` avec seuil de similarité | **Rejeté** — `batimentb` et `batimenta` sont similaires à 89 %, donc un bâtiment absent du référentiel serait rattaché au mauvais |
| 3.5 | Remplacer l'appariement approximatif par des règles d'inclusion de mots, `null` en cas d'ambiguïté | Règles ordonnées | **Accepté** — cas ambigus renvoient bien `null` |
| 3.6 | Écrire un test pour chaque forme citée dans le tableau du § 4 | Tests paramétrés | **Accepté** — tous verts |
| 4.1 | Comparer les pages sans bibliothèque de dédoublonnage, par corrélation de vignettes 32×32 et 64×64 | Corrélation de vignettes | **Rejeté** — sur l'exemple, des documents différents de même gabarit obtiennent 0,94, plus que de vrais rescans |
| 4.2 | Proposer une méthode plus discriminante : redressement, recadrage sur le contenu, corrélation fine recalée par FFT | Pipeline complet | **Accepté avec réserve** — scores cohérents, mais 61 s pour 112 pages |
| 4.3 | Mesurer chaque version sur les 6 216 paires de l'exemple (min vraies paires / max paires différentes) | Tableau : vignette 0,82/0,94 ; redressement lent 0,63/0,67 ; redressement rapide 0,63/0,66 ; seuil adaptatif 0,826/0,654 | **Accepté** — conforme aux exécutions |
| 4.4 | 61 s, c'est trop lent : calculer le redressement sur les coordonnées des pixels d'encre plutôt que sur l'image entière | Redressement par moments | **Corrigé** — 4 s au lieu de 61 s |
| 4.5 | Comparer la version rapide à la version lente, angle par angle | Comparaison automatique | **Corrigé** — scores des vraies paires effondrés : **signe de l'angle inversé**, détecté puis corrigé |
| 4.6 | Une vraie paire reste à 0,63 : diagnostiquer sur l'image | Rescan délavé, traits gris perdus par le seuil fixe | **Corrigé** — seuil d'encre adaptatif à chaque page |
| 4.7 | Balayer la fraction du seuil d'encre : 0,4 / 0,5 / 0,6, et comparer | Tableau comparatif | **Accepté** — 0,5 retenu |
| 4.8 | Tester l'encre continue plutôt que binaire | Implémentation | **Rejeté** — plus mauvais, le bruit de fond élargit le cadre du contenu |
| 4.9 | Ne pas régler le seuil sur l'exemple seul : écrire `evaluation/evaluer_doublons.py` avec rescans simulés des 200 pages d'entraînement contre 59 700 paires différentes | Script d'évaluation | **Accepté** — rappel initial 0,64, donc insuffisant |
| 4.10 | Analyser sur image les paires manquées par l'évaluation | Une bande de scanner inclinée faussait le seuil d'encre | **Corrigé** — niveau sombre mesuré au centre, retrait des traits de bord |
| 4.11 | La simulation est irréaliste : la bande de scanner est au milieu de la page. Corriger la simulation | Bande placée en bord de page | **Corrigé** — rescans simulés visuellement plausibles |
| 4.12 | Produire un tableau seuil / rappel / faux positifs pour σ = 1,0 ; 1,5 ; 2,0 | Tableaux comparatifs | **Accepté** — σ = 1,5 et seuil 0,76 retenus : rappel 0,92, 2 faux sur 59 700 |
| 4.13 | Contre-vérifier sur l'exemple : scores des vraies paires et des paires différentes | Vraies paires ≥ 0,894, différentes ≤ 0,687 | **Accepté** — distributions affichées |
| 5.1 | Classer les pages en 5 types avec les bibliothèques autorisées ; proposer des caractéristiques et comparer plusieurs modèles | 58 caractéristiques, comparaison RandomForest / ExtraTrees / régression logistique (validation croisée groupée + test sur l'exemple) | **Accepté** — ExtraTrees retenu ; régression logistique **rejetée** (confusion texte / tableau sur test indépendant) |
| 5.2 | Entraîner sur les 4 quarts de tour et rendre les caractéristiques invariantes | Entraînement avec rotations | **Accepté** — macro-F1 de 1,0 aussi sur l'exemple tourné de 90° |
| 5.3 | Exporter la forêt en tableaux numpy plutôt qu'en pickle, pour éviter les problèmes de version | Export numpy | **Accepté** — un pickle scikit-learn peut ne pas se relire avec une autre version |
| 5.4 | Vérifier que l'export donne exactement `predict_proba` (écart 0), par un test et dans le script d'entraînement | Test unitaire + vérification dans le script | **Accepté** — écart 0 |
| 5.5 | Mesurer honnêtement : validation croisée groupée et test indépendant sur l'exemple | Protocole complet ; note dans le README que le 25/25 du vérificateur n'est plus une mesure indépendante | **Accepté** — résultats cohérents entre les deux protocoles |
| 6.1 | Écrire des tests unittest : unitaires par module, bout en bout en sous-processus, entrées dégradées (arguments faux, bordereau absent, référentiel mal formé) | 46 tests | **Accepté** — tous passent |
| 6.2 | Passer pyflakes et corriger les avertissements | 2 imports inutilisés | **Corrigé** — correction appliquée |
| 6.3 | Vérifier qu'il n'y a aucun commentaire ni docstring dans les `.py`, et pas de commentaire dans `requirements.txt` | Un `# noqa` restant, une ligne de commentaire dans `requirements.txt` | **Corrigé** — recherche de `#` et de docstrings dans tous les `.py` |
| 6.4 | Copier le rendu dans un autre dossier et exécuter `verifier.py` comme le correcteur | Exécution | **Accepté** — 40/40 et 25/25, 15 à 25 s pour 112 pages |
| 6.5 | Vérifier que le JSON respecte exactement le format imposé : clés, types, ordre des classes, notation `chemin#numéro` des doublons | Script de validation et test unitaire | **Accepté** — comparaison clé par clé avec le § 3 |
| 7.1 | Rédiger le README : démarche, choix, limites, avec les mesures obtenues | Rédaction complète | **Accepté** — relecture section par section |
| 7.2 | Recalculer tous les chiffres cités dans le README et signaler les écarts | Deux chiffres faux (nombre de caractéristiques, borne des scores) | **Corrigé** — recalcul effectué |
| 8.1 | Générer 3 dossiers clients inédits de 71 fichiers : référentiels différents, formes de bordereau absentes de l'exemple, zip avec sous-dossier, fichiers cassés, copies exactes, rescans simulés | Générateur complet | **Accepté** — inspection manuelle de quelques fichiers |
| 8.2 | Noter chaque dossier simulé avec `scoring4.py` | Partie A : 38,67 / 39,12 / 40 ; Partie B : 25/25 (surestimée, pages issues de l'entraînement) | **Accepté** — scores détaillés relus |
| 8.3 | Lister les paires manquées ou en trop avec leur score, pour comprendre les points perdus | Paires manquées = rescans les plus dégradés ; 1 faux doublon (0,786) = deux tableaux différents à grille identique | **Accepté** — faux doublon vérifié visuellement |
| 9.1 | Sonder des formes de bordereau plausibles absentes de l'exemple et signaler les cas mal normalisés | **2 défauts** : « 2e sous-sol » → R-1 au lieu de R-2 ; dates à tirets (« 15-mars-2024 », « 1er-avril-2022 ») → `null` | **Corrigé** — 4 tests ajoutés, README mis à jour |
| 9.2 | Fusionner le calcul des plages d'encre écrit deux fois | Fonction `plages()` | **Accepté** — caractéristiques identiques au bit près, pas de ré-entraînement |
| 9.3 | Remplacer `[None] * len(...)` par `nombre_pages` et `liberer_pages()` | Refactorisation | **Accepté** — 46 tests verts, vérificateur 40/40 et 25/25 |
| 9.4 | Sortir `valeur_cellule()` de la boucle de lecture du bordereau | Extraction | **Accepté** — notes des dossiers simulés inchangées |
| 10.1 | Éliminer le faux doublon entre tableaux à grille identique : comparer le détail fin (texte des cases) à 384 et 512 px, après recalage | Filtre de détail | **Rejeté** — le faux doublon (0,756) dépasse plusieurs vrais doublons (jusqu'à 0,572 sur l'exemple réel) |
| 10.2 | Appliquer le même filtre seulement aux paires de classes tableau et texte, puis combiner score global et détail | Variante ciblée | **Rejeté** — toujours pas de séparation (vrais doublons de tableaux à 0,63 à 0,72) ; seuil 0,76 conservé, limite documentée dans le README |
| 11.1 | Donner l'objectif du TP en une synthèse | Automatiser le tri d'un dossier client (inventaire, normalisation, doublons, classification) au format JSON imposé ; double enjeu : généraliser à un dossier caché et une démarche de qualité | **Accepté** — correspond aux sections 1 à 7 et au barème ; m'a servi de grille de relecture avant rendu |

## Ce que l'IA a mal fait ou mal compris, et comment je l'ai détecté

- **Signe de l'angle de redressement inversé** (4.5) : détecté en comparant angle par angle la version rapide et la version lente.
- **Corrélation de vignettes trop naïve** (4.1) : détectée par la distribution des scores sur l'exemple — des documents différents obtenaient 0,94.
- **Encre continue** (4.8) : régression mesurée, idée abandonnée.
- **Simulation de rescans irréaliste** (4.11) : détectée en affichant les pages préparées (bande de scanner au milieu de la page).
- **Chiffres inexacts dans le README** (7.2) : détectés en recalculant (nombre de caractéristiques, borne des scores).
- **Normalisation incomplète** (9.1) : détectée en testant des formes absentes de l'exemple (« 2e sous-sol », dates à tirets).
- **Filtre de détail pour les doublons** (10.1, 10.2) : piste séduisante, mais réfutée par la mesure, donc pas intégrée.

## Ce que j'ai écrit ou conçu sans IA

- **Le cadre** : règles du TP (bibliothèques autorisées, pas de dédoublonnage tout fait, format de sortie exact, aucun commentaire dans le code, tests approfondis), repris dans chaque prompt.
- **Le découpage en prompts unitaires** : refus d'une demande globale, une action mesurable par prompt, pour pouvoir contrôler chaque résultat séparément (grille des étapes 1 à 11).
- **Le protocole de validation** : comparaison à `attendu.json`, `verifier.py`, tests unitaires, rescans simulés — imposé à chaque étape avant d'accepter un résultat.
- **Les cas de test inventés** : fichiers cassés fabriqués, formes de bordereau absentes de l'exemple (« 2e sous-sol », dates à tirets), dossiers clients simulés avec référentiels inédits.
- **Les décisions d'acceptation, de correction et de rejet** : seuil de similarité rejeté, vignettes rejetées, encre continue rejetée, filtre de détail rejeté, seuil 0,76 conservé.
- **La structure et le plan du README**, puis la vérification des chiffres cités.
- **Ce journal et l'export des échanges** (`IA/echanges.md`).
- **La relecture du code module par module**, pour pouvoir le modifier en séance sans IA.

*Le code Python lui-même a été généré par l'agent IA, sous ce cadre et ces contrôles.*