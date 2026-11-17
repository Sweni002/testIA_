"""Tri d'un dossier client — à compléter.
Usage : python trier.py <dossier_client> <bordereau.csv> <referentiel.json> <sortie.json>
"""
import json
import sys


def main(dossier: str, bordereau: str, referentiel: str, sortie: str) -> None:
    resultat = {"fichiers": [], "doublons": [], "manquants": []}
    # TODO : inventaire, lecture des pages, normalisation, doublons, classification
    json.dump(resultat, open(sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:5])
