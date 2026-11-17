import tempfile
import unittest
from pathlib import Path

import numpy as np

import fabrique
from tri.caracteristiques import extraire
from tri.classification import CHEMIN_MODELE, CLASSES, ForetExportee
from tri.image import preparer

try:
    from sklearn.ensemble import ExtraTreesClassifier
except ImportError:
    ExtraTreesClassifier = None


class TestCaracteristiques(unittest.TestCase):
    def test_vecteur_de_taille_fixe_et_fini(self):
        tailles = set()
        for page in (np.asarray(fabrique.page_plan(1)), np.full((300, 200), 255, np.uint8),
                     np.zeros((50, 80), np.uint8)):
            valeurs = extraire(preparer(page))
            self.assertTrue(np.isfinite(valeurs).all())
            tailles.add(len(valeurs))
        self.assertEqual(len(tailles), 1)


@unittest.skipIf(ExtraTreesClassifier is None, "scikit-learn n'est nécessaire que pour l'entraînement")
class TestExport(unittest.TestCase):
    def test_export_identique_a_sklearn(self):
        generateur = np.random.default_rng(0)
        x = generateur.normal(size=(200, 6))
        y = np.array(CLASSES)[(x[:, 0] > 0).astype(int) + 2 * (x[:, 1] > 0).astype(int)]
        foret = ExtraTreesClassifier(n_estimators=20, random_state=0).fit(x, y)
        exportee = ForetExportee.depuis_sklearn(foret)
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "foret.npz"
            exportee.sauvegarder(chemin)
            rechargee = ForetExportee.charger(chemin)
        test = generateur.normal(size=(50, 6))
        np.testing.assert_allclose(rechargee.probabilites(test), foret.predict_proba(test), atol=1e-6)
        self.assertEqual(rechargee.predire(test), list(foret.predict(test)))


class TestModeleLivre(unittest.TestCase):
    def test_modele_livre_charge_et_predit(self):
        modele = ForetExportee.charger(CHEMIN_MODELE)
        self.assertEqual(sorted(modele.classes), sorted(CLASSES))
        valeurs = extraire(preparer(np.asarray(fabrique.page_plan(1))))
        self.assertIn(modele.predire(valeurs[None, :])[0], CLASSES)
        self.assertEqual(modele.predire(np.zeros((0, len(valeurs)))), [])


if __name__ == "__main__":
    unittest.main()
