import unittest

import fabrique
from tri.normalisation import ReferentielBatiments, normaliser_date, normaliser_niveau


class TestBatiment(unittest.TestCase):
    def setUp(self):
        self.referentiel = ReferentielBatiments(fabrique.BATIMENTS)

    def test_formes_du_sujet(self):
        cas = {
            "Bât.A": "BA", "BAT. A": "BA", "batiment-a": "BA", " Bat  A ": "BA", "Batiment-A": "BA",
            "BÂTIMENT C": "BC", "bat c": "BC", "Bât.B": "BB", "BatB": "BB",
            "Logements A": "BA", "Bâtiment A - Logements": "BA", "Bâtiment B - Bureaux": "BB",
            "Commerces": "BC", "PARKING": "PK", "Parking  Souterrain": "PK", "PK ": "PK", "pk": "PK",
        }
        for valeur, attendu in cas.items():
            with self.subTest(valeur=valeur):
                self.assertEqual(self.referentiel.normaliser(valeur), attendu)

    def test_formes_partielles(self):
        self.assertEqual(self.referentiel.normaliser("Bat A logements neufs"), "BA")
        self.assertEqual(self.referentiel.normaliser("Bureaux"), "BB")

    def test_abreviations_et_singuliers(self):
        cas = {
            "Bt A": "BA", "Bld A": "BA", "Immeuble A": "BA", "Bloc A": "BA", "Log. A": "BA", "Logement": "BA",
            "Bureau": "BB", "Commerce": "BC", "Park.": "PK", "Parking sous-sol": "PK",
        }
        for valeur, attendu in cas.items():
            with self.subTest(valeur=valeur):
                self.assertEqual(self.referentiel.normaliser(valeur), attendu)

    def test_valeurs_inconnues_ou_vides(self):
        for valeur in ("", None, "   ", "Bâtiment Z", "batiment", "inconnu", "Logistique", "Parc", "Batiment A1"):
            with self.subTest(valeur=valeur):
                self.assertIsNone(self.referentiel.normaliser(valeur))


class TestNiveau(unittest.TestCase):
    def test_formes_du_sujet(self):
        cas = {
            "RDC": "R+0", "rez-de-chaussée": "R+0", "Rez de chaussee": "R+0", "R0": "R+0", "Niv 0": "R+0",
            "Niveau 0": "R+0", "R+1": "R+1", "r+4": "R+4", "R4": "R+4", "R1": "R+1", "Niv 3": "R+3",
            "Niveau 5": "R+5", "Etage 2": "R+2", "ÉTAGE 3": "R+3", "1er étage": "R+1", "2e étage": "R+2",
            "2ème étage": "R+2", "5eme étage": "R+5", "premier étage": "R+1", "R-1": "R-1", "R-2": "R-2",
            "SS 2": "R-2", "SS1": "R-1", "Sous-sol 1": "R-1", "sous sol 2": "R-2", "S-Sol 2": "R-2",
            "Niveau -1": "R-1", "Niveau -2": "R-2", "Sous-sol": "R-1", "2e sous-sol": "R-2", "1er sous-sol": "R-1", "Toiture": "TT", "Terrasse": "TT",
            "TOITURE-TERRASSE": "TT", "TT": "TT",
        }
        for valeur, attendu in cas.items():
            with self.subTest(valeur=valeur):
                self.assertEqual(normaliser_niveau(valeur), attendu)

    def test_variantes_abregees_et_anglaises(self):
        cas = {
            "R +1": "R+1", "R+01": "R+1", "N-1": "R-1", "Niv. -1": "R-1", "Niveau R+3": "R+3", "-1": "R-1",
            "Etage 1er": "R+1", "E1": "R+1", "Etg 2": "R+2", "Et. 3": "R+3", "4ème": "R+4", "RDJ": "R+0",
            "Sous sol niveau 2": "R-2", "Deuxième sous-sol": "R-2", "SS-2": "R-2", "Basement 1": "R-1",
            "B1": "R-1", "Ground floor": "R+0", "1st floor": "R+1", "Floor 2": "R+2", "Level 3": "R+3",
            "Roof": "TT", "R‑1": "R-1",
        }
        for valeur, attendu in cas.items():
            with self.subTest(valeur=valeur):
                self.assertEqual(normaliser_niveau(valeur), attendu)

    def test_lettre_de_batiment_non_confondue(self):
        for valeur, attendu in {"Bat B niveau 2": "R+2", "Niv 2 B": "R+2", "Lot 3": None, "Rue 3": None}.items():
            with self.subTest(valeur=valeur):
                self.assertEqual(normaliser_niveau(valeur), attendu)

    def test_hors_referentiel_ou_vide(self):
        for valeur in ("", None, "R+9", "SS 4", "grenier", "Mezzanine", "Etage"):
            with self.subTest(valeur=valeur):
                self.assertIsNone(normaliser_niveau(valeur))

    def test_liste_de_niveaux_du_referentiel(self):
        self.assertEqual(normaliser_niveau("Etage 7", ["R+7"]), "R+7")
        self.assertIsNone(normaliser_niveau("Etage 7"))


class TestDate(unittest.TestCase):
    def test_formes_du_sujet(self):
        cas = {
            "15/03/2024": "2024-03-15", "15-03-2024": "2024-03-15", "15.03.24": "2024-03-15",
            "2024-03-15": "2024-03-15", "15 mars 2024": "2024-03-15", "3 févr. 2021": "2021-02-03",
            "3 fevr. 2021": "2021-02-03", "23 Décembre 2020": "2020-12-23", "12 janv. 2019": "2019-01-12",
            "1er août 2022": "2022-08-01", "08 Octobre 2023": "2023-10-08", "7 déc. 2019": "2019-12-07",
            "lundi 4 septembre 2019": "2019-09-04", "15-mars-2024": "2024-03-15", "1er-avril-2022": "2022-04-01", "10.01.19": "2019-01-10", "2024/03/15": "2024-03-15",
        }
        for valeur, attendu in cas.items():
            with self.subTest(valeur=valeur):
                self.assertEqual(normaliser_date(valeur), attendu)

    def test_formats_exportes_et_anglais(self):
        cas = {
            "2024-03-15 00:00:00": "2024-03-15", "15/03/2024 10:30": "2024-03-15", "15 03 2024": "2024-03-15",
            "Mar 15, 2024": "2024-03-15", "March 15, 2024": "2024-03-15", "15-Mar-24": "2024-03-15",
            "mars 15 2024": "2024-03-15", "Sept. 4, 2019": "2019-09-04", "15032024": "2024-03-15",
            "20240315": "2024-03-15", "45366": "2024-03-15", "45366.0": "2024-03-15", "15‑03‑2024": "2024-03-15",
        }
        for valeur, attendu in cas.items():
            with self.subTest(valeur=valeur):
                self.assertEqual(normaliser_date(valeur), attendu)

    def test_dates_invalides_ou_vides(self):
        for valeur in ("", None, "31/02/2024", "mars 2024", "n/a", "45 truc 2020", "12345", "2024"):
            with self.subTest(valeur=valeur):
                self.assertIsNone(normaliser_date(valeur))


if __name__ == "__main__":
    unittest.main()
