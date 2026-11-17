# Échanges avec l'IA — export

**Outil :** Claude Code, modèle Claude Opus 5.5, en mode agent dans VS Code.
**Périmètre :** session complète de réalisation du TP Futurmap.
**Format :** le cadrage d'ouverture n'est pas numéroté ; les prompts suivants portent l'identifiant du journal (`IA/journal_ia.md`), de la forme En.p, où `n` est l'étape et `p` le numéro du prompt dans l'étape. Les prompts sont reformulés pour la lisibilité ; les réponses de l'agent et les actions exécutées sont résumées. Les décisions sont analysées dans le journal.

---

## Cadrage (hors compte)

Le premier message demande à l'agent de lire le kit et d'expliciter l'objectif du TP, sans produire aucun fichier.

> « Lis le kit (sujet, `outils/verifier.py`, `scoring4.py`, `attendu.json`, bordereau, référentiel, échantillons d'images) et donne-moi l'objectif de ce TP : ce que le programme doit produire, les tâches attendues, et la façon dont le travail est évalué. Ne produis aucun fichier pour l'instant. »

- **Réponse :** objectif résumé en quatre tâches (inventaire, normalisation du bordereau, doublons, classification) et format JSON imposé ; double enjeu, généraliser à un dossier caché et tenir une démarche de qualité ; barème A 40 / B 25 / Q 35, avec la règle « sortie mal formée = zéro ».
- **Contrôle :** confronté aux sections 1 à 7 du sujet et au barème.
- **Décision :** Accepté. Cette lecture a servi de cadre pour découper le travail en étapes.

Ce premier échange ne compte pas dans les 49 prompts de production listés ci-dessous : il ne demande aucun code. Chaque prompt suivant porte sur **une seule action mesurable**, avec le critère de contrôle annoncé dans la demande.

**Bilan :** 49 échanges numérotés — 34 acceptés en l'état, 1 accepté avec réserve, 9 corrigés après contrôle, 5 rejetés.

---

## Étape 1 — Analyse du kit

**E1.1 — Lire le barème**
- **Prompt :** « Lis le sujet, `outils/verifier.py`, `scoring4.py` et `attendu.json`. Résume le barème et indique quels critères rapportent le plus de points. »
- **Réponse :** synthèse (A 40 / B 25 / Q 35), priorités : F1 doublons (12), classification (25), exactitude par fichier lisible. Rappel que la sortie mal formée vaut zéro.
- **Contrôle :** relecture croisée avec les sections 4 à 6 du sujet.
- **Décision :** Accepté.

**E1.2 — Inventorier les cas présents dans l'exemple**
- **Prompt :** « Liste les cas particuliers du dossier d'exemple : fichiers système, archives, PDF multipages, illisibles, lignes de bordereau sans fichier. »
- **Réponse :** 93 fichiers, 1 zip, PDF multipages, 6 illisibles, lignes orphelines.
- **Contrôle :** vérification manuelle de quelques entrées.
- **Décision :** Accepté.

**E1.3 — Comparaison bordereau / fichiers**
- **Prompt :** « Regarde dans `scoring4.py` comment le nom du fichier du bordereau est comparé aux chemins. Avec ou sans extension ? »
- **Réponse :** comparaison sur le nom **avec** extension, insensible à la casse ; `relevé R1.jpg` et `relevé R1.pdf` sont deux entrées distinctes.
- **Contrôle :** lecture du code de scoring.
- **Décision :** Accepté — constat structurant.

**E1.4 — Recenser les formes de bordereau**
- **Prompt :** « Extrais toutes les formes distinctes de bâtiment, niveau et date du bordereau. »
- **Réponse :** tableau des formes rencontrées.
- **Contrôle :** recoupement avec le tableau du § 4 du sujet.
- **Décision :** Accepté.

---

## Étape 2 — Inventaire

**E2.1 — Écrire l'inventaire**
- **Prompt :** « Écris `tri/inventaire.py` : parcours récursif trié, PDF multipages via pypdfium2, JPG/PNG, zip comme sous-dossier, fichiers système ignorés. »
- **Réponse :** module complet.
- **Contrôle :** exécution sur l'exemple.
- **Décision :** Accepté.

**E2.2 — Illisibles sans plantage**
- **Prompt :** « Comment signaler un fichier illisible sans planter ? Contrôle la signature binaire face à l'extension. »
- **Réponse :** lecture des premiers octets, comparaison avec la signature attendue, statut `illisible`, `pages = 0`.
- **Contrôle :** test sur les 6 illisibles de l'exemple.
- **Décision :** Accepté.

**E2.3 — Comparaison avec `attendu.json`**
- **Prompt :** « Compare l'inventaire avec `attendu.json` : chemins, pages, illisibles. »
- **Réponse :** script de comparaison, 93 fichiers identiques, 0 écart.
- **Contrôle :** affichage des résultats.
- **Décision :** Accepté.

**E2.4 — Tests sur fichiers cassés fabriqués**
- **Prompt :** « Ajoute des tests sur fichiers cassés fabriqués : vide, texte renommé `.png`, PDF corrompu, JPEG tronqué, zip corrompu. »
- **Réponse :** 5 tests unitaires.
- **Contrôle :** exécution, tous verts.
- **Décision :** Accepté.

---

## Étape 3 — Normalisation

**E3.1 — Écrire la normalisation**
- **Prompt :** « Écris `tri/normalisation.py` : découpage en mots sans accents, règles ordonnées pour les niveaux, dates françaises. »
- **Réponse :** module complet.
- **Contrôle :** tests sur les formes citées dans le sujet.
- **Décision :** Accepté.

**E3.2 — Lire le bordereau**
- **Prompt :** « Écris `tri/bordereau.py` : CSV Windows-1252 séparateur `;`, colonnes du sujet, comparaison de noms sans tenir compte de la casse. »
- **Réponse :** module complet.
- **Contrôle :** 74 lignes lues.
- **Décision :** Accepté.

**E3.3 — Comparaison normalisée avec `attendu.json`**
- **Prompt :** « Compare les valeurs normalisées avec `attendu.json` sur les 74 lignes. »
- **Réponse :** 0 écart.
- **Contrôle :** affichage des écarts (aucun).
- **Décision :** Accepté.

**E3.4 — Fautes de frappe sur les bâtiments**
- **Prompt :** « Gère les fautes de frappe sur les bâtiments par appariement approximatif. »
- **Réponse :** `difflib` avec seuil de similarité.
- **Contrôle :** `batimentb` et `batimenta` sont similaires à 89 % → risque de rattacher au mauvais bâtiment.
- **Décision :** **Rejeté**.

**E3.5 — Règles d'inclusion de mots**
- **Prompt :** « Remplace l'appariement approximatif par des règles d'inclusion de mots, avec `null` en cas d'ambiguïté. »
- **Réponse :** règles ordonnées.
- **Contrôle :** cas ambigus renvoient bien `null`.
- **Décision :** Accepté.

**E3.6 — Tester chaque forme du § 4**
- **Prompt :** « Écris un test pour chaque forme citée dans le tableau du § 4. »
- **Réponse :** tests paramétrés.
- **Contrôle :** tous verts.
- **Décision :** Accepté.

---

## Étape 4 — Détection des doublons

**E4.1 — Première méthode (vignettes)**
- **Prompt :** « Compare les pages sans bibliothèque de dédoublonnage, par corrélation de vignettes 32×32 et 64×64. »
- **Réponse :** corrélation de vignettes.
- **Contrôle :** sur l'exemple, des documents différents de même gabarit obtiennent 0,94, plus que de vrais rescans.
- **Décision :** **Rejeté**.

**E4.2 — Pipeline plus discriminant**
- **Prompt :** « Propose une méthode plus discriminante : redressement, recadrage sur le contenu, corrélation fine recalée par FFT. »
- **Réponse :** pipeline complet.
- **Contrôle :** scores cohérents, mais 61 s pour 112 pages.
- **Décision :** Accepté **avec réserve** de performance.

**E4.3 — Mesure des prototypes sur les 6 216 paires de l'exemple**
- **Prompt :** « Mesure chaque version sur les 6 216 paires de l'exemple : min des vraies paires, max des paires différentes. »
- **Réponse :**

  | Version | Vraies paires (min) | Paires différentes (max) | Remarque |
  |---|---|---|---|
  | vignette 32 px | 0,82 | 0,94 | rejetée (voir E4.1) |
  | redressement + recadrage + corrélation fine recalée | 0,63 | 0,67 | 61 s de préparation |
  | redressement rapide, signe corrigé | 0,63 | 0,66 | 4 s |
  | seuil d'encre adaptatif (fraction 0,5) | 0,826 | 0,654 | retenu |

- **Contrôle :** tableau conforme aux exécutions.
- **Décision :** Accepté.

**E4.4 — Optimiser le redressement**
- **Prompt :** « 61 s, c'est trop lent. Calcule le redressement sur les coordonnées des pixels d'encre plutôt que sur l'image entière. »
- **Réponse :** redressement par moments.
- **Contrôle :** 4 s au lieu de 61 s.
- **Décision :** Corrigé.

**E4.5 — Vérifier la version rapide**
- **Prompt :** « Compare la version rapide à la version lente angle par angle. »
- **Réponse :** comparaison automatique.
- **Contrôle :** scores des vraies paires effondrés → **signe de l'angle inversé**.
- **Décision :** Corrigé.

**E4.6 — Vraie paire à 0,63**
- **Prompt :** « Une vraie paire reste à 0,63. Diagnostique sur l'image. »
- **Réponse :** rescan délavé, traits gris perdus par le seuil fixe.
- **Contrôle :** affichage de l'image et du masque d'encre.
- **Décision :** Corrigé (seuil adaptatif).

**E4.7 — Fraction du seuil adaptatif**
- **Prompt :** « Balaye la fraction du seuil : 0,4 / 0,5 / 0,6, et compare. »
- **Réponse :** tableau comparatif.
- **Contrôle :** 0,5 retenu.
- **Décision :** Accepté.

**E4.8 — Encre continue**
- **Prompt :** « Teste l'encre continue plutôt que binaire. »
- **Réponse :** implémentation.
- **Contrôle :** plus mauvais, le bruit de fond élargit le cadre.
- **Décision :** **Rejeté**.

**E4.9 — Ne pas régler le seuil sur l'exemple seul**
- **Prompt :** « Écris `evaluation/evaluer_doublons.py` : rescans simulés des 200 pages d'entraînement, comparés à 59 700 paires différentes. »
- **Réponse :** script d'évaluation.
- **Contrôle :** rappel initial 0,64.
- **Décision :** Accepté — insuffisant.

**E4.10 — Analyse des paires manquées**
- **Prompt :** « Analyse sur image les paires manquées. »
- **Réponse :** une bande de scanner inclinée faussait le seuil d'encre.
- **Contrôle :** visualisation.
- **Décision :** Corrigé (niveau sombre mesuré au centre, retrait des traits de bord).

**E4.11 — Corriger la simulation**
- **Prompt :** « La bande de scanner est au milieu de la page, c'est irréaliste. Corrige la simulation. »
- **Réponse :** bande placée en bord de page.
- **Contrôle :** rescans visuellement plausibles.
- **Décision :** Corrigé.

**E4.12 — Choisir flou et seuil**
- **Prompt :** « Tableau seuil / rappel / faux positifs pour σ = 1,0 ; 1,5 ; 2,0. »
- **Réponse :** tableaux comparatifs.
- **Contrôle :** σ = 1,5 et seuil 0,76 retenus → rappel 0,92, 2 faux sur 59 700.
- **Décision :** Accepté.

**E4.13 — Contre-vérifier sur l'exemple**
- **Prompt :** « Contre-vérifie sur l'exemple : scores des vraies paires et des paires différentes. »
- **Réponse :** vraies paires ≥ 0,894, différentes ≤ 0,687.
- **Contrôle :** affichage des distributions.
- **Décision :** Accepté.

---

## Étape 5 — Classification

**E5.1 — Caractéristiques et comparaison de modèles**
- **Prompt :** « Classe les pages en 5 types avec les bibliothèques autorisées. Propose des caractéristiques calculables et compare plusieurs modèles. »
- **Réponse :** 58 caractéristiques, comparaison de modèles :

  | Modèle | Validation croisée groupée | Test sur l'exemple |
  |---|---|---|
  | RandomForest | 0,99 | 1,0 |
  | ExtraTrees | 0,995 | 1,0 |
  | Régression logistique | 1,0 | 0,992 |

- **Contrôle :** validation croisée groupée par page d'origine.
- **Décision :** Accepté — ExtraTrees retenu ; régression logistique **rejetée** (confusion texte / tableau sur test indépendant).

**E5.2 — Pages tournées**
- **Prompt :** « Entraîne sur les 4 quarts de tour et rends les caractéristiques invariantes. »
- **Réponse :** entraînement avec rotations.
- **Contrôle :** macro-F1 de 1,0 sur l'exemple tourné de 90°.
- **Décision :** Accepté.

**E5.3 — Export portable**
- **Prompt :** « Exporte la forêt en tableaux numpy plutôt qu'en pickle, pour éviter les problèmes de version. »
- **Réponse :** export numpy.
- **Contrôle :** un pickle scikit-learn peut ne pas se relire avec une autre version.
- **Décision :** Accepté.

**E5.4 — Vérifier l'export**
- **Prompt :** « Vérifie que l'export donne exactement `predict_proba` (écart 0), par un test et dans le script d'entraînement. »
- **Réponse :** test unitaire + vérification dans le script.
- **Contrôle :** écart 0.
- **Décision :** Accepté.

**E5.5 — Mesure honnête**
- **Prompt :** « Mesure honnêtement : validation croisée groupée et test indépendant sur l'exemple. »
- **Réponse :** protocole complet ; note dans le README que le 25/25 du vérificateur n'est plus une mesure indépendante.
- **Contrôle :** cohérence entre les deux protocoles.
- **Décision :** Accepté.

---

## Étape 6 — Tests, robustesse et qualité

**E6.1 — Écrire les tests**
- **Prompt :** « Écris des tests unittest : unitaires par module, bout en bout en sous-processus, entrées dégradées (arguments faux, bordereau absent, référentiel mal formé). »
- **Réponse :** 46 tests.
- **Contrôle :** tous passent.
- **Décision :** Accepté.

**E6.2 — pyflakes**
- **Prompt :** « Passe pyflakes et corrige les avertissements. »
- **Réponse :** 2 imports inutilisés.
- **Contrôle :** correction appliquée.
- **Décision :** Corrigé.

**E6.3 — Aucun commentaire dans le code**
- **Prompt :** « Vérifie qu'il n'y a aucun commentaire ni docstring dans les `.py`, et pas de commentaire dans `requirements.txt`. »
- **Réponse :** un `# noqa` restant, une ligne de commentaire dans `requirements.txt`.
- **Contrôle :** recherche de `#` et de docstrings dans tous les `.py`.
- **Décision :** Corrigé.

**E6.4 — Exécuter comme le correcteur**
- **Prompt :** « Copie le rendu dans un autre dossier et exécute `verifier.py` comme le correcteur. »
- **Réponse :** exécution.
- **Contrôle :** 40/40 et 25/25 en 15 à 25 s pour 112 pages.
- **Décision :** Accepté.

**E6.5 — Vérifier le format de sortie**
- **Prompt :** « Vérifie que le JSON respecte exactement le format imposé : clés, types, ordre des classes, notation `chemin#numéro` des doublons. »
- **Réponse :** script de validation et test unitaire.
- **Contrôle :** comparaison clé par clé avec le § 3 du sujet.
- **Décision :** Accepté.

---

## Étape 7 — Documentation

**E7.1 — Rédiger le README**
- **Prompt :** « Rédige le README : démarche, choix, limites, avec les mesures obtenues. »
- **Réponse :** rédaction complète.
- **Contrôle :** relecture section par section.
- **Décision :** Accepté.

**E7.2 — Vérifier les chiffres du README**
- **Prompt :** « Recalcule tous les chiffres cités dans le README et signale les écarts. »
- **Réponse :** deux chiffres faux (nombre de caractéristiques, borne des scores).
- **Contrôle :** recalcul effectué.
- **Décision :** Corrigé.

---

## Étape 8 — Dossiers cachés simulés

**E8.1 — Générer 3 dossiers inédits**
- **Prompt :** « Génère 3 dossiers clients inédits de 71 fichiers chacun. Référentiels différents (Bâtiment Nord/Sud, Gymnase, Parking), formes de bordereau absentes de l'exemple, zip avec sous-dossier, fichiers cassés, copies exactes, rescans simulés. »
- **Réponse :** générateur complet.
- **Contrôle :** inspection manuelle de quelques fichiers.
- **Décision :** Accepté.

**E8.2 — Notation des dossiers simulés**
- **Prompt :** « Note chaque dossier simulé avec `scoring4.py`. »
- **Réponse :**

  | Dossier | Partie A | Partie B | Perte |
  |---|---|---|---|
  | simulé 1 | 38,67 | 25 | F1 doublons 0,889 |
  | simulé 2 | 39,12 | 25 | F1 doublons 0,927 |
  | simulé 3 | 40 | 25 | aucune |

  Partie B surestimée, les pages viennent de l'entraînement.
- **Contrôle :** relecture des scores détaillés.
- **Décision :** Accepté.

**E8.3 — Comprendre les points perdus**
- **Prompt :** « Liste les paires manquées ou en trop avec leur score. »
- **Réponse :** paires manquées = rescans simulés les plus dégradés ; 1 faux doublon (0,786) = deux tableaux différents avec la même grille.
- **Contrôle :** vérification visuelle du faux doublon.
- **Décision :** Accepté.

---

## Étape 9 — Corrections et lisibilité

**E9.1 — Sonder des formes de bordereau absentes**
- **Prompt :** « Sonde des formes plausibles absentes de l'exemple et signale les cas mal normalisés. »
- **Réponse :** **2 défauts trouvés** — « 2e sous-sol » → R-1 au lieu de R-2 ; dates à tirets (« 15-mars-2024 », « 1er-avril-2022 ») → `null`.
- **Contrôle :** reproduction sur entrées fabriquées.
- **Décision :** Corrigé — 4 tests ajoutés, README mis à jour.

**E9.2 — Lisibilité : `plages()`**
- **Prompt :** « Fusionne le calcul des plages d'encre écrit deux fois. »
- **Réponse :** fonction `plages()`.
- **Contrôle :** caractéristiques identiques au bit près.
- **Décision :** Accepté — pas de ré-entraînement.

**E9.3 — Lisibilité : pages**
- **Prompt :** « Remplace `[None] * len(...)` par `nombre_pages` et `liberer_pages()`. »
- **Réponse :** refactorisation.
- **Contrôle :** 46 tests verts, vérificateur 40/40 et 25/25.
- **Décision :** Accepté.

**E9.4 — Lisibilité : `valeur_cellule()`**
- **Prompt :** « Sors `valeur_cellule()` de la boucle de lecture du bordereau. »
- **Réponse :** extraction.
- **Contrôle :** notes des dossiers simulés inchangées.
- **Décision :** Accepté.

---

## Étape 10 — Faux doublon entre tableaux

**E10.1 — Second filtre de détail**
- **Prompt :** « Compare le détail fin (texte des cases) à 384 et 512 px, après recalage, pour éliminer le faux doublon entre tableaux à grille identique. »
- **Réponse :** filtre de détail.
- **Contrôle :** le faux doublon (0,756) dépasse plusieurs vrais doublons (jusqu'à 0,572 sur l'exemple réel).
- **Décision :** **Rejeté**.

**E10.2 — Variante limitée aux tableaux et textes**
- **Prompt :** « Applique le même filtre seulement aux paires de classes tableau et texte, puis combine score global et détail. »
- **Réponse :** variante ciblée.
- **Contrôle :** toujours pas de séparation (vrais doublons de tableaux à 0,63 à 0,72, faux doublon à 0,686 à 0,756).
- **Décision :** **Rejeté** — seuil 0,76 conservé, limite documentée dans le README.

---

## Étape 11 — Relecture de l'objectif

**E11.1 — Redonner l'objectif en synthèse**
- **Prompt :** « Redonne l'objectif de ce TP en une synthèse, pour relire le rendu. »
- **Réponse :** automatiser le tri d'un dossier client (inventaire, normalisation du bordereau, doublons, classification) au format JSON imposé. Double enjeu : généraliser à un dossier caché, et une démarche de qualité.
- **Contrôle :** correspondance avec les sections 1 à 7 de l'énoncé et le barème (A 40, B 25, Q 35).
- **Décision :** Accepté. Reprise, sans code, de la lecture d'ouverture : la première synthèse avait servi à planifier, celle-ci sert de grille de relecture avant le rendu.

---

## Récapitulatif

- **1 cadrage hors compte** + **49 échanges numérotés**.
- **34 acceptés en l'état**, **1 accepté avec réserve** (E4.2), **9 corrigés après contrôle**, **5 rejetés**.
- Les 5 rejets : appariement approximatif sur les bâtiments (E3.4), corrélation de vignettes (E4.1), encre continue (E4.8), filtre de détail (E10.1 et E10.2).
- Les 9 corrections : redressement accéléré (E4.4), signe de l'angle (E4.5), seuil adaptatif (E4.6), niveau sombre au centre / retrait des traits de bord (E4.10), simulation irréaliste (E4.11), imports inutilisés (E6.2), `# noqa` et commentaire `requirements.txt` (E6.3), chiffres du README (E7.2), normalisation incomplète (E9.1).