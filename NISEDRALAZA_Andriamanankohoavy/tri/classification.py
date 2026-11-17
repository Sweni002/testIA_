from pathlib import Path

import numpy as np

CLASSES = ["plan", "coupe_facade", "plan_situation", "texte", "tableau"]
CHEMIN_MODELE = Path(__file__).resolve().parent.parent / "model" / "foret.npz"


class ForetExportee:
    def __init__(self, gauche, droite, variable, seuil, valeurs, racines, classes, profondeur):
        self.gauche = gauche
        self.droite = droite
        self.variable = variable
        self.seuil = seuil
        self.valeurs = valeurs
        self.racines = racines
        self.classes = list(classes)
        self.profondeur = int(profondeur)

    @classmethod
    def depuis_sklearn(cls, foret) -> "ForetExportee":
        gauche, droite, variable, seuil, valeurs, racines = [], [], [], [], [], []
        decalage, profondeur = 0, 0
        for estimateur in foret.estimators_:
            arbre = estimateur.tree_
            feuille = arbre.children_left == -1
            racines.append(decalage)
            gauche.append(np.where(feuille, -1, arbre.children_left + decalage))
            droite.append(np.where(feuille, -1, arbre.children_right + decalage))
            variable.append(np.where(feuille, 0, arbre.feature))
            seuil.append(arbre.threshold)
            brutes = arbre.value[:, 0, :]
            valeurs.append(brutes / np.maximum(brutes.sum(1, keepdims=True), 1e-12))
            profondeur = max(profondeur, arbre.max_depth)
            decalage += arbre.node_count
        return cls(np.concatenate(gauche).astype(np.int32), np.concatenate(droite).astype(np.int32),
                   np.concatenate(variable).astype(np.int32), np.concatenate(seuil),
                   np.concatenate(valeurs).astype(np.float32), np.array(racines, np.int32),
                   [str(c) for c in foret.classes_], profondeur)

    def sauvegarder(self, chemin) -> None:
        np.savez_compressed(chemin, gauche=self.gauche, droite=self.droite, variable=self.variable,
                            seuil=self.seuil, valeurs=self.valeurs, racines=self.racines,
                            classes=np.array(self.classes), profondeur=np.array(self.profondeur))

    @classmethod
    def charger(cls, chemin) -> "ForetExportee":
        with np.load(chemin, allow_pickle=False) as donnees:
            return cls(donnees["gauche"], donnees["droite"], donnees["variable"], donnees["seuil"],
                       donnees["valeurs"], donnees["racines"], donnees["classes"].tolist(),
                       donnees["profondeur"])

    def probabilites(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32).astype(np.float64)
        lignes = np.arange(len(x))
        total = np.zeros((len(x), len(self.classes)))
        for racine in self.racines:
            noeud = np.full(len(x), racine, dtype=np.int64)
            for _ in range(self.profondeur + 1):
                interne = self.gauche[noeud] >= 0
                if not interne.any():
                    break
                va_gauche = x[lignes, self.variable[noeud]] <= self.seuil[noeud]
                suivant = np.where(va_gauche, self.gauche[noeud], self.droite[noeud])
                noeud = np.where(interne, suivant, noeud)
            total += self.valeurs[noeud]
        return total / max(len(self.racines), 1)

    def predire(self, x: np.ndarray) -> list:
        if len(x) == 0:
            return []
        return [self.classes[i] for i in np.argmax(self.probabilites(x), axis=1)]
