import argparse
import io
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tri.doublons import SEUIL_DOUBLON, calculer_signature, similarite
from tri.image import preparer, retirer_bandes
from tri.inventaire import reduire


def nettoyer(page: np.ndarray) -> np.ndarray:
    gris = page.astype(np.float32) / 255
    return (retirer_bandes(gris, float(np.median(gris))) * 255).astype(np.uint8)


def rescanner(page: np.ndarray, generateur: np.random.Generator) -> np.ndarray:
    image = Image.fromarray(page)
    fond = int(generateur.integers(200, 256))
    angle = float(generateur.uniform(-3, 3))
    image = image.rotate(angle, resample=Image.Resampling.BILINEAR, expand=True, fillcolor=fond)
    echelle = float(generateur.uniform(0.8, 1.2))
    image = image.resize((max(1, int(image.width * echelle)), max(1, int(image.height * echelle))),
                         Image.Resampling.BILINEAR)
    marge = int(generateur.integers(0, 40))
    toile = Image.new("L", (image.width + 2 * marge, image.height + 2 * marge), fond)
    toile.paste(image, (int(generateur.integers(0, 2 * marge + 1)), int(generateur.integers(0, 2 * marge + 1))))
    tableau = np.asarray(toile, dtype=np.float32)
    contraste = float(generateur.uniform(0.5, 1.0))
    tableau = 255 - (255 - tableau) * contraste
    tableau += generateur.normal(0, 6, tableau.shape)
    points = generateur.random(tableau.shape) < 0.002
    tableau[points] = generateur.uniform(60, 160)
    if generateur.random() < 0.5:
        epaisseur = int(generateur.integers(5, 15))
        cote = int(generateur.integers(0, 4))
        if cote == 0:
            tableau[:, -epaisseur:] = 10
        elif cote == 1:
            tableau[-epaisseur:, :] = 10
        elif cote == 2:
            tableau[:, :epaisseur] = 10
        else:
            tableau[:epaisseur, :] = 10
    image = Image.fromarray(np.clip(tableau, 0, 255).astype(np.uint8))
    if generateur.random() < 0.3:
        image = image.filter(ImageFilter.GaussianBlur(0.8))
    image = image.rotate(90 * int(generateur.integers(0, 4)), expand=True)
    flux = io.BytesIO()
    image.save(flux, format="JPEG", quality=int(generateur.integers(30, 90)))
    return reduire(Image.open(io.BytesIO(flux.getvalue())))


def main() -> None:
    analyseur = argparse.ArgumentParser(description="Mesure la détection de doublons sur des rescans simulés.")
    analyseur.add_argument("--entrainement", required=True, type=Path)
    analyseur.add_argument("--nombre", type=int, default=200)
    arguments = analyseur.parse_args()

    generateur = np.random.default_rng(0)
    fichiers = sorted(arguments.entrainement.glob("*.jpg"))[:arguments.nombre]
    originaux = [nettoyer(np.asarray(Image.open(f).convert("L"))) for f in fichiers]
    sig_originaux = [calculer_signature(preparer(p)) for p in originaux]
    sig_rescans = [calculer_signature(preparer(rescanner(p, generateur))) for p in originaux]

    positifs = np.array([similarite(a, b) for a, b in zip(sig_rescans, sig_originaux)])
    negatifs = np.array([similarite(sig_originaux[i], sig_originaux[j])
                         for i, j in combinations(range(len(originaux)), 2)])
    rescans_croises = np.array([similarite(sig_rescans[i], sig_originaux[j])
                                for i in range(len(originaux)) for j in range(len(originaux)) if i != j])
    vrais = int((positifs >= SEUIL_DOUBLON).sum())
    faux = int((negatifs >= SEUIL_DOUBLON).sum() + (rescans_croises >= SEUIL_DOUBLON).sum())
    precision = vrais / max(vrais + faux, 1)
    rappel = vrais / len(positifs)
    print(f"Seuil {SEUIL_DOUBLON}")
    print(f"Rescans retrouvés : {vrais}/{len(positifs)} (rappel {rappel:.3f})")
    print(f"Faux doublons : {faux} sur {len(negatifs) + len(rescans_croises)} paires différentes")
    print(f"Précision {precision:.3f}, F1 {2 * precision * rappel / max(precision + rappel, 1e-9):.3f}")
    print("Similarité des vrais doublons, centiles 1/5/50 :", np.round(np.percentile(positifs, [1, 5, 50]), 3))
    print("Similarité des pages différentes, max / centile 99.9 :",
          round(float(max(negatifs.max(), rescans_croises.max())), 3),
          np.round(np.percentile(np.concatenate([negatifs, rescans_croises]), 99.9), 3))
    differentes = np.concatenate([negatifs, rescans_croises])
    print("Seuil   rappel  faux  F1")
    for seuil in np.arange(0.66, 0.90, 0.02):
        tp = int((positifs >= seuil).sum())
        fp = int((differentes >= seuil).sum())
        p, r = tp / max(tp + fp, 1), tp / len(positifs)
        print(f"{seuil:.2f}    {r:.3f}  {fp:4d}  {2 * p * r / max(p + r, 1e-9):.3f}")
    for indice in np.argsort(positifs)[:5]:
        print("  rescan difficile :", fichiers[indice].name, round(float(positifs[indice]), 3))


if __name__ == "__main__":
    main()
