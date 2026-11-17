import hashlib
import sys

import numpy as np

from tri import bordereau as brd
from tri.caracteristiques import extraire
from tri.classification import CHEMIN_MODELE, CLASSES, ForetExportee
from tri.doublons import calculer_signature, regrouper
from tri.image import preparer
from tri.inventaire import inventorier

CLASSE_PAR_DEFAUT = CLASSES[0]


def avertir(message: str) -> None:
    print(f"[avertissement] {message}", file=sys.stderr)


def charger_lignes(chemin: str) -> list:
    try:
        return brd.lire_bordereau(chemin)
    except (OSError, ValueError) as erreur:
        avertir(f"bordereau illisible ({erreur}) : aucune information de bordereau")
        return []


def charger_referentiel(chemin: str) -> brd.Referentiel:
    try:
        return brd.charger_referentiel(chemin)
    except (OSError, ValueError, AttributeError, TypeError) as erreur:
        avertir(f"référentiel illisible ({erreur}) : bâtiments non normalisés")
        return brd.referentiel_vide()


def charger_modele(chemin) -> ForetExportee | None:
    try:
        return ForetExportee.charger(chemin)
    except (OSError, ValueError, KeyError) as erreur:
        avertir(f"modèle introuvable ou invalide ({erreur}) : classe par défaut utilisée")
        return None


def analyser_page(page: np.ndarray):
    empreinte = hashlib.sha1(page.tobytes() + str(page.shape).encode()).hexdigest()
    try:
        densite = preparer(page)
        return empreinte, calculer_signature(densite), extraire(densite)
    except Exception as erreur:
        avertir(f"analyse d'une page impossible ({erreur})")
        return empreinte, None, None


def classer(modele: ForetExportee | None, caracteristiques: list) -> list:
    classes = [CLASSE_PAR_DEFAUT] * len(caracteristiques)
    valides = [i for i, c in enumerate(caracteristiques) if c is not None]
    if modele is None or not valides:
        return classes
    try:
        predites = modele.predire(np.vstack([caracteristiques[i] for i in valides]))
    except Exception as erreur:
        avertir(f"classification impossible ({erreur}) : classe par défaut utilisée")
        return classes
    for index, classe in zip(valides, predites):
        classes[index] = classe
    return classes


def trier(dossier: str, bordereau: str, referentiel: str, chemin_modele=CHEMIN_MODELE) -> dict:
    documents = inventorier(dossier)
    lignes = charger_lignes(bordereau)
    index = brd.indexer(lignes)
    ref = charger_referentiel(referentiel)
    modele = charger_modele(chemin_modele)

    identifiants, empreintes, signatures, caracteristiques = [], [], [], []
    for document in documents:
        for numero, page in enumerate(document.pages, 1):
            empreinte, signature, valeurs = analyser_page(page)
            identifiants.append(f"{document.chemin}#{numero}")
            empreintes.append(empreinte)
            signatures.append(signature)
            caracteristiques.append(valeurs)
        document.liberer_pages()

    classes = classer(modele, caracteristiques)
    classes_par_page = dict(zip(identifiants, classes))

    fichiers = []
    for document in documents:
        champs = brd.normaliser_ligne(index.get(brd.cle_fichier(document.nom)) if document.lisible else None, ref)
        fichiers.append({
            "chemin": document.chemin,
            "statut": document.statut,
            "pages": document.nombre_pages,
            **champs,
            "classes": [classes_par_page[f"{document.chemin}#{n}"] for n in range(1, document.nombre_pages + 1)],
        })

    noms_presents = {brd.cle_fichier(document.nom) for document in documents}
    return {
        "fichiers": fichiers,
        "doublons": regrouper(identifiants, signatures, empreintes),
        "manquants": brd.manquants(lignes, noms_presents),
    }
