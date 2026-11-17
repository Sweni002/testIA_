import io
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

DOSSIER_KIT = RACINE.parent / "Kit_candidat_TP_Tri_Documents"

BATIMENTS = [
    {"code": "BA", "nom": "Bâtiment A", "alias": ["Bâtiment A - Logements", "Logements A"]},
    {"code": "BB", "nom": "Bâtiment B", "alias": ["Bâtiment B - Bureaux"]},
    {"code": "BC", "nom": "Bâtiment C", "alias": ["Bâtiment C - Commerces", "Commerces"]},
    {"code": "PK", "nom": "Parking", "alias": ["Parking souterrain"]},
]


def page_plan(graine: int, taille=(620, 877)) -> Image.Image:
    generateur = np.random.default_rng(graine)
    image = Image.new("L", taille, 235)
    dessin = ImageDraw.Draw(image)
    largeur, hauteur = taille
    gauche, haut, droite, bas = 40, 40, largeur - 40, int(hauteur * 0.7)
    dessin.rectangle([gauche, haut, droite, bas], outline=0, width=6)
    for _ in range(4):
        x = int(generateur.integers(gauche + 40, droite - 40))
        dessin.line([x, haut, x, bas], fill=0, width=5)
        y = int(generateur.integers(haut + 40, bas - 40))
        dessin.line([gauche, y, droite, y], fill=0, width=5)
    for _ in range(12):
        x = int(generateur.integers(gauche + 10, droite - 60))
        y = int(generateur.integers(haut + 10, bas - 20))
        dessin.text((x, y), f"P{int(generateur.integers(100))}", fill=40)
    dessin.rectangle([largeur - 220, hauteur - 120, largeur - 30, hauteur - 30], outline=0, width=2)
    dessin.text((largeur - 210, hauteur - 110), "FUTURMAP", fill=0)
    return image


def rescan(image: Image.Image, quart_de_tour: int = 1) -> Image.Image:
    tourne = image.rotate(1.5, resample=Image.Resampling.BILINEAR, expand=True, fillcolor=250)
    reduit = tourne.resize((int(tourne.width * 0.9), int(tourne.height * 0.9)), Image.Resampling.BILINEAR)
    toile = Image.new("L", (reduit.width + 30, reduit.height + 30), 250)
    toile.paste(reduit, (20, 8))
    toile = toile.rotate(90 * quart_de_tour, expand=True)
    flux = io.BytesIO()
    toile.save(flux, format="JPEG", quality=60)
    return Image.open(io.BytesIO(flux.getvalue())).convert("L")


def octets_image(image: Image.Image, format_image: str) -> bytes:
    flux = io.BytesIO()
    image.save(flux, format=format_image)
    return flux.getvalue()


def octets_pdf(images: list) -> bytes:
    flux = io.BytesIO()
    images[0].convert("RGB").save(flux, format="PDF", save_all=True,
                                  append_images=[i.convert("RGB") for i in images[1:]])
    return flux.getvalue()


def octets_zip(entrees: dict) -> bytes:
    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w") as archive:
        for nom, contenu in entrees.items():
            archive.writestr(nom, contenu)
    return flux.getvalue()


def ecrire(racine: Path, chemin: str, contenu: bytes) -> None:
    cible = racine / chemin
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_bytes(contenu)


def dossier_client(racine: Path) -> None:
    plan_a = page_plan(1)
    ecrire(racine, "Plans/Scan_01.pdf", octets_pdf([plan_a, page_plan(2)]))
    ecrire(racine, "Plans/copie.pdf", octets_pdf([plan_a, page_plan(2)]))
    ecrire(racine, "IMG_0002.JPG", octets_image(rescan(plan_a), "JPEG"))
    ecrire(racine, "autre.png", octets_image(page_plan(3), "PNG"))
    ecrire(racine, "Docs/vide.pdf", b"")
    ecrire(racine, "Docs/faux.png", "Ceci n'est pas une image".encode())
    ecrire(racine, "Docs/casse.pdf", b"%PDF-1.4\n%broken")
    ecrire(racine, "Thumbs.db", b"\x00\x01")
    ecrire(racine, "Docs/desktop.ini", b"[x]")
    ecrire(racine, "envoi.zip", octets_zip({
        "dans_zip.jpg": octets_image(page_plan(4), "JPEG"),
        "sous/niveau.png": octets_image(page_plan(5), "PNG"),
        ".DS_Store": b"x",
    }))
