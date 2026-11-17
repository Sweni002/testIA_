import tempfile
import unittest
from pathlib import Path

import fabrique
from tri.inventaire import COTE_MAX, est_ignore, inventorier, lire_document


class TestInventaire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dossier = tempfile.TemporaryDirectory()
        fabrique.dossier_client(Path(cls.dossier.name))
        cls.documents = {d.chemin: d for d in inventorier(cls.dossier.name)}

    @classmethod
    def tearDownClass(cls):
        cls.dossier.cleanup()

    def test_chemins_relatifs_avec_barre_oblique(self):
        self.assertEqual(set(self.documents), {
            "Plans/Scan_01.pdf", "Plans/copie.pdf", "IMG_0002.JPG", "autre.png", "Docs/vide.pdf",
            "Docs/faux.png", "Docs/casse.pdf", "envoi.zip/dans_zip.jpg", "envoi.zip/sous/niveau.png",
        })

    def test_nombre_de_pages(self):
        self.assertEqual(len(self.documents["Plans/Scan_01.pdf"].pages), 2)
        self.assertEqual(len(self.documents["IMG_0002.JPG"].pages), 1)
        self.assertEqual(len(self.documents["envoi.zip/sous/niveau.png"].pages), 1)

    def test_fichiers_illisibles_signales(self):
        for chemin in ("Docs/vide.pdf", "Docs/faux.png", "Docs/casse.pdf"):
            with self.subTest(chemin=chemin):
                self.assertEqual(self.documents[chemin].statut, "illisible")
                self.assertEqual(self.documents[chemin].pages, [])

    def test_pages_en_niveaux_de_gris_reduites(self):
        page = self.documents["Plans/Scan_01.pdf"].pages[0]
        self.assertEqual(page.ndim, 2)
        self.assertLessEqual(max(page.shape), COTE_MAX)


class TestCasParticuliers(unittest.TestCase):
    def test_extension_ne_correspond_pas_au_contenu(self):
        png = fabrique.octets_image(fabrique.page_plan(1), "PNG")
        self.assertEqual(lire_document("x.jpg", png).statut, "illisible")
        self.assertEqual(lire_document("x.png", png).statut, "ok")

    def test_extension_inconnue(self):
        self.assertEqual(lire_document("notes.txt", b"bonjour").statut, "illisible")

    def test_image_tronquee(self):
        jpeg = fabrique.octets_image(fabrique.page_plan(1), "JPEG")
        self.assertEqual(lire_document("x.jpg", jpeg[: len(jpeg) // 3]).statut, "illisible")

    def test_zip_corrompu(self):
        with tempfile.TemporaryDirectory() as dossier:
            fabrique.ecrire(Path(dossier), "archive.zip", b"PK\x03\x04pas un zip")
            documents = inventorier(dossier)
        self.assertEqual([(d.chemin, d.statut) for d in documents], [("archive.zip", "illisible")])

    def test_fichiers_systeme_ignores(self):
        for chemin in ("Thumbs.db", "a/.DS_Store", "DESKTOP.INI", "__MACOSX/x.jpg", "a/._x.jpg"):
            with self.subTest(chemin=chemin):
                self.assertTrue(est_ignore(chemin))
        self.assertFalse(est_ignore("Plans/plan.pdf"))

    def test_dossier_inexistant(self):
        self.assertEqual(inventorier("dossier/qui/n/existe/pas"), [])


if __name__ == "__main__":
    unittest.main()
