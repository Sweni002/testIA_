import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tri.pipeline import trier

USAGE = "Usage : python trier.py <dossier_client> <bordereau.csv> <referentiel.json> <sortie.json>"


def main(arguments: list) -> int:
    if len(arguments) != 4:
        print(USAGE, file=sys.stderr)
        return 2
    dossier, bordereau, referentiel, sortie = arguments
    if not Path(dossier).is_dir():
        print(f"[avertissement] dossier client introuvable : {dossier}", file=sys.stderr)
    resultat = trier(dossier, bordereau, referentiel)
    chemin_sortie = Path(sortie)
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin_sortie, "w", encoding="utf-8") as flux:
        json.dump(resultat, flux, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
