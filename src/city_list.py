"""Whitelist der Zielstädte für die EV-Clustering-Analyse.

Untersuchungsmenge (N = 77):
    Gruppe A — alle deutschen Großstädte mit >= 100.000 Einwohnern (76 Städte)
    Gruppe B — alle 16 Landeshauptstädte; einzige reine Ergänzung unter der
               100k-Schwelle ist Schwerin.

Die Schlüssel sind der 8-stellige Amtliche Gemeindeschlüssel (AGS) als String.
Die AGS-Codes wurden gegen das Gemeindeverzeichnis des Statistischen
Bundesamtes bzw. statistikportal.de verifiziert (Stand 2024/2025).

WICHTIG: AGS immer als String mit führenden Nullen behandeln, niemals als int.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Zielstädte: AGS (8-stellig) -> Stadtname
# ---------------------------------------------------------------------------
TARGET_CITIES: dict[str, str] = {
    # --- Stadtstaaten / Landeshauptstädte (kreisfrei) ---
    "11000000": "Berlin",
    "02000000": "Hamburg",
    "04011000": "Bremen",
    "04012000": "Bremerhaven",
    # --- Schleswig-Holstein (01) ---
    "01002000": "Kiel",
    "01003000": "Lübeck",
    # --- Niedersachsen (03) ---
    "03101000": "Braunschweig",
    "03102000": "Salzgitter",
    "03103000": "Wolfsburg",
    "03159016": "Göttingen",
    "03241001": "Hannover",
    "03403000": "Oldenburg",
    "03404000": "Osnabrück",
    # --- Nordrhein-Westfalen (05) ---
    "05111000": "Düsseldorf",
    "05112000": "Duisburg",
    "05113000": "Essen",
    "05114000": "Krefeld",
    "05116000": "Mönchengladbach",
    "05117000": "Mülheim an der Ruhr",
    "05119000": "Oberhausen",
    "05120000": "Remscheid",
    "05122000": "Solingen",
    "05124000": "Wuppertal",
    "05162024": "Neuss",
    "05170024": "Moers",
    "05314000": "Bonn",
    "05315000": "Köln",
    "05316000": "Leverkusen",
    "05334002": "Aachen",
    "05378004": "Bergisch Gladbach",
    "05512000": "Bottrop",
    "05513000": "Gelsenkirchen",
    "05515000": "Münster",
    "05711000": "Bielefeld",
    "05774032": "Paderborn",
    "05911000": "Bochum",
    "05913000": "Dortmund",
    "05914000": "Hagen",
    "05915000": "Hamm",
    "05916000": "Herne",
    # --- Hessen (06) ---
    "06411000": "Darmstadt",
    "06412000": "Frankfurt am Main",
    "06413000": "Offenbach am Main",
    "06414000": "Wiesbaden",
    "06611000": "Kassel",
    # --- Rheinland-Pfalz (07) ---
    "07111000": "Koblenz",
    "07211000": "Trier",
    "07314000": "Ludwigshafen am Rhein",
    "07315000": "Mainz",
    # --- Baden-Württemberg (08) ---
    "08111000": "Stuttgart",
    "08121000": "Heilbronn",
    "08212000": "Karlsruhe",
    "08221000": "Heidelberg",
    "08222000": "Mannheim",
    "08231000": "Pforzheim",
    "08311000": "Freiburg im Breisgau",
    "08415061": "Reutlingen",
    "08421000": "Ulm",
    # --- Bayern (09) ---
    "09161000": "Ingolstadt",
    "09162000": "München",
    "09362000": "Regensburg",
    "09562000": "Erlangen",
    "09563000": "Fürth",
    "09564000": "Nürnberg",
    "09663000": "Würzburg",
    "09761000": "Augsburg",
    # --- Saarland (10) ---
    "10041100": "Saarbrücken",
    # --- Brandenburg (12) ---
    "12054000": "Potsdam",
    # --- Mecklenburg-Vorpommern (13) ---
    "13003000": "Rostock",
    "13004000": "Schwerin",
    # --- Sachsen (14) ---
    "14511000": "Chemnitz",
    "14612000": "Dresden",
    "14713000": "Leipzig",
    # --- Sachsen-Anhalt (15) ---
    "15002000": "Halle (Saale)",
    "15003000": "Magdeburg",
    # --- Thüringen (16) ---
    "16051000": "Erfurt",
    "16053000": "Jena",
}


def normalize_ags(value: object) -> str:
    """Standardisiere einen AGS-Wert auf 8-stelligen String mit führenden Nullen.

    Args:
        value: Roher AGS-Wert (int, float, str). Floats wie ``11000000.0`` und
            bereits getrimmte Strings werden korrekt behandelt.

    Returns:
        8-stelliger AGS als String, z.B. ``"02000000"``.

    Raises:
        ValueError: Wenn ``value`` keine extrahierbaren Ziffern enthält.
    """
    if value is None:
        raise ValueError("AGS darf nicht None sein")
    text = str(value).strip()
    if text.endswith(".0"):  # häufiges Artefakt aus float-Spalten
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        raise ValueError(f"Kein gültiger AGS in {value!r}")
    return digits.zfill(8)


if __name__ == "__main__":
    assert len(TARGET_CITIES) == 77, f"Erwartet 77 Städte, gefunden {len(TARGET_CITIES)}"
    print(f"{len(TARGET_CITIES)} Zielstädte - OK")
