# TP Développeur Méthodes — NISEDRALAZA Andriamanankohoavy

## Lancer le rendu

Python 3.10 ou plus (développé et testé avec Python 3.14, sans carte graphique).

```
pip install -r requirements.txt
python trier.py <dossier_client> <bordereau.csv> <referentiel.json> <sortie.json>
```

À l'exécution, `trier.py` n'utilise que numpy, Pillow, scipy et pypdfium2 (toutes dans la liste autorisée).
scikit-learn ne sert qu'à l'entraînement : le modèle livré (`model/foret.npz`) est un fichier de tableaux numpy,
relu sans pickle. Il n'y a donc pas de risque d'incompatibilité de version de scikit-learn sur la machine de correction.

Ré-entraîner le modèle (environ 3 minutes) :

```
python model/entrainer.py --entrainement <kit>/donnees/entrainement --exemple <kit>/donnees/dossier_exemple
```

`--exemple` est facultatif. S'il est donné, il sert d'abord de jeu de test indépendant, puis il est ajouté aux
données d'entraînement du modèle final. Les mesures sont écrites dans `model/metriques.json`.

Résultat de `python outils/verifier.py` sur le dossier d'exemple : **A = 40/40, B = 25/25, en 25 s** pour 112 pages.

### Organisation du code

| Fichier | Rôle |
|---|---|
| `trier.py` | point d'entrée : arguments, écriture du JSON |
| `tri/pipeline.py` | assemblage : inventaire → bordereau → analyse des pages → classes, doublons, manquants |
| `tri/inventaire.py` | parcours du dossier et des zip, lecture des PDF et images, détection des illisibles |
| `tri/bordereau.py` | lecture du CSV, correspondance avec les fichiers, référentiel, manquants |
| `tri/normalisation.py` | règles de normalisation bâtiment / niveau / date |
| `tri/image.py` | préparation commune d'une page : encre, bandes de scanner, redressement, recadrage |
| `tri/doublons.py` | signatures de page, similarité, regroupement |
| `tri/caracteristiques.py` | caractéristiques calculées pour la classification |
| `tri/classification.py` | forêt d'arbres exportée en numpy : export, sauvegarde, prédiction |
| `model/entrainer.py` | entraînement, validation, export du modèle |
| `evaluation/evaluer_doublons.py` | mesure des doublons sur des rescans simulés |

## Inventaire et lecture des fichiers

- Parcours récursif trié (sortie stable). Les chemins sont relatifs au dossier client, avec `/`, en Unicode NFC.
- Ignorés : `Thumbs.db`, `.DS_Store`, `desktop.ini` (sans tenir compte de la casse), ainsi que `__MACOSX/` et `._*`
  dans les archives.
- `.zip` : lu en mémoire comme un sous-dossier (`archive.zip/sous/fichier.jpg`). Les zip imbriqués sont gérés.
  Les noms non UTF-8 (drapeau zip absent) sont relus en cp437 → UTF-8. Un zip corrompu est signalé illisible.
- PDF : rendu de chaque page avec pypdfium2. Le nombre de pages est celui du document.
- Images JPG/PNG (et TIFF/BMP/GIF) : une page. L'orientation EXIF est appliquée.
- **Illisible** : fichier vide, signature binaire ne correspondant pas à l'extension (texte nommé `.png`,
  PNG nommé `.jpg`, etc.), extension non prise en charge, ou toute erreur de décodage (PDF cassé, image tronquée).
  Le statut est alors `illisible`, avec `pages: 0`, des champs à `null` et `classes: []`. Aucune exception ne remonte.
- Chaque page est convertie en niveaux de gris et réduite à 1000 px au plus grand côté, ce qui borne la mémoire.

## Normalisation du bordereau

Lecture : on tente UTF-8 strict, sinon Windows-1252. Le séparateur `;` est attendu (`\t` et `,` sont acceptés en
secours). Les colonnes sont repérées par leur en-tête (« fichier », « bâtiment », « niveau », « date »), avec repli sur
l'ordre du sujet. La correspondance avec un fichier se fait sur le **nom de base avec extension**, sans tenir compte de
la casse (`casefold` + NFC). Si un nom apparaît deux fois, les champs vides de la première ligne sont complétés par la
suivante. `manquants` contient les noms tels qu'écrits dans le bordereau, sans doublon.

Toutes les comparaisons se font sur une forme simplifiée : sans accents, en minuscules, ponctuation remplacée par des espaces.

- **Bâtiment** : chaque code, nom et alias du référentiel est découpé en mots. `bat`, `bât`, `bat.` et les formes
  collées (`BatA`) deviennent `batiment`. On cherche ensuite, dans l'ordre :
  1. une forme identique (espaces ignorés) ;
  2. la forme la plus longue contenue dans la valeur (`Bat A logements neufs` → BA) ;
  3. une seule forme qui contient la valeur (`Bureaux` → BB).

  En cas d'ambiguïté, ou si rien ne correspond, la valeur est `null`. Pas d'appariement approximatif de type
  distance d'édition : avec `Bâtiment A` / `Bâtiment B`, il confondrait les bâtiments.
