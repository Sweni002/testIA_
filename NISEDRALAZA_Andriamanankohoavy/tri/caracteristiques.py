import numpy as np
from scipy import ndimage

BORNES_PLAGES = np.array([1, 2, 3, 5, 9, 17, 33, 65, 129, 100000])
SEUIL_BINAIRE = 0.25


def plages(binaire: np.ndarray) -> tuple:
    bord = np.zeros((binaire.shape[0], 1), dtype=np.int8)
    diff = np.diff(np.hstack([bord, binaire.astype(np.int8), bord]), axis=1)
    lignes, debuts = np.nonzero(diff == 1)
    _, fins = np.nonzero(diff == -1)
    return lignes, fins - debuts


def histogramme_plages(binaire: np.ndarray) -> np.ndarray:
    _, longueurs = plages(binaire)
    if len(longueurs) == 0:
        return np.zeros(len(BORNES_PLAGES) - 1)
    hist, _ = np.histogram(longueurs, bins=BORNES_PLAGES, weights=longueurs)
    return hist / max(longueurs.sum(), 1)


def symetriques(a: np.ndarray, b: np.ndarray) -> list:
    a, b = np.asarray(a, float), np.asarray(b, float)
    return list(a + b) + list(np.abs(a - b))


def lignes_longues(binaire: np.ndarray) -> np.ndarray:
    lignes, longueurs = plages(binaire)
    plus_longue = np.zeros(binaire.shape[0])
    np.maximum.at(plus_longue, lignes, longueurs)
    largeur = binaire.shape[1]
    return np.array([min(ndimage.label(plus_longue >= fraction * largeur)[1], 60) / 60
                     for fraction in (0.25, 0.5, 0.8)])


def periodicite(profil: np.ndarray) -> float:
    profil = profil - profil.mean()
    energie = float((profil ** 2).sum())
    if energie <= 0 or len(profil) < 60:
        return 0.0
    auto = np.correlate(profil, profil, mode="full")[len(profil) - 1:] / energie
    return float(auto[4:40].max())


def orientations(densite: np.ndarray) -> np.ndarray:
    lisse = ndimage.gaussian_filter(densite, 1.0)
    gx = ndimage.sobel(lisse, axis=1)
    gy = ndimage.sobel(lisse, axis=0)
    magnitude = np.hypot(gx, gy)
    angle = np.mod(np.arctan2(gy, gx), np.pi / 2)
    hist, _ = np.histogram(angle, bins=6, range=(0, np.pi / 2), weights=magnitude)
    return hist / max(hist.sum(), 1e-9)


def composantes(binaire: np.ndarray) -> list:
    etiquettes, nombre = ndimage.label(binaire, np.ones((3, 3)))
    surface = binaire.size
    if nombre == 0:
        return [0.0] * 7
    tailles = np.bincount(etiquettes.ravel())[1:]
    objets = ndimage.find_objects(etiquettes)
    hauteurs = np.array([s[0].stop - s[0].start for s in objets])
    largeurs = np.array([s[1].stop - s[1].start for s in objets])
    remplissage = tailles / np.maximum(hauteurs * largeurs, 1)
    return [
        min(nombre / surface * 1000, 20),
        float((tailles < 10).mean()),
        float(((tailles >= 10) & (tailles < 80)).mean()),
        float(tailles.max() / max(tailles.sum(), 1)),
        float(np.log1p(np.median(tailles))),
        float(np.median(remplissage)),
        float(np.average(remplissage, weights=tailles)),
    ]


def epaisseur(binaire: np.ndarray) -> list:
    total = max(binaire.sum(), 1)
    resultats = []
    erode = binaire
    for _ in range(3):
        erode = ndimage.binary_erosion(erode)
        resultats.append(erode.sum() / total)
    return resultats


def grille(densite: np.ndarray, n: int = 3) -> list:
    hauteur, largeur = densite.shape
    cases = []
    for i in range(n):
        for j in range(n):
            bloc = densite[i * hauteur // n:(i + 1) * hauteur // n, j * largeur // n:(j + 1) * largeur // n]
            cases.append(float(bloc.mean()) if bloc.size else 0.0)
    cases = np.array(cases)
    return list(np.sort(cases) / max(cases.max(), 1e-9)) + [float(cases.std() / max(cases.mean(), 1e-9))]


def extraire(densite: np.ndarray) -> np.ndarray:
    binaire = densite > SEUIL_BINAIRE
    hauteur, largeur = binaire.shape
    lignes, colonnes = binaire.mean(1), binaire.mean(0)
    valeurs = [min(hauteur, largeur) / max(hauteur, largeur, 1), float(binaire.mean())]
    valeurs += symetriques(histogramme_plages(binaire), histogramme_plages(binaire.T))
    valeurs += symetriques(lignes_longues(binaire), lignes_longues(binaire.T))
    valeurs += symetriques([(lignes > 0.01).mean(), lignes.std(), periodicite(lignes)],
                           [(colonnes > 0.01).mean(), colonnes.std(), periodicite(colonnes)])
    valeurs += list(orientations(densite))
    valeurs += composantes(binaire)
    valeurs += epaisseur(binaire)
    valeurs += grille(densite)
    return np.nan_to_num(np.array(valeurs, dtype=np.float64))
