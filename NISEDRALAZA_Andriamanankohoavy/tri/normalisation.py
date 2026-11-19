import re
import unicodedata
from datetime import date, timedelta

NIVEAUX_PAR_DEFAUT = ["R-2", "R-1", "R+0", "R+1", "R+2", "R+3", "R+4", "R+5", "TT"]

ORDINAUX = {
    "premier": "1", "premiere": "1", "second": "2", "seconde": "2", "deuxieme": "2",
    "troisieme": "3", "quatrieme": "4", "cinquieme": "5", "sixieme": "6",
    "septieme": "7", "huitieme": "8", "neuvieme": "9", "dixieme": "10",
}

MOIS = [
    ("janv", 1), ("jan", 1), ("fevr", 2), ("fev", 2), ("feb", 2), ("mars", 3), ("mar", 3),
    ("avr", 4), ("apr", 4), ("mai", 5), ("may", 5), ("juin", 6), ("jun", 6), ("juil", 7),
    ("jul", 7), ("aout", 8), ("aou", 8), ("aug", 8), ("sept", 9), ("sep", 9), ("oct", 10),
    ("nov", 11), ("dec", 12),
]
JOURS = {"lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"}
ABREVIATIONS_BATIMENT = {"bat", "bt", "bati", "batim", "bat.", "bld", "bldg", "building", "immeuble", "imm", "bloc"}
TIRETS = dict.fromkeys(map(ord, "‐‑‒–—−"), "-")
SUFFIXE_ORDINAL = r"(?:er|ere|e|eme|ieme|em|nd|nde|st|rd|th)?"
SOUS_SOL = r"(?:sous sol|soussol|s sol|ssol|ss|basement)"
ORIGINE_EXCEL = date(1899, 12, 30)


def sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte.translate(TIRETS))
    return "".join(c for c in decompose if not unicodedata.combining(c)).lower()


def simplifier(texte: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sans_accents(texte)).split())


def jetons_batiment(texte: str) -> list:
    simple = re.sub(r"\bbat(?:iment)?(?=[a-z0-9]\b)", "batiment ", simplifier(texte))
    return ["batiment" if mot in ABREVIATIONS_BATIMENT else mot for mot in simple.split()]


def racine(mot: str) -> str:
    return mot[:-1] if len(mot) > 3 and mot[-1] in "sx" else mot


def correspond(jeton: str, jeton_forme: str) -> bool:
    if racine(jeton) == racine(jeton_forme):
        return True
    return len(jeton) >= 3 and not jeton.isdigit() and jeton_forme.startswith(jeton)


def contient(jetons, forme) -> bool:
    return all(any(correspond(jeton, mot) for jeton in jetons) for mot in forme)


class ReferentielBatiments:
    def __init__(self, batiments: list):
        self.formes = []
        for batiment in batiments:
            code = str(batiment.get("code", "")).strip()
            if not code:
                continue
            noms = [code, batiment.get("nom") or ""] + list(batiment.get("alias") or [])
            for nom in noms:
                jetons = jetons_batiment(str(nom))
                if jetons:
                    self.formes.append((tuple(jetons), code))

    @staticmethod
    def _unique(codes) -> str | None:
        codes = set(codes)
        return codes.pop() if len(codes) == 1 else None

    def normaliser(self, valeur: str | None) -> str | None:
        jetons = jetons_batiment(valeur or "")
        if not jetons:
            return None
        compact = "".join(jetons)
        exacts = [code for forme, code in self.formes if "".join(forme) == compact]
        if exacts:
            return self._unique(exacts)
        ensemble = set(jetons)
        inclus = [(len(forme), code) for forme, code in self.formes if contient(ensemble, forme)]
        if inclus:
            plus_long = max(n for n, _ in inclus)
            return self._unique(code for n, code in inclus if n == plus_long)
        sans_generique = ensemble - {"batiment"}
        if sans_generique:
            englobants = [code for forme, code in self.formes
                          if all(contient(forme, [jeton]) for jeton in sans_generique)]
            return self._unique(englobants)
        return None


def simplifier_niveau(texte: str) -> str:
    simple = re.sub(r"[^a-z0-9+\-]+", " ", sans_accents(texte))
    simple = re.sub(r"(?<=[a-z])-(?=[a-z])", " ", simple)
    mots = [ORDINAUX.get(mot, mot) for mot in simple.split()]
    return " ".join(mots)


