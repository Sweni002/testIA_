# Échanges avec l'IA (Claude Code, Claude Opus 5.5)

## Objectif du TP 

- Réponse : automatiser le tri des dossiers clients de Futurmap avec `trier.py`, qui produit un JSON au format
  imposé.
- Les 4 tâches : inventaire (pages, illisibles, zip), normalisation du bordereau (bâtiment, niveau, date,
  manquants), détection des doublons avec une logique écrite soi-même, classification des pages en 5 types.
- Le double enjeu : bien généraliser à un dossier caché, et une démarche de qualité (code lisible, tests, README,
  IA maîtrisée, code modifiable sans IA en séance).

## Demande initiale (résumé)

Réaliser l'outil de tri décrit par l'énoncé du TP, sous les contraintes suivantes :

  soi-même, format de sortie exact ;
- aucun commentaire dans le code ;
- tests approfondis ;
- journal d'utilisation de l'IA complet.

## Déroulé de la session (réponses et actions de l'agent, résumées)

1. **Lecture du kit** : `LISEZMOI.md`, `outils/verifier.py`, `outils/scoring4.py`, modèle de rendu, bordereau
   (Windows-1252), référentiel, `attendu.json`, échantillons d'images. Constats :
   - la correspondance se fait sur le nom de base **avec** extension (`relevé R1.jpg`, `.pdf` et `.png` ont des
     valeurs différentes) ;
   - les doublons quasi identiques diffèrent par le fond, le bruit, les bandes de scanner, l'inclinaison et le quart
     de tour.
2. **Installation** des bibliothèques autorisées manquantes (pypdfium2, scikit-learn, scipy…).
3. **Inventaire** écrit, puis comparé à `attendu.json` : 0 écart.
4. **Prototypes de doublons** mesurés sur les 6 216 paires de l'exemple :

   | Version | Vraies paires (min) | Paires différentes (max) | Remarque |
   |---|---|---|---|
   | vignette 32 px | 0,82 | 0,94 | rejetée |
   | redressement + recadrage + corrélation fine recalée | 0,63 | 0,67 | 61 s de préparation |
   | redressement rapide, signe corrigé | 0,63 | 0,66 | 4 s |
   | seuil d'encre adaptatif (fraction 0,5) | 0,826 | 0,654 | |

5. **Classification** : 58 caractéristiques calculées. Comparaison de modèles (macro-F1, validation croisée groupée /
   test sur l'exemple) :

   | Modèle | Validation croisée | Test sur l'exemple |
   |---|---|---|
   | RandomForest | 0,99 | 1,0 |
   | ExtraTrees | 0,995 | 1,0 |
   | Régression logistique | 1,0 | 0,992 |

   ExtraTrees retenu, puis exporté en numpy.
6. **Vérificateur officiel** : 65/65 en 16,6 s.
7. **Test de robustesse** sur 200 rescans simulés : rappel 0,64. Diagnostic sur images, corrections (bandes inclinées,
   niveau sombre mesuré au centre, simulation rendue réaliste). Choix σ = 1,5 et seuil 0,76 : rappel 0,92, 2 faux sur
   59 700. Vérification sur l'exemple : vraies paires ≥ 0,894, différentes ≤ 0,687.
8. **Ré-entraînement** après modification de la préparation : validation croisée 1,000, exemple indépendant 1,000
   (aussi tourné de 90°). Vérificateur : 40/40 et 25/25 en 25 s.
9. **Tests** : 46 tests, tous verts. pyflakes : 2 imports inutilisés corrigés. Contrôle : aucun commentaire ni
   docstring dans les `.py`.
10. **Rédaction** du README et de ce journal. Deux chiffres faux du README (nombre de caractéristiques, borne des
    scores) ont été vérifiés par calcul, puis corrigés.
11. **Demande : tester le rendu pour viser une bonne note.**
    - Tests (46), lint et vérificateur : tout est vert, 40/40 et 25/25.
    - Génération de 3 dossiers cachés simulés, inédits, notés avec `scoring4.py` :

      | Dossier | Partie A | Partie B | Perte |
      |---|---|---|---|
      | simulé 1 | 38,67 | 25 | F1 doublons 0,889 |
      | simulé 2 | 39,12 | 25 | F1 doublons 0,927 |
      | simulé 3 | 40 | 25 | aucune |

    - Analyse : paires manquées = rescans simulés extrêmes ; 1 faux doublon entre deux tableaux de même grille (0,786).
    - Essai d'un filtre de détail à 384 et 512 px : il ne sépare pas les cas, donc rejeté.
12. **Demande : corriger le code si besoin pour l'améliorer.**
    - Normalisation : « 2e sous-sol » → R-2 (au lieu de R-1) ; dates à tirets (« 15-mars-2024 ») reconnues.
      4 tests ajoutés.
    - Refactorisations de lisibilité : `plages()`, `nombre_pages` / `liberer_pages()`, `valeur_cellule()`.
      Caractéristiques identiques au bit près, donc modèle inchangé.
    - Contrôles : 46 tests verts, vérificateur 40/40 et 25/25 en 18,5 s, notes des dossiers simulés inchangées.
13. **Demande : revoir le seuil des doublons.**
    - Filtre de détail limité aux tableaux et textes, puis combiné au score global : toujours pas de séparation
      (vrais doublons de tableaux à 0,63 à 0,72, faux doublon à 0,686 à 0,756).
    - Décision : seuil 0,76 conservé.
14. **Demande : « donne l'objectif de ce TP ».** Réponse reprise dans la section « Objectif du TP » en haut de ce
    fichier.
