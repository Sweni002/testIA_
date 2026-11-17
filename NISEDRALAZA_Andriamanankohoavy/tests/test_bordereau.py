import json
import tempfile
import unittest
from pathlib import Path

import fabrique
from tri.bordereau import (charger_referentiel, cle_fichier, indexer, lire_bordereau, lire_lignes, manquants,
                           normaliser_ligne)

CSV = (
    "Nom du fichier;Bâtiment;Niveau;Date;Observations\n"
    "Plan R1.PDF;Bât.A;1er étage;15/03/2024;à vérifier\n"
    "relevé RDC.jpg; Bat  B ;RDC;3 févr. 2021;\n"
    "absent.pdf;Parking;SS 1;2024-01-02;\n"
    "plan r1.pdf;;;;doublon de ligne\n"
)


class TestLecture(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.racine = Path(self.dossier.name)

    def tearDown(self):
        self.dossier.cleanup()

    def test_lecture_windows_1252(self):
        fabrique.ecrire(self.racine, "bordereau.csv", CSV.encode("cp1252"))
        chemin = self.racine / "bordereau.csv"
        lignes = lire_bordereau(str(chemin))
        self.assertEqual([l.nom for l in lignes], ["Plan R1.PDF", "relevé RDC.jpg", "absent.pdf", "plan r1.pdf"])
        self.assertEqual(lignes[0].batiment, "Bât.A")
        self.assertEqual(lignes[1].niveau, "RDC")

    def test_lecture_utf8_acceptee(self):
        fabrique.ecrire(self.racine, "bordereau.csv", CSV.encode("utf-8-sig"))
        chemin = self.racine / "bordereau.csv"
        self.assertEqual(lire_bordereau(str(chemin))[1].nom, "relevé RDC.jpg")

    def test_colonnes_dans_un_autre_ordre(self):
        lignes = lire_lignes("Date;Nom du fichier;Niveau;Bâtiment\n01/02/2020;a.pdf;R+1;BA\n")
        self.assertEqual((lignes[0].nom, lignes[0].batiment, lignes[0].niveau, lignes[0].date),
                         ("a.pdf", "BA", "R+1", "01/02/2020"))

    def test_lignes_courtes_et_vides(self):
        lignes = lire_lignes("Nom du fichier;Bâtiment;Niveau;Date\nseul.pdf\n;;;\n\n")
        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0].batiment, "")

    def test_fichier_vide(self):
        self.assertEqual(lire_lignes(""), [])


class TestCorrespondance(unittest.TestCase):
    def test_cle_insensible_a_la_casse(self):
        self.assertEqual(cle_fichier("PLAN R1.PDF"), cle_fichier("plan r1.pdf"))
        self.assertEqual(cle_fichier("NUMÉRISATION 8502.PNG"), cle_fichier("Numérisation 8502.png"))
        self.assertEqual(cle_fichier("archive.zip/sous/x.JPG"), cle_fichier("x.jpg"))
        self.assertNotEqual(cle_fichier("plan.pdf"), cle_fichier("plan.png"))

    def test_lignes_en_double_fusionnees(self):
        index = indexer(lire_lignes(CSV))
        ligne = index[cle_fichier("PLAN R1.pdf")]
        self.assertEqual((ligne.batiment, ligne.date), ("Bât.A", "15/03/2024"))

    def test_manquants_ecrits_comme_dans_le_bordereau(self):
        lignes = lire_lignes(CSV)
        presents = {cle_fichier("plan r1.pdf"), cle_fichier("RELEVÉ rdc.JPG")}
        self.assertEqual(manquants(lignes, presents), ["absent.pdf"])


class TestNormalisationLigne(unittest.TestCase):
    def test_ligne_complete_et_absente(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "referentiel.json"
            chemin.write_text(json.dumps({"batiments": fabrique.BATIMENTS, "niveaux": ["R-1", "R+0", "R+1"]}),
                              encoding="utf-8")
            referentiel = charger_referentiel(str(chemin))
        ligne = lire_lignes(CSV)[0]
        self.assertEqual(normaliser_ligne(ligne, referentiel),
                         {"batiment": "BA", "niveau": "R+1", "date": "2024-03-15"})
        self.assertEqual(normaliser_ligne(None, referentiel), {"batiment": None, "niveau": None, "date": None})


if __name__ == "__main__":
    unittest.main()
