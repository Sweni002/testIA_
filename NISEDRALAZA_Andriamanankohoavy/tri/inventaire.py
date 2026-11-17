import io
import os
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageOps

COTE_MAX = 1000
FICHIERS_SYSTEME = {"thumbs.db", ".ds_store", "desktop.ini"}
SIGNATURES = {
    ".pdf": (b"%PDF",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".tif": (b"II*\x00", b"MM\x00*"),
    ".tiff": (b"II*\x00", b"MM\x00*"),
    ".bmp": (b"BM",),
    ".gif": (b"GIF87a", b"GIF89a"),
}


@dataclass
class Document:
    chemin: str
    statut: str
    pages: list = field(default_factory=list)
    nombre_pages: int = 0

    def __post_init__(self):
        self.nombre_pages = self.nombre_pages or len(self.pages)

    def liberer_pages(self) -> None:
        self.pages = []

    @property
    def nom(self) -> str:
        return PurePosixPath(self.chemin).name

    @property
    def lisible(self) -> bool:
        return self.statut == "ok"


def normaliser_chemin(chemin: str) -> str:
    return unicodedata.normalize("NFC", chemin.replace("\\", "/"))


def est_ignore(chemin: str) -> bool:
    parties = PurePosixPath(chemin).parts
    if any(p.lower() == "__macosx" for p in parties):
        return True
    nom = parties[-1] if parties else ""
    return nom.lower() in FICHIERS_SYSTEME or nom.startswith("._")


def reduire(image: Image.Image) -> np.ndarray:
    image = image.convert("L")
    cote = max(image.size)
    if cote > COTE_MAX:
        facteur = COTE_MAX / cote
        taille = (max(1, round(image.width * facteur)), max(1, round(image.height * facteur)))
        image = image.resize(taille, Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.uint8)


def lire_pdf(donnees: bytes) -> list:
    pdf = pdfium.PdfDocument(donnees)
    try:
        pages = []
        for index in range(len(pdf)):
            page = pdf[index]
            largeur, hauteur = page.get_size()
            echelle = COTE_MAX / max(largeur, hauteur, 1)
            rendu = page.render(scale=echelle, grayscale=True).to_pil()
            pages.append(reduire(rendu))
            page.close()
        return pages
    finally:
        pdf.close()


def lire_image(donnees: bytes) -> list:
    with Image.open(io.BytesIO(donnees)) as image:
        nb_images = getattr(image, "n_frames", 1) if image.format == "TIFF" else 1
        pages = []
        for index in range(nb_images):
            image.seek(index)
            image.load()
            pages.append(reduire(ImageOps.exif_transpose(image)))
        return pages


def contenu_conforme(extension: str, donnees: bytes) -> bool:
    attendus = SIGNATURES.get(extension)
    return attendus is not None and donnees.startswith(attendus)


def lire_document(chemin: str, donnees: bytes) -> Document:
    extension = PurePosixPath(chemin).suffix.lower()
    if not donnees or not contenu_conforme(extension, donnees):
        return Document(chemin, "illisible")
    try:
        pages = lire_pdf(donnees) if extension == ".pdf" else lire_image(donnees)
    except Exception:
        return Document(chemin, "illisible")
    if not pages:
        return Document(chemin, "illisible")
    return Document(chemin, "ok", pages)


def nom_entree_zip(info: zipfile.ZipInfo) -> str:
    nom = info.filename
    if not info.flag_bits & 0x800:
        try:
            nom = nom.encode("cp437").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return normaliser_chemin(nom).strip("/")


def lire_zip(chemin: str, donnees: bytes) -> list:
    try:
        archive = zipfile.ZipFile(io.BytesIO(donnees))
    except (zipfile.BadZipFile, OSError, ValueError):
        return [Document(chemin, "illisible")]
    documents = []
    with archive:
        for info in sorted(archive.infolist(), key=lambda i: i.filename):
            nom = nom_entree_zip(info)
            if info.is_dir() or not nom or est_ignore(nom):
                continue
            chemin_entree = f"{chemin}/{nom}"
            try:
                contenu = archive.read(info)
            except Exception:
                documents.append(Document(chemin_entree, "illisible"))
                continue
            documents.extend(lire_fichier(chemin_entree, contenu))
    return documents


def lire_fichier(chemin: str, donnees: bytes) -> list:
    if PurePosixPath(chemin).suffix.lower() == ".zip":
        return lire_zip(chemin, donnees)
    return [lire_document(chemin, donnees)]


def inventorier(racine: str) -> list:
    documents = []
    for dossier, sous_dossiers, fichiers in os.walk(racine):
        sous_dossiers.sort()
        for nom in sorted(fichiers):
            complet = os.path.join(dossier, nom)
            chemin = normaliser_chemin(os.path.relpath(complet, racine))
            if est_ignore(chemin):
                continue
            try:
                with open(complet, "rb") as flux:
                    donnees = flux.read()
            except OSError:
                documents.append(Document(chemin, "illisible"))
                continue
            documents.extend(lire_fichier(chemin, donnees))
    return documents
