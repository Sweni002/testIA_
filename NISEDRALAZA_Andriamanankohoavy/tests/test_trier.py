import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fabrique
from tri.classification import CLASSES

TRIER = fabrique.RACINE / "trier.py"
EXEMPLE = fabrique.DOSSIER_KIT / "donnees" / "dossier_exemple"
CLES = ["chemin", "statut", "pages", "batiment", "niveau", "date", "classes"]

BORDEREAU = (
    "Nom du fichier;Bâtiment;Niveau;Date;Observations\n"
    "scan_01.PDF;Bat A;R+1;15.03.24;\n"
    "Docs/faux.png;Bât A;RDC;01/01/2020;\n"
    "dans_zip.JPG;parking;SS 1;3 févr. 2021;\n"
    "fantome.pdf;Bat A;;;\n"
)
REFERENTIEL = {
    "batiments": [{"code": "BA", "nom": "Bâtiment A", "alias": []},
                  {"code": "PK", "nom": "Parking", "alias": ["Parking souterrain"]}],
    "niveaux": ["R-2", "R-1", "R+0", "R+1", "R+2", "TT"],
}


def executer(*arguments):
    return subprocess.run([sys.executable, str(TRIER), *map(str, arguments)], capture_output=True, text=True)


class TestBoutEnBout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dossier = tempfile.TemporaryDirectory()
        racine = Path(cls.dossier.name)
        fabrique.dossier_client(racine / "client")
        (racine / "bordereau.csv").write_bytes(BORDEREAU.encode("cp1252"))
        (racine / "referentiel.json").write_text(json.dumps(REFERENTIEL), encoding="utf-8")
        cls.processus = executer(racine / "client", racine / "bordereau.csv", racine / "referentiel.json",
                                 racine / "sortie" / "resultat.json")
        sortie = racine / "sortie" / "resultat.json"
        cls.resultat = json.loads(sortie.read_text(encoding="utf-8")) if sortie.exists() else None

    @classmethod
    def tearDownClass(cls):
        cls.dossier.cleanup()

    def fichier(self, chemin):
        return next(f for f in self.resultat["fichiers"] if f["chemin"] == chemin)

    def test_execution_reussie(self):
        self.assertEqual(self.processus.returncode, 0, self.processus.stderr)
        self.assertEqual(set(self.resultat), {"fichiers", "doublons", "manquants"})

    def test_format_de_chaque_fichier(self):
        for entree in self.resultat["fichiers"]:
            with self.subTest(chemin=entree["chemin"]):
                self.assertEqual(list(entree), CLES)
                self.assertEqual(len(entree["classes"]), entree["pages"])
                self.assertTrue(set(entree["classes"]) <= set(CLASSES))

    def test_valeurs_du_bordereau(self):
        scan = self.fichier("Plans/Scan_01.pdf")
        self.assertEqual((scan["batiment"], scan["niveau"], scan["date"]), ("BA", "R+1", "2024-03-15"))
        zip_entree = self.fichier("envoi.zip/dans_zip.jpg")
        self.assertEqual((zip_entree["batiment"], zip_entree["niveau"], zip_entree["date"]),
                         ("PK", "R-1", "2021-02-03"))
        absent = self.fichier("autre.png")
        self.assertEqual((absent["batiment"], absent["niveau"], absent["date"]), (None, None, None))

    def test_fichier_illisible_sans_valeurs(self):
        faux = self.fichier("Docs/faux.png")
        self.assertEqual(faux, {"chemin": "Docs/faux.png", "statut": "illisible", "pages": 0,
                                "batiment": None, "niveau": None, "date": None, "classes": []})

    def test_manquants(self):
        self.assertEqual(self.resultat["manquants"], ["fantome.pdf"])

    def test_doublons(self):
        paires = {frozenset(p) for g in self.resultat["doublons"] for p in
                  ((a, b) for i, a in enumerate(g) for b in g[i + 1:])}
        self.assertIn(frozenset({"Plans/Scan_01.pdf#1", "Plans/copie.pdf#1"}), paires)
        self.assertIn(frozenset({"Plans/Scan_01.pdf#2", "Plans/copie.pdf#2"}), paires)
        self.assertIn(frozenset({"Plans/Scan_01.pdf#1", "IMG_0002.JPG#1"}), paires)
        self.assertNotIn(frozenset({"Plans/Scan_01.pdf#1", "Plans/Scan_01.pdf#2"}), paires)


class TestEntreesDegradees(unittest.TestCase):
    def test_mauvais_nombre_d_arguments(self):
        processus = executer("un", "deux")
        self.assertEqual(processus.returncode, 2)
        self.assertIn("Usage", processus.stderr)

    def test_bordereau_et_referentiel_absents(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            fabrique.ecrire(racine / "client", "a.png", fabrique.octets_image(fabrique.page_plan(1), "PNG"))
            processus = executer(racine / "client", racine / "absent.csv", racine / "absent.json",
                                 racine / "sortie.json")
            self.assertEqual(processus.returncode, 0, processus.stderr)
            resultat = json.loads((racine / "sortie.json").read_text(encoding="utf-8"))
        self.assertEqual(resultat["fichiers"][0]["chemin"], "a.png")
        self.assertEqual(resultat["manquants"], [])

    def test_referentiel_mal_forme(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            fabrique.ecrire(racine / "client", "a.png", fabrique.octets_image(fabrique.page_plan(1), "PNG"))
            (racine / "bordereau.csv").write_text("Nom du fichier;Bâtiment;Niveau;Date\na.png;BA;R+1;01/02/2020\n",
                                                  encoding="cp1252")
            (racine / "referentiel.json").write_text("{pas du json", encoding="utf-8")
            processus = executer(racine / "client", racine / "bordereau.csv", racine / "referentiel.json",
                                 racine / "sortie.json")
            self.assertEqual(processus.returncode, 0, processus.stderr)
            fichier = json.loads((racine / "sortie.json").read_text(encoding="utf-8"))["fichiers"][0]
        self.assertEqual((fichier["batiment"], fichier["niveau"], fichier["date"]), (None, "R+1", "2020-02-01"))


@unittest.skipUnless((EXEMPLE / "attendu.json").exists(), "dossier d'exemple du kit absent")
class TestDossierExemple(unittest.TestCase):
    def test_score_sur_le_dossier_exemple(self):
        sys.path.insert(0, str(fabrique.DOSSIER_KIT / "outils"))
        import scoring4
        with tempfile.TemporaryDirectory() as dossier:
            sortie = Path(dossier) / "sortie.json"
            processus = executer(EXEMPLE / "dossier_client", EXEMPLE / "bordereau.csv",
                                 EXEMPLE / "referentiel.json", sortie)
            self.assertEqual(processus.returncode, 0, processus.stderr)
            resultat = json.loads(sortie.read_text(encoding="utf-8"))
        attendu = json.loads((EXEMPLE / "attendu.json").read_text(encoding="utf-8"))
        note = scoring4.score(resultat, attendu)
        self.assertGreaterEqual(note["A_sur_40"], 38)
        self.assertGreaterEqual(note["B_sur_25"], 23)


if __name__ == "__main__":
    unittest.main()