- **Niveau** : expressions régulières appliquées dans l'ordre suivant.
  - toiture / terrasse / TT → `TT`
  - RDC / rez → `R+0`
  - SS n, sous-sol n, S-Sol n, « 2e sous-sol » → `R-n` ; « sous-sol » sans numéro → `R-1`
  - R±n, Rn, Niv n, Niveau ±n, Etage n → `R±n`
  - « n er/e/ème étage » → `R+n` (les ordinaux en lettres, comme « premier », sont convertis en chiffres)

  Le résultat n'est gardé que s'il figure dans la liste `niveaux` du référentiel.
- **Date** : AAAA-MM-JJ, JJ/MM/AAAA, JJ-MM-AA, JJ.MM.AA… (lecture française jour/mois, années à 2 chiffres → 20xx si
  < 70), mois en toutes lettres ou abrégés avec ou sans accent, séparés par des espaces ou des tirets (« 3 févr. 2021 »,
  « 1er août 2022 », « 15-mars-2024 », jour de semaine toléré), AAAAMMJJ. Les dates impossibles (31/02) donnent `null`. Si le mois dépasse 12 mais que le jour est valide
  comme mois, on tente l'inversion.

Cas non couverts : fautes de frappe dans les noms de bâtiments, dates sans jour (« mars 2024 »), niveaux décrits en
toutes lettres hors du vocabulaire listé.

## Détection des doublons

Logique entièrement écrite à la main (numpy/scipy), sans bibliothèque de dédoublonnage.

1. **Copies exactes** : empreinte SHA-1 des pixels décodés de chaque page. Deux fichiers identiques (même un PDF
   multipage) sont donc appariés page à page.
2. **Préparation de chaque page** (`tri/image.py`) :
   - fond = médiane des gris ;
   - retrait des bandes noires de scanner collées aux bords ;
   - seuil d'encre adaptatif `fond − 0,5 × (fond − niveau sombre)`, le niveau sombre étant mesuré au centre de la
     page pour ne pas être faussé par les bandes ;
   - retrait des traits fins et longs qui touchent le bord (bande de scanner inclinée) ;
   - densité d'encre à 500 px ;
   - redressement : angle de −6° à +6° qui maximise l'énergie des projections horizontale et verticale (recherche
     grossière puis fine au 1/10 de degré, calculée sur les coordonnées des pixels d'encre, donc rapide) ;
   - recadrage sur le contenu, en ignorant les petites taches de bruit.

   Le recadrage absorbe le décalage et le changement d'échelle. Le redressement absorbe la légère rotation.
3. **Signature** : la densité recadrée en 256 px (flou gaussien σ = 1,5), sous ses 4 quarts de tour, plus une vignette
   32×32 normalisée.
4. **Comparaison** d'une paire, pour chacun des 4 quarts de tour :
   - filtre sur les proportions du cadre (écart log ≤ 0,2) et sur la corrélation des vignettes (≥ 0,5) ;
   - puis corrélation fine après recalage par corrélation croisée FFT (±6 px).

   On garde le maximum sur les rotations. La paire est doublon si ce score est ≥ **0,76**.
5. **Regroupement** par union-find (transitivité), groupes triés.

**Choix des seuils, mesurés et non devinés :**
- Sur le dossier d'exemple, les 20 paires de doublons attendues ont un score entre 0,894 et 1 (copies exactes). La paire différente
  la plus ressemblante (même gabarit Futurmap) est à 0,687. Le seuil de 0,76 est placé dans cet écart.
- Pour ne pas régler le seuil sur l'exemple seul, `evaluation/evaluer_doublons.py` simule un rescan de chacune des
  200 pages d'entraînement. Le rescan combine :
  - rotation de ±3°, échelle de 0,8 à 1,2, décalage ;
  - fond de 200 à 255, contraste divisé jusqu'à 2, bruit et taches ;
  - bande de scanner, flou, quart de tour aléatoire, JPEG de qualité 30 à 90.

  Chaque rescan est comparé à toutes les autres pages, soit 59 700 paires différentes, souvent du même gabarit.

| Seuil | Rappel | Faux doublons | F1 |
|---|---|---|---|
| 0,72 | 0,925 | 8 | 0,941 |
| 0,74 | 0,925 | 5 | 0,949 |
| **0,76** | **0,920** | **2** | **0,953** |
| 0,78 | 0,890 | 0 | 0,942 |
| 0,80 | 0,870 | 0 | 0,930 |

Le flou σ = 1,5 a été retenu face à σ = 1,0 et σ = 2,0 (F1 maximal respectifs 0,951 et 0,950), et la fraction de seuil
d'encre 0,5 face à 0,4 et 0,6 (rappel 0,86 et 0,80).

