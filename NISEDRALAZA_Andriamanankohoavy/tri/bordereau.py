import csv
import io
import json
import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath

from tri.normalisation import (NIVEAUX_PAR_DEFAUT, ReferentielBatiments, normaliser_date,
                               normaliser_niveau, simplifier)

COLONNES = {
    "fichier": ("fichier", "nom"),
    "batiment": ("batiment", "bat"),
    "niveau": ("niveau", "etage"),
    "date": ("date",),
}
POSITIONS_PAR_DEFAUT = {"fichier": 0, "batiment": 1, "niveau": 2, "date": 3}


@dataclass
class LigneBordereau:
    nom: str
    batiment: str = ""
    niveau: str = ""
    date: str = ""


@dataclass
class Referentiel:
    batiments: ReferentielBatiments
    niveaux: list


def cle_fichier(nom: str) -> str:
    base = PurePosixPath(nom.strip().replace("\\", "/")).name
    return unicodedata.normalize("NFC", base).casefold()


def decoder(donnees: bytes) -> str:
    try:
        return donnees.decode("utf-8-sig")
    except UnicodeDecodeError:
        return donnees.decode("cp1252", errors="replace")


def choisir_separateur(premiere_ligne: str) -> str:
    for separateur in (";", "\t", ","):
        if separateur in premiere_ligne:
            return separateur
    return ";"


def reperer_colonnes(entete: list) -> dict | None:
    simples = [simplifier(cellule) for cellule in entete]
    positions = {}
    for champ, mots in COLONNES.items():
        for index, cellule in enumerate(simples):
            if index not in positions.values() and any(mot in cellule.split() for mot in mots):
                positions[champ] = index
                break
    return positions if "fichier" in positions else None


def lire_lignes(texte: str) -> list:
    premiere = texte.splitlines()[0] if texte.strip() else ""
    lecteur = csv.reader(io.StringIO(texte), delimiter=choisir_separateur(premiere))
    lignes = [ligne for ligne in lecteur if any(cellule.strip() for cellule in ligne)]
    if not lignes:
        return []
    positions = reperer_colonnes(lignes[0])
    if positions is None:
        positions = POSITIONS_PAR_DEFAUT
    else:
        lignes = lignes[1:]
        positions = {**{c: None for c in POSITIONS_PAR_DEFAUT}, **positions}
    resultat = []
    for ligne in lignes:
        valeurs = [valeur_cellule(ligne, positions.get(champ)) for champ in ("fichier", "batiment", "niveau", "date")]
        if valeurs[0]:
            resultat.append(LigneBordereau(*valeurs))
    return resultat


def valeur_cellule(ligne: list, index: int | None) -> str:
    return ligne[index].strip() if index is not None and index < len(ligne) else ""


def lire_bordereau(chemin: str) -> list:
    with open(chemin, "rb") as flux:
        return lire_lignes(decoder(flux.read()))


def indexer(lignes: list) -> dict:
    index = {}
    for ligne in lignes:
        cle = cle_fichier(ligne.nom)
        existante = index.get(cle)
        if existante is None:
            index[cle] = LigneBordereau(ligne.nom, ligne.batiment, ligne.niveau, ligne.date)
            continue
        existante.batiment = existante.batiment or ligne.batiment
        existante.niveau = existante.niveau or ligne.niveau
        existante.date = existante.date or ligne.date
    return index


def charger_referentiel(chemin: str) -> Referentiel:
    with open(chemin, "rb") as flux:
        contenu = json.loads(decoder(flux.read()))
    niveaux = [str(n) for n in contenu.get("niveaux") or []] or list(NIVEAUX_PAR_DEFAUT)
    return Referentiel(ReferentielBatiments(contenu.get("batiments") or []), niveaux)


def referentiel_vide() -> Referentiel:
    return Referentiel(ReferentielBatiments([]), list(NIVEAUX_PAR_DEFAUT))


def normaliser_ligne(ligne: LigneBordereau | None, referentiel: Referentiel) -> dict:
    if ligne is None:
        return {"batiment": None, "niveau": None, "date": None}
    return {
        "batiment": referentiel.batiments.normaliser(ligne.batiment),
        "niveau": normaliser_niveau(ligne.niveau, referentiel.niveaux),
        "date": normaliser_date(ligne.date),
    }


def manquants(lignes: list, noms_presents: set) -> list:
    vus, resultat = set(), []
    for ligne in lignes:
        cle = cle_fichier(ligne.nom)
        if cle not in noms_presents and cle not in vus:
            vus.add(cle)
            resultat.append(ligne.nom)
    return resultat
