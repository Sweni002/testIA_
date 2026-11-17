# Journal d'utilisation de l'IA

Outils utilisés : **Deepseek** 
Le récapitulatif chiffré des échanges est dans `IA/echanges.md`.

## Principe suivi

L'IA a servi d'outil de production. Chaque résultat a été contrôlé par une mesure avant d'être gardé :
- comparaison avec `attendu.json` ;
- `outils/verifier.py` ;
- tests unitaires ;
- évaluation sur des rescans simulés, pour ne pas régler les seuils sur le seul dossier d'exemple.

Les règles du TP ont servi de cadre à chaque demande : bibliothèques autorisées uniquement, aucune bibliothèque de
dédoublonnage, logique écrite soi-même, format de sortie exact, pas de commentaires dans le code.

## Étape 1 — Analyse du kit et des règles de notation

| Demande | Proposition de l'IA | Contrôle et décision |
|---|---|---|
| Analyser l'énoncé, `verifier.py`, `scoring4.py`, `attendu.json`, le bordereau et le référentiel | Lecture du barème, inventaire des cas présents dans l'exemple | Accepté. Priorités retenues : F1 sur les paires de doublons, exactitude par fichier lisible (null compris), macro-F1 sur les classes. Constat clé : le bordereau se compare sur le nom de fichier **avec** extension (`relevé R1.jpg` et `relevé R1.pdf` n'ont pas les mêmes valeurs) |

## Étape 2 — Inventaire du dossier

| Demande | Proposition de l'IA | Contrôle et décision |
|---|---|---|
| Lire l'arborescence, le zip comme sous-dossier et les PDF multipages, ignorer les fichiers système, signaler les illisibles sans plantage | `tri/inventaire.py` : parcours trié, zip lu en mémoire, rendu PDF avec pypdfium2, contrôle de la signature binaire face à l'extension | Accepté après comparaison avec `attendu.json` : chemins, nombres de pages et illisibles identiques (93 fichiers). Ajout de tests sur des fichiers cassés fabriqués : vide, texte en `.png`, PDF corrompu, JPEG tronqué, zip corrompu |

## Étape 3 — Normalisation du bordereau

| Demande | Proposition de l'IA | Contrôle et décision |
|---|---|---|
| Normaliser bâtiment, niveau et date selon le tableau du sujet | `tri/bordereau.py` et `tri/normalisation.py` : découpage en mots sans accents, règles ordonnées pour les niveaux, lecture des dates françaises | Accepté : 0 écart sur les 74 lignes de l'exemple, et chaque forme citée dans le sujet est testée |
| Gérer les fautes de frappe sur les bâtiments | Appariement approximatif (difflib) | **Rejeté** : `batimentb` et `batimenta` sont similaires à 89 %, donc un bâtiment absent du référentiel serait rattaché au mauvais. Remplacé par des règles d'inclusion de mots, avec `null` en cas d'ambiguïté |

## Étape 4 — Détection des doublons

| Demande | Proposition de l'IA | Contrôle et décision |
|---|---|---|
| Comparer les pages sans bibliothèque de dédoublonnage | Corrélation de vignettes 32×32 / 64×64 | **Rejeté** après mesure : des textes et tableaux différents mais de même gabarit obtenaient 0,94, plus que de vrais rescans |
| Méthode plus discriminante | Redressement de l'inclinaison, recadrage sur le contenu, corrélation fine recalée par FFT | Gardé, mais trop lent (61 s pour 112 pages). **Corrigé** : redressement calculé sur les coordonnées des pixels d'encre, soit 4 s au lieu de 61 s |
| Vérifier la version rapide | Scores des vraies paires effondrés | **Erreur détectée** : le signe de l'angle était inversé, repéré en comparant les deux méthodes angle par angle. Corrigé |
| Une vraie paire restait à 0,63 | Diagnostic sur image : rescan délavé, traits gris perdus par le seuil fixe | **Corrigé** : seuil d'encre adaptatif à chaque page. Fraction 0,5 choisie après un balayage 0,4 / 0,5 / 0,6 |
| Alternative : encre continue plutôt que binaire | Implémentée | **Rejetée** : plus mauvais, car le bruit de fond élargit le cadre du contenu |
| Ne pas régler le seuil sur l'exemple seul | `evaluation/evaluer_doublons.py` : rescans simulés des 200 pages d'entraînement, comparés à 59 700 paires différentes | Rappel initial de 0,64. Analyse sur images : une bande de scanner inclinée faussait le seuil d'encre. **Corrigé** dans le code (niveau sombre mesuré au centre, retrait des traits de bord). La simulation elle-même était irréaliste (bande déplacée au milieu de la page) et a aussi été **corrigée** |
| Choisir le flou et le seuil | Tableaux seuil / rappel / faux positifs pour σ = 1,0 ; 1,5 ; 2,0 | Retenu σ = 1,5 et seuil 0,76 : rappel 0,92, 2 faux sur 59 700. Contre-vérification sur l'exemple : vraies paires ≥ 0,894, différentes ≤ 0,687 |

## Étape 5 — Classification des pages

| Demande | Proposition de l'IA | Contrôle et décision |
|---|---|---|
| Classer les pages en 5 types avec les bibliothèques autorisées | 58 caractéristiques calculées (plages d'encre, lignes longues, orientations, composantes, épaisseur des traits), comparaison de 3 modèles | ExtraTrees retenu. Régression logistique **rejetée** : sur le test indépendant, elle confondait un texte avec un tableau |
| Pages tournées dans le dossier caché | Entraînement sur les 4 quarts de tour, caractéristiques invariantes | Contrôlé : macro-F1 de 1,0 aussi sur l'exemple tourné de 90° |
| Livrer un modèle fiable sur une autre machine | Export de la forêt en tableaux numpy plutôt qu'en pickle | Accepté : un pickle scikit-learn peut ne pas se relire avec une autre version. Export vérifié identique à `predict_proba` (écart 0), par un test et dans le script d'entraînement |
| Mesurer honnêtement | Validation croisée groupée par page d'origine et test indépendant sur l'exemple | Accepté. Le README précise que le 25/25 du vérificateur n'est plus une mesure indépendante, puisque le modèle final inclut l'exemple |

## Étape 6 — Tests, robustesse et qualité

| Demande | Proposition de l'IA | Contrôle et décision |
|---|---|---|
| Tests approfondis | 46 tests unittest : unitaires par module, bout en bout en sous-processus, entrées dégradées (arguments faux, bordereau absent, référentiel mal formé) | Tous passent. pyflakes a relevé 2 imports inutilisés, corrigés |
| Pas de commentaires dans le code | Un `# noqa` restant, et la ligne de commentaire du `requirements.txt` modèle | **Corrigé**, puis vérifié par une recherche de `#` et de docstrings dans tous les `.py` |
| Exécution comme le correcteur | Copie du rendu dans un autre dossier, puis `verifier.py` | 40/40 et 25/25, environ 15 à 25 s pour 112 pages |

## Étape 7 — Documentation

| Demande | Proposition de l'IA | Contrôle et décision |
|---|---|---|
| README : démarche, choix, limites | Rédaction avec les mesures | Deux chiffres faux détectés en recalculant (nombre de caractéristiques, borne des scores), puis corrigés |

## Ce que l'IA a mal fait ou mal compris, et comment je l'ai détecté

- Signe de l'angle de redressement inversé : détecté par comparaison angle par angle avec la méthode lente.
- Corrélation de vignettes trop naïve : détectée par la distribution des scores sur l'exemple.
- Encre continue : régression mesurée, idée abandonnée.
- Simulation de rescans irréaliste : détectée en affichant les pages préparées.
- Chiffres inexacts dans le README : détectés en recalculant.

## Ma part dans le travail

Le code a été généré avec l'agent IA. Ma part :
- fixer le cadre : règlement, pas de commentaires, exigence de tests ;
- imposer une validation chiffrée à chaque étape ;
- relire le code module par module pour pouvoir le modifier en séance sans IA.