Limites : les rescans manqués en simulation sont des cas extrêmes, cumulant contraste divisé par deux, JPEG de qualité
30 et une page déjà grise. Les traits fins y disparaissent et il ne reste que les murs épais. Une page coupée par le
cadrage du scan (contenu hors champ) déplace le recadrage et peut faire baisser le score. La comparaison est en O(n²)
paires, ce qui reste rapide pour quelques centaines de pages (environ 3 s pour 112 pages).

## Classification des pages

- **Données** : les 200 pages de `entrainement/` (40 par classe). Chaque page est ajoutée sous ses 4 quarts de tour,
  car certaines pages arrivent tournées, ce qui donne 800 exemples.
- **Caractéristiques** (58 valeurs, `tri/caracteristiques.py`), calculées sur la page préparée comme pour les doublons :
  - histogrammes des longueurs de plages d'encre horizontales et verticales (traits longs de tableaux et de murs,
    plages courtes de texte) ;
  - nombre de lignes longues ;
  - taux de lignes et colonnes encrées, périodicité du profil (lignes de texte) ;
  - histogramme des orientations du gradient (diagonales des plans de situation) ;
  - statistiques des composantes connexes (caractères, pièces) ;
  - épaisseur des traits par érosions successives (murs épais des plans) ;
  - répartition de l'encre sur une grille 3×3.

  Les paires horizontal/vertical sont combinées en somme et écart absolu, ce qui rend la plupart des valeurs
  invariantes au quart de tour.
- **Modèle** : ExtraTrees (300 arbres) de scikit-learn, exporté en tableaux numpy (`model/foret.npz`, 265 Ko).
  L'export est vérifié identique à `predict_proba`, avec un écart maximal de 0. Ce choix est meilleur qu'une régression
  logistique : en test indépendant sur l'exemple, celle-ci confondait un texte avec un tableau.
- **Mesure des résultats** (`model/metriques.json`) :
  - validation croisée stratifiée en 5 plis sur `entrainement/`, groupée par page d'origine pour qu'une page et ses
    rotations ne soient jamais à la fois en apprentissage et en test : **macro-F1 = 1,000** ;
  - test indépendant sur les 112 pages du dossier d'exemple, avec un modèle entraîné **uniquement** sur
    `entrainement/` : **macro-F1 = 1,000**, et toujours 1,000 sur ces mêmes pages tournées de 90°.

  Le modèle livré est ensuite ré-entraîné sur entraînement + exemple. Le 25/25 du vérificateur n'est donc plus une
  mesure indépendante : la mesure honnête est le test ci-dessus.
- Temps : environ 0,1 s par page pour la préparation et les caractéristiques.

## Tests

```
python -m unittest discover -s tests -v
```

46 tests (environ 22 s) :
- `test_normalisation.py` : toutes les formes citées dans le sujet pour bâtiment, niveau et date, plus les valeurs
  vides, inconnues, ambiguës ou impossibles.
- `test_bordereau.py` : Windows-1252 et UTF-8, colonnes dans un autre ordre, lignes courtes, lignes en double,
  correspondance insensible à la casse, manquants.
- `test_inventaire.py` : dossier synthétique avec PDF multipage, zip avec sous-dossier, fichiers système, et
  illisibles (vide, texte en `.png`, PDF cassé, PNG nommé `.jpg`, JPEG tronqué, zip corrompu, extension inconnue).
- `test_doublons.py` : un rescan tourné de 0, 90, 180 et 270° est retrouvé, des pages différentes du même gabarit ne
  le sont pas, page blanche, regroupement transitif, copies exactes.
- `test_classification.py` : vecteur de taille fixe et fini sur des pages extrêmes, export numpy identique à
  scikit-learn, chargement du modèle livré.
- `test_trier.py` : exécution complète de `trier.py` en sous-processus (format exact du JSON, valeurs, illisibles,
  manquants, doublons), entrées dégradées (mauvais arguments, bordereau absent, référentiel mal formé), et note
  minimale sur le dossier d'exemple du kit s'il est présent à côté du rendu.

## Limites connues et pistes d'amélioration

- Si deux fichiers de dossiers différents portent le même nom, ils reçoivent la même ligne de bordereau (le bordereau
  ne donne pas le chemin).
- Le seuil de doublon est global. Un seuil par classe (les textes et tableaux d'un même gabarit sont plus proches entre
  eux) pourrait améliorer encore la précision.
- Pour les pages cadrées différemment (contenu coupé), une mise en correspondance de points d'intérêt avec estimation
  d'une transformation (RANSAC) serait plus robuste que le recadrage sur le contenu.
- Les 200 pages d'entraînement sont propres et très séparables. Sur des documents réels plus variés, un petit réseau
  convolutif exporté en ONNX serait à évaluer.
- Un PDF dont une seule page ne se rend pas est marqué illisible en entier.
