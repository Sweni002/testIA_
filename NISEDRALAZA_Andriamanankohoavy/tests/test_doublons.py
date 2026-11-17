import unittest

import numpy as np

import fabrique
from tri.doublons import SEUIL_DOUBLON, calculer_signature, regrouper, similarite
from tri.image import preparer


def signature(image):
    return calculer_signature(preparer(np.asarray(image)))


class TestSimilarite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = fabrique.page_plan(10)
        cls.sig_original = signature(cls.original)

    def test_rescan_tourne_d_un_quart_de_tour(self):
        for quart in (0, 1, 2, 3):
            with self.subTest(quart=quart):
                score = similarite(signature(fabrique.rescan(self.original, quart)), self.sig_original)
                self.assertGreaterEqual(score, SEUIL_DOUBLON)

    def test_pages_differentes_meme_gabarit(self):
        for graine in (11, 12, 13):
            with self.subTest(graine=graine):
                self.assertLess(similarite(signature(fabrique.page_plan(graine)), self.sig_original), SEUIL_DOUBLON)

    def test_page_blanche_sans_erreur(self):
        blanche = signature(np.full((877, 620), 240, np.uint8))
        self.assertLess(similarite(blanche, self.sig_original), SEUIL_DOUBLON)


class TestRegroupement(unittest.TestCase):
    def test_copies_exactes_regroupees_par_empreinte(self):
        groupes = regrouper(["a#1", "b#1", "c#1"], [None, None, None], ["h1", "h1", "h2"])
        self.assertEqual(groupes, [["a#1", "b#1"]])

    def test_groupes_transitifs_et_tries(self):
        sig = signature(fabrique.page_plan(20))
        autre = signature(fabrique.page_plan(21))
        groupes = regrouper(["z#1", "y#1", "x#2", "w#1"], [sig, autre, sig, sig], ["1", "2", "3", "4"])
        self.assertEqual(groupes, [["w#1", "x#2", "z#1"]])

    def test_aucune_page(self):
        self.assertEqual(regrouper([], [], []), [])


if __name__ == "__main__":
    unittest.main()
