import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from tri.caracteristiques import extraire
from tri.classification import CHEMIN_MODELE, CLASSES, ForetExportee
from tri.image import preparer
from tri.inventaire import inventorier, lire_image

NB_ARBRES = 300
GRAINE = 0


def charger_entrainement(dossier: Path) -> list:
    with open(dossier / "etiquettes.csv", encoding="utf-8") as flux:
        lignes = list(csv.reader(flux, delimiter=";"))[1:]
    pages = []
    for nom, classe in lignes:
        page = lire_image((dossier / nom).read_bytes())[0]
        pages.append((f"entrainement/{nom}", page, classe))
    return pages


def charger_exemple(dossier: Path) -> list:
    with open(dossier / "attendu.json", encoding="utf-8") as flux:
        etiquettes = json.load(flux)["pages"]
    pages = []
    for document in inventorier(str(dossier / "dossier_client")):
        for numero, page in enumerate(document.pages, 1):
            identifiant = f"{document.chemin}#{numero}"
            if identifiant in etiquettes:
                pages.append((f"exemple/{identifiant}", page, etiquettes[identifiant]))
    return pages


def caracteristiques(pages: list, rotations=(0, 1, 2, 3)):
    x, y, groupes = [], [], []
    for indice, (_, page, classe) in enumerate(pages):
        for rotation in rotations:
            x.append(extraire(preparer(np.rot90(page, rotation).copy())))
            y.append(classe)
            groupes.append(indice)
    return np.array(x), np.array(y), np.array(groupes)


def nouveau_modele() -> ExtraTreesClassifier:
    return ExtraTreesClassifier(n_estimators=NB_ARBRES, random_state=GRAINE, n_jobs=-1)


def mesurer(nom: str, vrai, predit) -> dict:
    score = f1_score(vrai, predit, labels=CLASSES, average="macro")
    print(f"\n=== {nom} : macro-F1 = {score:.3f}")
    print(classification_report(vrai, predit, labels=CLASSES, digits=3, zero_division=0))
    print("Matrice de confusion (lignes = vérité, colonnes = prédiction) :", CLASSES)
    matrice = confusion_matrix(vrai, predit, labels=CLASSES)
    print(matrice)
    return {"macro_f1": round(float(score), 4), "confusion": matrice.tolist()}


def validation_croisee(x, y, groupes) -> dict:
    predit = np.empty(len(y), dtype=object)
    for apprentissage, test in StratifiedGroupKFold(5, shuffle=True, random_state=GRAINE).split(x, y, groupes):
        modele = nouveau_modele().fit(x[apprentissage], y[apprentissage])
        predit[test] = modele.predict(x[test])
    return mesurer("Validation croisée 5 plis sur entrainement/ (groupes = page d'origine)", y, predit)


def main() -> None:
    analyseur = argparse.ArgumentParser(description="Entraîne le classifieur de pages.")
    analyseur.add_argument("--entrainement", required=True, type=Path)
    analyseur.add_argument("--exemple", type=Path)
    analyseur.add_argument("--sortie", type=Path, default=CHEMIN_MODELE)
    arguments = analyseur.parse_args()

    metriques = {}
    pages_entrainement = charger_entrainement(arguments.entrainement)
    x, y, groupes = caracteristiques(pages_entrainement)
    print(f"{len(pages_entrainement)} pages d'entraînement, {len(y)} exemples après rotations")
    metriques["validation_croisee"] = validation_croisee(x, y, groupes)

    if arguments.exemple:
        pages_exemple = charger_exemple(arguments.exemple)
        modele = ForetExportee.depuis_sklearn(nouveau_modele().fit(x, y))
        for rotation in (0, 1):
            xe, ye, _ = caracteristiques(pages_exemple, rotations=(rotation,))
            nom = f"Test sur dossier_exemple ({len(ye)} pages, rotation {90 * rotation}°)"
            metriques[f"exemple_rotation_{90 * rotation}"] = mesurer(nom, ye, modele.predire(xe))
        xe, ye, _ = caracteristiques(pages_exemple)
        x = np.vstack([x, xe])
        y = np.concatenate([y, ye])

    foret = nouveau_modele().fit(x, y)
    exportee = ForetExportee.depuis_sklearn(foret)
    ecart = np.abs(exportee.probabilites(x) - foret.predict_proba(x)).max()
    print(f"\nÉcart maximal entre sklearn et le modèle exporté : {ecart:.2e}")
    if ecart > 1e-5:
        raise SystemExit("Export incohérent avec le modèle sklearn")
    arguments.sortie.parent.mkdir(parents=True, exist_ok=True)
    exportee.sauvegarder(arguments.sortie)
    metriques["exemples_modele_final"] = int(len(y))
    with open(arguments.sortie.with_name("metriques.json"), "w", encoding="utf-8") as flux:
        json.dump(metriques, flux, ensure_ascii=False, indent=1)
    print(f"Modèle enregistré dans {arguments.sortie}")


if __name__ == "__main__":
    main()
