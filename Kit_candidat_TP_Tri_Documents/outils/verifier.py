"""Auto-vérification sur le dossier d'exemple (mêmes règles de notation que la correction).

Usage (depuis la racine du kit) :
    python outils/verifier.py rendu_modele
La correction finale utilise un autre dossier client, non communiqué.
"""
import json, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import scoring4 as sc

EX = HERE.parent / "donnees" / "dossier_exemple"


def main(sub):
    sub = Path(sub).resolve()
    entry = sub / "trier.py"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "sortie.json"
        t0 = time.time()
        r = subprocess.run([sys.executable, str(entry), str(EX / "dossier_client"), str(EX / "bordereau.csv"),
                            str(EX / "referentiel.json"), str(out)], cwd=entry.parent, capture_output=True, text=True)
        print(f"Durée d'exécution : {time.time() - t0:.1f} s")
        if r.returncode != 0 or not out.exists():
            print("ÉCHEC d'exécution :\n" + r.stderr[-2000:])
            return
        res = sc.score(json.load(open(out, encoding="utf-8")), json.load(open(EX / "attendu.json", encoding="utf-8")))
    print(f"Partie A : {res['A_sur_40']} / 40")
    print(f"Partie B : {res['B_sur_25']} / 25")
    for k, v in res["detail_points"].items():
        print(f"  {k:<16} {v:>6} / {sc.BAREME[k]}   (taux {res['detail_taux'][k]})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "rendu_modele")
