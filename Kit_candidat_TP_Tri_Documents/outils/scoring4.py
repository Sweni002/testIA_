"""Notation automatique du TP « Tri d'un dossier de documents scannés »."""
from itertools import combinations

CLASSES = ["plan", "coupe_facade", "plan_situation", "texte", "tableau"]
BAREME = {"inv_chemins": 3, "inv_pages": 3, "inv_illisibles": 1, "inv_manquants": 1,
          "dbl_exacts": 4, "dbl_f1": 12, "norm_batiment": 6, "norm_niveau": 6, "norm_date": 4, "classif": 25}


def f1(pred, true):
    pred, true = set(pred), set(true)
    if not pred and not true:
        return 1.0
    tp = len(pred & true)
    if tp == 0:
        return 0.0
    p, r = tp / len(pred), tp / len(true)
    return 2 * p * r / (p + r)


def pairs(groups):
    out = set()
    for g in groups:
        if isinstance(g, (list, tuple)):
            for a, b in combinations(sorted(set(map(str, g))), 2):
                out.add((a, b))
    return out


def macro_f1(pred, true):
    s = 0
    for c in CLASSES:
        tp = sum(1 for k, v in true.items() if v == c and pred.get(k) == c)
        fp = sum(1 for k, v in pred.items() if v == c and true.get(k) != c and k in true)
        fn = sum(1 for k, v in true.items() if v == c and pred.get(k) != c)
        s += 0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)
    return s / len(CLASSES)


def score(out, truth):
    det = {}
    files = {}
    for f in out.get("fichiers", []) if isinstance(out, dict) else []:
        if isinstance(f, dict) and "chemin" in f:
            files.setdefault(str(f["chemin"]), f)
    T = truth["fichiers"]
    det["inv_chemins"] = f1(files, T)
    ok = [k for k, v in T.items() if v["statut"] == "ok"]
    det["inv_pages"] = sum(1 for k in ok if k in files and files[k].get("pages") == T[k]["pages"]) / len(ok)
    ill_t = {k for k, v in T.items() if v["statut"] == "illisible"}
    ill_p = {k for k, v in files.items() if v.get("statut") == "illisible"}
    det["inv_illisibles"] = f1(ill_p, ill_t)
    man = out.get("manquants", []) if isinstance(out, dict) else []
    det["inv_manquants"] = f1({str(m).lower() for m in man if isinstance(m, str)}, {m.lower() for m in truth["manquants"]})
    P = pairs(out.get("doublons", []) if isinstance(out, dict) else [])
    Tp = pairs(truth["doublons"])
    ex = {tuple(sorted(p)) for p in truth["paires_exactes"]}
    det["dbl_exacts"] = len(ex & P) / len(ex) if ex else 1.0
    det["dbl_f1"] = f1(P, Tp)
    for champ in ("batiment", "niveau", "date"):
        det[f"norm_{champ}"] = sum(1 for k in ok if k in files and files[k].get(champ) == T[k][champ]) / len(ok)
    pred = {}
    for k, f in files.items():
        cl = f.get("classes", [])
        if isinstance(cl, list):
            for i, c in enumerate(cl, 1):
                pred[f"{k}#{i}"] = c
    det["classif"] = macro_f1(pred, truth["pages"])
    pts = {k: round(BAREME[k] * v, 2) for k, v in det.items()}
    A = round(sum(v for k, v in pts.items() if k != "classif"), 2)
    return {"A_sur_40": A, "B_sur_25": pts["classif"], "detail_points": pts, "detail_taux": {k: round(v, 3) for k, v in det.items()}}
