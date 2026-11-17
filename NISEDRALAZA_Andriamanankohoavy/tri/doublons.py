from dataclasses import dataclass
from itertools import combinations

import numpy as np
from scipy import ndimage

from tri.image import redimensionner

COTE_FIN = 256
COTE_GROSSIER = 32
SEUIL_GROSSIER = 0.5
SEUIL_DOUBLON = 0.76
ECART_PROPORTIONS = 0.2
DECALAGE_MAX = 6


@dataclass
class Signature:
    fines: list
    grossieres: list


def centrer_reduire(tableau: np.ndarray) -> np.ndarray:
    centre = tableau - tableau.mean()
    return centre / (np.linalg.norm(centre) + 1e-9)


def calculer_signature(densite: np.ndarray) -> Signature:
    hauteur, largeur = densite.shape
    facteur = COTE_FIN / max(hauteur, largeur)
    forme = (max(8, round(hauteur * facteur)), max(8, round(largeur * facteur)))
    fine = ndimage.gaussian_filter(redimensionner(densite, forme), 1.5)
    grossiere = ndimage.gaussian_filter(redimensionner(densite, (COTE_GROSSIER, COTE_GROSSIER)), 1.0)
    return Signature(
        [np.rot90(fine, k).copy() for k in range(4)],
        [centrer_reduire(np.rot90(grossiere, k)).ravel() for k in range(4)],
    )


def correlation_alignee(a: np.ndarray, b: np.ndarray) -> float:
    b = redimensionner(b, a.shape)
    a0, b0 = a - a.mean(), b - b.mean()
    croisee = np.fft.irfft2(np.fft.rfft2(a0) * np.conj(np.fft.rfft2(b0)), s=a.shape)
    fenetre = np.roll(croisee, (DECALAGE_MAX, DECALAGE_MAX), axis=(0, 1))[:2 * DECALAGE_MAX + 1, :2 * DECALAGE_MAX + 1]
    dy, dx = np.unravel_index(int(np.argmax(fenetre)), fenetre.shape)
    decale = np.roll(b0, (dy - DECALAGE_MAX, dx - DECALAGE_MAX), axis=(0, 1))
    return float((centrer_reduire(a0) * centrer_reduire(decale)).sum())


def proportions_compatibles(a: np.ndarray, b: np.ndarray) -> bool:
    rapport_a = a.shape[1] / a.shape[0]
    rapport_b = b.shape[1] / b.shape[0]
    return abs(np.log(rapport_a / rapport_b)) <= ECART_PROPORTIONS


def similarite(a: Signature, b: Signature) -> float:
    meilleure = -1.0
    reference = b.fines[0]
    for rotation in range(4):
        candidate = a.fines[rotation]
        if not proportions_compatibles(candidate, reference):
            continue
        if float(a.grossieres[rotation] @ b.grossieres[0]) < SEUIL_GROSSIER:
            continue
        meilleure = max(meilleure, correlation_alignee(candidate, reference))
    return meilleure


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def trouver(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def unir(self, i: int, j: int) -> None:
        self.parent[self.trouver(i)] = self.trouver(j)


def paires_exactes(empreintes: list) -> list:
    par_empreinte = {}
    for index, empreinte in enumerate(empreintes):
        if empreinte is not None:
            par_empreinte.setdefault(empreinte, []).append(index)
    return [(i, j) for indices in par_empreinte.values() for i, j in combinations(indices, 2)]


def regrouper(identifiants: list, signatures: list, empreintes: list) -> list:
    union = UnionFind(len(identifiants))
    for i, j in paires_exactes(empreintes):
        union.unir(i, j)
    for i, j in combinations(range(len(identifiants)), 2):
        if signatures[i] is None or signatures[j] is None or union.trouver(i) == union.trouver(j):
            continue
        if similarite(signatures[i], signatures[j]) >= SEUIL_DOUBLON:
            union.unir(i, j)
    groupes = {}
    for index, identifiant in enumerate(identifiants):
        groupes.setdefault(union.trouver(index), []).append(identifiant)
    return sorted(sorted(g) for g in groupes.values() if len(g) > 1)
