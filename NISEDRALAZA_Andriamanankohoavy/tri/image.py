import numpy as np
from PIL import Image
from scipy import ndimage

COTE_TRAVAIL = 500
SEUIL_BANDE = 0.8
FRACTION_ENCRE = 0.5
ANGLE_MAX = 12


def redimensionner(tableau: np.ndarray, forme: tuple) -> np.ndarray:
    image = Image.fromarray(tableau.astype(np.float32), "F")
    return np.asarray(image.resize((forme[1], forme[0]), Image.Resampling.BOX))


def retirer_bandes(gris: np.ndarray, fond: float) -> np.ndarray:
    sombre = gris < fond * 0.6
    hauteur, largeur = sombre.shape
    lignes, colonnes = sombre.mean(1), sombre.mean(0)
    haut, bas, gauche, droite = 0, hauteur, 0, largeur
    while haut < hauteur // 10 and lignes[haut] > SEUIL_BANDE:
        haut += 1
    while bas > hauteur - hauteur // 10 and lignes[bas - 1] > SEUIL_BANDE:
        bas -= 1
    while gauche < largeur // 10 and colonnes[gauche] > SEUIL_BANDE:
        gauche += 1
    while droite > largeur - largeur // 10 and colonnes[droite - 1] > SEUIL_BANDE:
        droite -= 1
    return gris[haut:bas, gauche:droite]


def retirer_traits_de_bord(encre: np.ndarray) -> np.ndarray:
    etiquettes, nombre = ndimage.label(encre)
    if nombre == 0:
        return encre
    hauteur, largeur = encre.shape
    for indice, zone in enumerate(ndimage.find_objects(etiquettes), 1):
        haut, bas = zone[0].start, zone[0].stop
        gauche, droite = zone[1].start, zone[1].stop
        touche_bord = haut <= 2 or gauche <= 2 or bas >= hauteur - 2 or droite >= largeur - 2
        horizontal = droite - gauche >= 0.5 * largeur and bas - haut <= 0.08 * hauteur
        vertical = bas - haut >= 0.5 * hauteur and droite - gauche <= 0.08 * largeur
        if touche_bord and (horizontal or vertical):
            encre[zone][etiquettes[zone] == indice] = False
    return encre


def niveau_sombre(gris: np.ndarray) -> float:
    hauteur, largeur = gris.shape
    centre = gris[hauteur // 20:hauteur - hauteur // 20, largeur // 20:largeur - largeur // 20]
    return float(np.percentile(centre if centre.size else gris, 0.3))


def masque_encre(page: np.ndarray) -> np.ndarray:
    gris = page.astype(np.float32) / 255
    fond = float(np.median(gris))
    gris = retirer_bandes(gris, fond)
    if gris.size == 0:
        return np.zeros((1, 1), np.float32)
    seuil = fond - FRACTION_ENCRE * (fond - niveau_sombre(gris))
    return retirer_traits_de_bord(gris < seuil).astype(np.float32)


def angle_inclinaison(densite: np.ndarray) -> float:
    ys, xs = np.nonzero(densite > 0.3)
    if len(ys) < 10:
        return 0.0
    poids = densite[ys, xs]

    def energie(angle: float) -> float:
        t = np.deg2rad(angle)
        yr = ys * np.cos(t) - xs * np.sin(t)
        xr = xs * np.cos(t) + ys * np.sin(t)
        hy = np.bincount((yr - yr.min()).astype(int), poids)
        hx = np.bincount((xr - xr.min()).astype(int), poids)
        return float((hy ** 2).sum() + (hx ** 2).sum())

    meilleur = max(np.arange(-ANGLE_MAX, ANGLE_MAX + 0.01, 0.5), key=energie)
    return float(max(np.arange(meilleur - 0.5, meilleur + 0.51, 0.1), key=energie))


def recadrer_contenu(densite: np.ndarray) -> np.ndarray:
    etiquettes, nombre = ndimage.label(densite > 0.15, np.ones((3, 3)))
    if nombre == 0:
        return densite
    tailles = ndimage.sum(densite, etiquettes, range(1, nombre + 1))
    garde = np.isin(etiquettes, 1 + np.nonzero(tailles >= 3)[0])
    ys, xs = np.nonzero(garde)
    if len(ys) == 0:
        return densite
    return densite[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def preparer(page: np.ndarray) -> np.ndarray:
    encre = masque_encre(page)
    hauteur, largeur = encre.shape
    facteur = COTE_TRAVAIL / max(hauteur, largeur)
    forme = (max(1, round(hauteur * facteur)), max(1, round(largeur * facteur)))
    densite = redimensionner(encre, forme)
    angle = angle_inclinaison(densite)
    if abs(angle) > 0.05:
        densite = ndimage.rotate(densite, angle, reshape=True, order=1)
    return recadrer_contenu(densite)