def formater_niveau(signe: str, nombre: int) -> str:
    if nombre == 0:
        return "R+0"
    return f"R-{nombre}" if signe == "-" else f"R+{nombre}"


def interpreter_niveau(texte: str) -> str | None:
    s = simplifier_niveau(texte)
    if not s:
        return None
    if re.search(r"\b(toit\w*|terrasse\w*|tt|roof\w*)\b", s):
        return "TT"
    if re.search(r"\b(rdc|rez|r d c|rdj|ground|gf)\b", s):
        return "R+0"
    m = re.search(rf"\b{SOUS_SOL}\s*(?:niveau|niv|n)?\s*-?\s*(\d+)\b", s) or re.fullmatch(r"b\s*-?\s*(\d+)", s)
    if m:
        return formater_niveau("-", int(m.group(1)))
    m = re.search(rf"\b(\d+)\s*{SUFFIXE_ORDINAL}\s*{SOUS_SOL}\b", s)
    if m:
        return formater_niveau("-", int(m.group(1)))
    if re.search(rf"\b{SOUS_SOL}\b", s):
        return "R-1"
    m = re.search(rf"\b(?:r|niv|niveau|n|etage|etg|et|e|level|lvl|l|floor)\s*([+-])?\s*(\d+){SUFFIXE_ORDINAL}\b", s)
    if m:
        return formater_niveau(m.group(1) or "+", int(m.group(2)))
    m = re.fullmatch(rf"(\d+)\s*{SUFFIXE_ORDINAL}\s*(?:etage|etg|et|floor)?", s)
    if m:
        return formater_niveau("+", int(m.group(1)))
    m = re.fullmatch(r"([+-])?\s*(\d+)", s)
    if m:
        return formater_niveau(m.group(1) or "+", int(m.group(2)))
    return None


def normaliser_niveau(valeur: str | None, niveaux: list = NIVEAUX_PAR_DEFAUT) -> str | None:
    niveau = interpreter_niveau(valeur or "")
    return niveau if niveau in niveaux else None


def annee_complete(annee: str) -> int:
    n = int(annee)
    if len(annee) == 2:
        return 2000 + n if n < 70 else 1900 + n
    return n


def construire_date(annee: int, mois: int, jour: int) -> str | None:
    try:
        return date(annee, mois, jour).isoformat()
    except ValueError:
        return None


def numero_mois(mot: str) -> int | None:
    mot = mot.rstrip(".")
    if mot in JOURS:
        return None
    for prefixe, numero in MOIS:
        if mot.startswith(prefixe):
            return numero
    return None


def date_excel(texte: str) -> str | None:
    m = re.fullmatch(r"(\d{5})(?:[.,]0+)?", texte)
    if m and 20000 <= int(m.group(1)) <= 80000:
        return (ORIGINE_EXCEL + timedelta(days=int(m.group(1)))).isoformat()
    return None


def normaliser_date(valeur: str | None) -> str | None:
    s = sans_accents(valeur or "").strip()
    if not s:
        return None
    m = re.search(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", s)
    if m:
        return construire_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"\b(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{4}|\d{2})\b", s)
    if not m:
        m = re.search(r"\b(\d{1,2})\s+(\d{1,2})\s+(\d{4})\b", s)
    if m:
        jour, mois, annee = int(m.group(1)), int(m.group(2)), annee_complete(m.group(3))
        return construire_date(annee, mois, jour) or construire_date(annee, jour, mois)
    m = re.search(r"\b(\d{1,2})\s*(?:er)?[\s\-/.]+([a-z]+)\.?,?[\s\-/.]+(\d{4}|\d{2})\b", s)
    if m:
        mois = numero_mois(m.group(2))
        if mois:
            return construire_date(annee_complete(m.group(3)), mois, int(m.group(1)))
    m = re.search(r"\b([a-z]+)\.?\s+(\d{1,2})(?:er|st|nd|rd|th)?,?\s+(\d{4})\b", s)
    if m:
        mois = numero_mois(m.group(1))
        if mois:
            return construire_date(int(m.group(3)), mois, int(m.group(2)))
    m = re.search(r"\b((?:19|20)\d{2})(\d{2})(\d{2})\b", s)
    if m:
        return construire_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"\b(\d{2})(\d{2})((?:19|20)\d{2})\b", s)
    if m:
        return construire_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return date_excel(s)
